from flask.views import MethodView
from flask import request, current_app

from server.api.globals import db, exceptions
from server.api.utils import is_authorized
from server.api.v1.tosurnament.tournaments.brackets import get_bracket_data, delete_bracket_and_associated_spreadsheets
from common.databases.tosurnament.tournament import Tournament
from common.databases.tosurnament.bracket import Bracket
from common.databases.tosurnament.allowed_reschedule import AllowedReschedule


def get_brackets_data_of_tournament(tournament, include_spreadsheets=False):
    brackets_data = []
    brackets = db.query(Bracket).where(Bracket.tournament_id == tournament.id).all()
    for bracket in brackets:
        brackets_data.append(get_bracket_data(bracket, include_spreadsheets))
    return brackets_data


def get_tournament_data(tournament, include_brackets=False, include_spreadsheets=False):
    tournament_data = tournament.get_api_dict()
    if include_brackets:
        tournament_data["brackets"] = get_brackets_data_of_tournament(tournament, include_spreadsheets)
    return tournament_data


class TournamentsResource(MethodView):
    def _get_object(self, tournament_id):
        tournament = db.query(Tournament).where(Tournament.id == tournament_id).first()
        if not tournament:
            raise exceptions.NotFound()
        return tournament

    @is_authorized(user=True)
    def get(self, tournament_id):
        request_args = request.args.to_dict()
        include_brackets = request_args.pop("include_brackets", "false").casefold() == "true"
        include_spreadsheets = request_args.pop("include_spreadsheets", "false").casefold() == "true"
        if tournament_id is None:
            return self.get_all(include_brackets, include_spreadsheets, request_args)
        tournament = self._get_object(tournament_id)
        return get_tournament_data(tournament, include_brackets, include_spreadsheets)

    def get_all(self, include_brackets, include_spreadsheets, request_args):
        guild_id = request_args.pop("guild_id", None)
        if guild_id:
            try:
                request_args["guild_id"] = int(guild_id)
            except ValueError:
                raise exceptions.BadRequest()
        tournaments = db.query(Tournament).where(**request_args).all()
        tournaments_data = []
        for tournament in tournaments:
            tournaments_data.append(get_tournament_data(tournament, include_brackets, include_spreadsheets))
        return {"tournaments": tournaments_data}

    @is_authorized(user=True)
    def put(self, tournament_id):
        tournament = self._get_object(tournament_id)
        tournament.update(**request.json)
        db.update(tournament)
        current_app.logger.debug("The tournament {0} has been updated successfully.".format(tournament_id))
        return {}, 204

    @is_authorized(user=True)
    def post(self):
        body = request.json
        if (
            not body
            or not body["guild_id"]
            or not body["guild_id_snowflake"]
            or not body["name"]
            or not body["acronym"]
        ):
            raise exceptions.MissingRequiredInformation()
        try:
            body["guild_id"] = int(body["guild_id"])
        except ValueError:
            raise exceptions.BadRequest()
        tournament = Tournament(**body)
        db.add(tournament)
        bracket = Bracket(tournament_id=tournament.id, name=tournament.name)
        db.add(bracket)
        tournament.current_bracket_id = bracket.id
        db.update(tournament)
        current_app.logger.debug("The tournament {0} has been created successfully.".format(tournament.id))
        return get_tournament_data(tournament, True), 201

    @is_authorized(user=True)
    def delete(self, tournament_id):
        tournament = self._get_object(tournament_id)
        brackets = db.query(Bracket).where(Bracket.tournament_id == tournament_id).all()
        for bracket in brackets:
            delete_bracket_and_associated_spreadsheets(bracket)
        allowed_reschedules = db.query(AllowedReschedule).where(AllowedReschedule.tournament_id == tournament_id).all()
        for allowed_reschedule in allowed_reschedules:
            current_app.logger.debug(
                "The allowed reschedule {0} for the match id {1} has been deleted successfully.".format(
                    allowed_reschedule.id, allowed_reschedule.match_id
                )
            )
            db.delete(allowed_reschedule)
        db.delete(tournament)
        current_app.logger.debug("The tournament {0} has been deleted successfully.".format(tournament_id))
        return {}, 204
