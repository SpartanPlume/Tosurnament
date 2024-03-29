import sys
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import inspect
import requests_cache
from flask import Flask, g
from flask_cors import CORS
from api.v1.tosurnament.token import TokenResource
from api.v1.tosurnament.token.revoke import RevokeTokenResource
from api.v1.tosurnament.users import UsersResource
from api.v1.tosurnament.guilds import GuildsResource
from api.v1.tosurnament.tournaments import TournamentsResource
from api.v1.tosurnament.tournaments.allowed_reschedules import AllowedReschedulesResource
from api.v1.tosurnament.tournaments.brackets import BracketsResource
from api.v1.tosurnament.tournaments.brackets.schedules_spreadsheet import SchedulesSpreadsheetResource
from api.v1.tosurnament.tournaments.brackets.players_spreadsheet import PlayersSpreadsheetResource
from api.v1.tosurnament.tournaments.brackets.qualifiers_spreadsheet import QualifiersSpreadsheetResource
from api.v1.tosurnament.tournaments.brackets.qualifiers_results_spreadsheet import (
    QualifiersResultsSpreadsheetResource,
)
from api.v1.discord.guilds.roles import DiscordRolesResource
from api.v1.discord.guilds.channels import DiscordChannelsResource
from api.v1.discord.guilds.common import DiscordCommonGuildsResource
from api.v1.discord.users.me import DiscordUsersMeResource
from api.v1.tosurnament.auth import AuthResource
from api.globals import db, exceptions
from api import logger

app = Flask("tosurnament-api")
app.config["BUNDLE_ERRORS"] = True
CORS(app, max_age=7200)

requests_cache.install_cache(expire_after=300, allowable_methods=("GET"))

logging_handler = TimedRotatingFileHandler(
    filename="logs/api.log",
    when="W1",
    utc=True,
    backupCount=4,
    atTime=datetime.time(hour=12),
)
logging_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(name)s <%(filename)s:%(lineno)d>: %(message)s")
)
app.logger.addHandler(logging_handler)
app.logger.setLevel(logging.DEBUG)

gunicorn_logger = logging.getLogger("gunicorn.access")
for handler in gunicorn_logger.handlers:
    gunicorn_logger.removeHandler(handler)
gunicorn_logger.addHandler(logging_handler)
gunicorn_logger.setLevel(logging.DEBUG)

db_logger = logging.getLogger("encrypted_mysqldb")
for handler in db_logger.handlers:
    db_logger.removeHandler(handler)
db_logger.addHandler(logging_handler)
db_logger.setLevel(logging.DEBUG)


@app.before_request
def clear_g():
    g.token = None


# @app.after_request
# def apply_caching(response):
#    if "Cache-Control" not in response.headers:
#        response.headers["Cache-Control"] = "max-age=60"
#    return response


if not db:
    app.logger.error("ERROR: Couldn't initialize the db session. Is the mysql service started ?")
    sys.exit(4)


def register_api_v1_tosurnament(resource, endpoint, url, id_parameter_name, with_delete_all=False):
    resource_view = resource.as_view(endpoint)
    methods_with_default = ["GET"]
    if with_delete_all:
        methods_with_default.append("DELETE")
    url = "/api/v1/tosurnament" + url
    app.add_url_rule(url, defaults={id_parameter_name: None}, view_func=resource_view, methods=methods_with_default)
    app.add_url_rule(url, view_func=resource_view, methods=["POST"])
    app.add_url_rule(f"{url}/<int:{id_parameter_name}>", view_func=resource_view, methods=["GET", "PUT", "DELETE"])


register_api_v1_tosurnament(UsersResource, "users_api", "/users", "user_id")
register_api_v1_tosurnament(GuildsResource, "guilds_api", "/guilds", "guild_id")
register_api_v1_tosurnament(TournamentsResource, "tournaments_api", "/tournaments", "tournament_id")
register_api_v1_tosurnament(
    AllowedReschedulesResource,
    "allowed_reschedules_api",
    "/tournaments/<int:tournament_id>/allowed_reschedules",
    "allowed_reschedule_id",
    with_delete_all=True,
)
register_api_v1_tosurnament(BracketsResource, "brackets_api", "/tournaments/<int:tournament_id>/brackets", "bracket_id")


def register_api_v1_for_spreadsheet(resource, endpoint, url):
    resource_view = resource.as_view(endpoint)
    url = "/api/v1/tosurnament/tournaments/<int:tournament_id>/brackets/<int:bracket_id>" + url
    app.add_url_rule(url, view_func=resource_view, methods=["POST"])
    app.add_url_rule(f"{url}/<int:spreadsheet_id>", view_func=resource_view, methods=["GET", "PUT", "DELETE"])


register_api_v1_for_spreadsheet(SchedulesSpreadsheetResource, "schedules_spreadsheet_api", "/schedules_spreadsheet")
register_api_v1_for_spreadsheet(PlayersSpreadsheetResource, "players_spreadsheet_api", "/players_spreadsheet")
register_api_v1_for_spreadsheet(QualifiersSpreadsheetResource, "qualifiers_spreadsheet_api", "/qualifiers_spreadsheet")
register_api_v1_for_spreadsheet(
    QualifiersResultsSpreadsheetResource, "qualifiers_results_spreadsheet_api", "/qualifiers_results_spreadsheet"
)

resource_view = TokenResource.as_view("token_api")
app.add_url_rule("/api/v1/tosurnament/token", view_func=resource_view, methods=["POST"])
resource_view = RevokeTokenResource.as_view("revoke_token_api")
app.add_url_rule("/api/v1/tosurnament/token/revoke", view_func=resource_view, methods=["POST"])

resource_view = DiscordRolesResource.as_view("discord_roles_api")
app.add_url_rule(
    "/api/v1/discord/guilds/<guild_id>/roles", defaults={"role_id": None}, view_func=resource_view, methods=["GET"]
)
resource_view = DiscordChannelsResource.as_view("discord_channels_api")
app.add_url_rule(
    "/api/v1/discord/guilds/<guild_id>/channels",
    defaults={"channel_id": None},
    view_func=resource_view,
    methods=["GET"],
)
resource_view = DiscordCommonGuildsResource.as_view("discord_common_guilds_api")
app.add_url_rule("/api/v1/discord/guilds/common", view_func=resource_view, methods=["GET"])
resource_view = DiscordUsersMeResource.as_view("discord_users_me_api")
app.add_url_rule("/api/v1/discord/users/me", view_func=resource_view, methods=["GET"])


def log_and_update_exception(e):
    object_to_return = {"status": e.code, "title": e.title, "detail": e.description}
    logger.info("{0} {1}: {2}".format("Error", e.code, e.description))
    return object_to_return, e.code


exception_classes = inspect.getmembers(sys.modules[exceptions.__name__], inspect.isclass)
for exception_class in exception_classes:
    if exception_class[0] != "HTTPException":
        app.register_error_handler(exception_class[1], log_and_update_exception)


app.add_url_rule("/api/v1/tosurnament/auth", view_func=AuthResource.as_view("auth_api"), methods=["POST"])


if __name__ == "__main__":
    app.run(debug=True, port=5001)
