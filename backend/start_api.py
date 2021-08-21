import sys
import logging
from flask import Flask
from server.api.v1.tosurnament.users import UsersResource
from server.api.v1.tosurnament.guilds import GuildsResource
from server.api.v1.tosurnament.tournaments import TournamentsResource
from server.api.v1.tosurnament.tournaments.allowed_reschedules import AllowedReschedulesResource
from server.api.v1.tosurnament.tournaments.brackets import BracketsResource
from server.api.v1.tosurnament.tournaments.brackets.schedules_spreadsheet import SchedulesSpreadsheetResource
from server.api.v1.tosurnament.tournaments.brackets.players_spreadsheet import PlayersSpreadsheetResource
from server.api.v1.tosurnament.tournaments.brackets.qualifiers_spreadsheet import QualifiersSpreadsheetResource
from server.api.v1.tosurnament.tournaments.brackets.qualifiers_results_spreadsheet import (
    QualifiersResultsSpreadsheetResource,
)
from server.api.v1.tosurnament.auth import AuthResource
from server.api.globals import db, logging_handler, exceptions

app = Flask("tosurnament-api")
app.config["BUNDLE_ERRORS"] = True


@app.before_first_request
def init_logger():
    app.logger.addHandler(logging_handler)
    app.logger.setLevel(logging.DEBUG)

    logger = logging.getLogger("gunicorn.access")
    for handler in logger.handlers:
        logger.removeHandler(handler)
    logger.addHandler(logging_handler)
    logger.setLevel(logging.DEBUG)


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
    app.add_url_rule(f"{url}/<int:spreadsheet_id>", view_func=resource_view, methods=["GET", "PUT"])


register_api_v1_for_spreadsheet(SchedulesSpreadsheetResource, "schedules_spreadsheet_api", "/schedules_spreadsheet")
register_api_v1_for_spreadsheet(PlayersSpreadsheetResource, "players_spreadsheet_api", "/players_spreadsheet")
register_api_v1_for_spreadsheet(QualifiersSpreadsheetResource, "qualifiers_spreadsheet_api", "/qualifiers_spreadsheet")
register_api_v1_for_spreadsheet(
    QualifiersResultsSpreadsheetResource, "qualifiers_results_spreadsheet_api", "/qualifiers_results_spreadsheet"
)


def register_exception(exception):
    app.register_error_handler(
        exception, lambda e: ({"status": e.code, "title": e.title, "detail": e.description}, e.code)
    )


register_exception(exceptions.NotFound)

app.add_url_rule("/api/v1/tosurnament/auth", view_func=AuthResource.as_view("auth_api"), methods=["POST"])

if __name__ == "__main__":
    app.run(debug=True, port=5001)
