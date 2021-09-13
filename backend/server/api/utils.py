import time
import requests
import functools

from flask import request, current_app, g
from common.databases.tosurnament.tournament import Tournament
from common.databases.tosurnament.guild import Guild

from server.api.globals import db, endpoints, exceptions
from common.config import constants
from common.databases.tosurnament.token import Token


def refresh_token_if_needed(token):
    if int(token.access_token_expiry_date) >= int(time.time()):
        return
    if token.token_type == "user":
        data = {
            "client_id": constants.CLIENT_ID,
            "client_secret": constants.CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
            "redirect_uri": constants.DISCORD_REDIRECT_URI,
            "scope": token.scope,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            r = requests.post(endpoints.DISCORD_TOKEN + "/token", data=data, headers=headers)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise exceptions.DiscordTokenError()
        token.access_token = data["access_token"]
        token.access_token_expiry_date = str(int(time.time()) + data["expires_in"])
        token.refresh_token = data["refresh_token"]
        token.scope = data["scope"]
        db.update(token)


def is_authorized(local=True, client=False, user=False):
    def decorator_is_authorized(func):
        def exec_func_if_user_can_access_resource(func, *args, **kwargs):
            if "guild_id" in kwargs and kwargs["guild_id"]:
                guild = db.query(Guild).where(Guild.id == kwargs["guild_id"]).first()
                if not guild:
                    raise exceptions.NotFound()
                assert_user_can_access_resource(guild.guild_id_snowflake, guild.admin_role_id)
            elif "tournament_id" in kwargs and kwargs["tournament_id"]:
                tournament = db.query(Tournament).where(Tournament.id == kwargs["tournament_id"]).first()
                if not tournament:
                    raise exceptions.NotFound()
                admin_role_id = None
                guild = db.query(Guild).where(Guild.id == tournament.guild_id_snowflake).first()
                if guild:
                    admin_role_id = guild.admin_role_id
                assert_user_can_access_resource(tournament.guild_id_snowflake, admin_role_id)
            else:
                request_args = request.args.to_dict()
                if "guild_id" not in request_args or not request_args["guild_id"]:
                    body = request.json
                    if func.__name__ == "post" and body and "guild_id" in body and body["guild_id"]:
                        assert_user_can_access_resource(body["guild_id"])
                        return func(*args, **kwargs)
                    raise exceptions.Forbidden()
                guild = db.query(Guild).where(Guild.guild_id == request_args["guild_id"]).first()
                if not guild:
                    tournament = db.query(Tournament).where(Tournament.guild_id == request_args["guild_id"]).first()
                    if not tournament:
                        raise exceptions.NotFound()
                    assert_user_can_access_resource(tournament.guild_id_snowflake)
                    return func(*args, **kwargs)
                assert_user_can_access_resource(guild.guild_id_snowflake, guild.admin_role_id)
            return func(*args, **kwargs)

        @functools.wraps(func)
        def wrapper_is_authorized(*args, **kwargs):
            if request.remote_addr == "127.0.0.1":
                if local:
                    return func(*args, **kwargs)
                else:
                    raise exceptions.Forbidden()
            session_token = request.headers.get("Authorization")
            if not session_token:
                raise exceptions.Unauthorized()
            token = db.query(Token).where(Token.session_token == session_token).first()
            if not token:
                raise exceptions.Unauthorized()
            if int(token.expiry_date) < int(time.time()):
                db.delete(token)
                current_app.logger.debug("Token of the user {0} has expired".format(token.discord_user_id))
                raise exceptions.Unauthorized()
            refresh_token_if_needed(token)
            g.token = token
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
    headers = {"Authorization": "Bot " + constants.BOT_TOKEN, "Content-type": "application/json"}
    if admin_role_id:
        try:
            r = requests.get(
                endpoints.DISCORD_GUILD_MEMBER.format(
                    discord_guild_id,
                ),
                headers=headers,
            )
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise exceptions.DiscordGetError()
        member = r.json()
        if str(admin_role_id) in member["roles"]:
            return
    try:
        r = requests.get(endpoints.DISCORD_GUILD.format(discord_guild_id), headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        raise exceptions.DiscordGetError()
    guild = r.json()
    if str(discord_user_id) == guild["owner_id"]:
        return
    raise exceptions.Forbidden()
