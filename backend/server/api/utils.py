import datetime
import requests
import functools

from flask import request, g
from common.databases.tosurnament.tournament import Tournament
from common.databases.tosurnament.guild import Guild

from server.api.globals import db, endpoints, exceptions
from server.api import logger
from common.config import constants
from common.databases.tosurnament.token import Token

from common.api import spreadsheet as spreadsheet_api

DATABASE_DATE_REGEX = r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$"
DAY_REGEX = r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
TIME_REGEX = r"([0-2][0-3]|[0-1][0-9]):[0-5][0-9]"


def assert_int_field(body, field, min, max):
    if field in body:
        try:
            field_as_int = int(body[field])
        except Exception:
            raise exceptions.InvalidFieldValue(field)
        if field_as_int < min or field_as_int > max:
            raise exceptions.InvalidFieldValue(field)


def assert_range_field(body, field):
    if field in body:
        if body[field] and not spreadsheet_api.check_range(body[field]):
            raise exceptions.InvalidFieldValue(field)


def assert_str_field_length(body, field, max_length, min_length=0):
    if field in body:
        field_length = len(body[field])
        if field_length < min_length or field_length > max_length:
            raise exceptions.InvalidFieldValue(field)


def check_body_fields(db_class, mandatory_fields=[]):
    def decorator_check_body_fields(func):
        @functools.wraps(func)
        def wrapper_check_body_fields(*args, **kwargs):
            body = request.json
            if not body:
                raise exceptions.BadRequest("Missing body")
            if "created_at" in body:
                del body["created_at"]
            if "updated_at" in body:
                del body["updated_at"]
            db_class_vars = vars(db_class())
            for field_key, field_value in body.items():
                if field_key not in db_class_vars:
                    raise exceptions.UnknownField(field_key)
                try:
                    db_class_field_type = type(db_class_vars[field_key])
                    db_class_field_type(field_value)
                except Exception:
                    raise exceptions.IncorrectFieldType(field_key)
                if field_key in mandatory_fields:
                    mandatory_fields.remove(field_key)
            if mandatory_fields:
                raise exceptions.MissingRequiredInformation(mandatory_fields)
            return func(*args, **kwargs)

        return wrapper_check_body_fields

    return decorator_check_body_fields


def refresh_token_if_needed(token):
    if token.access_token_expiry_date >= datetime.datetime.utcnow():
        return
    if token.token_type == "user":
        data = {
            "client_id": constants.DISCORD_CLIENT_ID,
            "client_secret": constants.DISCORD_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
            "redirect_uri": constants.DISCORD_REDIRECT_URI,
            "scope": token.scope,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            r = requests.post(endpoints.DISCORD_TOKEN, data=data, headers=headers)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error = r.json()
            if r.status_code == 400:
                db.delete(token)
            raise exceptions.DiscordException(r.status_code, e.response.reason, error)
        except requests.exceptions.ConnectionError:
            raise exceptions.DiscordError()
        token.access_token = data["access_token"]
        token.access_token_expiry_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=data["expires_in"])
        token.refresh_token = data["refresh_token"]
        token.scope = data["scope"]
        db.update(token)
        g.token = token
        logger.debug("Token has been updated")


def is_authorized(local=True, client=False, user=False):
    def decorator_is_authorized(func):
        def exec_func_if_user_can_access_resource(func, *args, **kwargs):
            request_args = request.args.to_dict()
            url_rules_to_ignore = ["/api/v1/tosurnament/token", "/api/v1/tosurnament/token/revoke"]
            if (
                request.url_rule.rule in url_rules_to_ignore or "discord" in request.url_rule.rule
            ) and not request_args:
                return func(*args, **kwargs)
            if "guild_id" in kwargs and kwargs["guild_id"]:
                if "tosurnament" in request.url_rule.rule:
                    guild = db.query(Guild).where(Guild.id == kwargs["guild_id"]).first()
                    if not guild:
                        raise exceptions.NotFound()
                else:
                    guild = db.query(Guild).where(Guild.guild_id == kwargs["guild_id"]).first()
                    if not guild:
                        guild = db.add(Guild(guild_id=kwargs["guild_id"], guild_id_snowflake=kwargs["guild_id"]))
                assert_user_can_access_resource(guild.guild_id_snowflake, guild.admin_role_id)
            elif "tournament_id" in kwargs and kwargs["tournament_id"]:
                tournament = db.query(Tournament).where(Tournament.id == kwargs["tournament_id"]).first()
                if not tournament:
                    raise exceptions.NotFound()
                admin_role_id = None
                guild = db.query(Guild).where(Guild.guild_id == tournament.guild_id_snowflake).first()
                if guild:
                    admin_role_id = guild.admin_role_id
                assert_user_can_access_resource(tournament.guild_id_snowflake, admin_role_id)
            else:
                if "guild_id" not in request_args or not request_args["guild_id"]:
                    body = request.json
                    if func.__name__ == "post" and body and "guild_id" in body and body["guild_id"]:
                        assert_user_can_access_resource(str(body["guild_id"]))
                        return func(*args, **kwargs)
                    raise exceptions.Forbidden()
                guild = db.query(Guild).where(Guild.guild_id == request_args["guild_id"]).first()
                if not guild:
                    guild = db.add(
                        Guild(guild_id=request_args["guild_id"], guild_id_snowflake=request_args["guild_id"])
                    )
                assert_user_can_access_resource(guild.guild_id_snowflake, guild.admin_role_id)
            return func(*args, **kwargs)

        @functools.wraps(func)
        def wrapper_is_authorized(*args, **kwargs):
            session_token = request.headers.get("Authorization")
            if request.remote_addr == "127.0.0.1" and session_token == "Bot":
                if local:
                    return func(*args, **kwargs)
                else:
                    raise exceptions.Forbidden()
            if not session_token:
                raise exceptions.Unauthorized()
            token = db.query(Token).where(Token.session_token == session_token).first()
            if not token:
                raise exceptions.Unauthorized()
            g.token = token
            if token.expiry_date < datetime.datetime.utcnow():
                db.delete(token)
                logger.debug("Token has expired")
                raise exceptions.Unauthorized()
            refresh_token_if_needed(token)
            if user and token.token_type == "user":
                return exec_func_if_user_can_access_resource(func, *args, **kwargs)
            if client and token.token_type == "client":
                return func(*args, **kwargs)
            raise exceptions.Forbidden()

        return wrapper_is_authorized

    return decorator_is_authorized


def assert_user_can_access_resource(discord_guild_id, admin_role_id=None):
    token = g.token
    discord_user_id = token.discord_user_id
    headers = {"Authorization": "Bot " + constants.BOT_TOKEN}
    if admin_role_id:
        try:
            r = requests.get(
                endpoints.DISCORD_GUILD_MEMBER.format(discord_guild_id, discord_user_id),
                headers=headers,
            )
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error = r.json()
            raise exceptions.DiscordException(r.status_code, e.response.reason, error)
        except requests.exceptions.ConnectionError:
            raise exceptions.DiscordError()
        member = r.json()
        if str(admin_role_id) in member["roles"]:
            return
    try:
        r = requests.get(endpoints.DISCORD_GUILD.format(discord_guild_id), headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        error = r.json()
        raise exceptions.DiscordException(r.status_code, e.response.reason, error)
    except requests.exceptions.ConnectionError:
        raise exceptions.DiscordError()
    guild = r.json()
    if str(discord_user_id) == guild["owner_id"]:
        return
    raise exceptions.Forbidden()
