import re

import dateparser
from flask.views import MethodView
from flask import request

from api.globals import db, exceptions
from api.utils import (
    assert_int_field,
    is_authorized,
    check_body_fields,
    assert_str_field_length,
    DAY_REGEX,
    TIME_REGEX,
)
from api import logger
from api.v1.tosurnament.tournaments.brackets import get_bracket_data, delete_bracket_and_associated_spreadsheets
from common.databases.tosurnament.team import Team
from common.databases.tosurnament.bracket import Bracket
from common.databases.tosurnament.allowed_reschedule import AllowedReschedule
from common.api import challonge as challonge_api


def get_players_data_of_team(team, include_spreadsheets=False):
    players_data = []
    players = db.query(Bracket).where(Bracket.team_id == team.id).all()
    for bracket in players:
        players_data.append(get_bracket_data(bracket, include_spreadsheets))
    return players_data


class TeamsResource(MethodView):
    def _get_object(self, team_id):
        team = db.query(Team).where(Team.id == team_id).first()
        if not team:
            raise exceptions.NotFound()
        return team

    @is_authorized(user=True)
    def get(self, team_id):
        return None
        # request_args = request.args.to_dict()
        # include_players = request_args.pop("include_players", "false").casefold() == "true"
        # if team_id is None:
        #    return self.get_all(include_players, include_spreadsheets, request_args)
        # team = self._get_object(team_id)
        # return get_team_data(team, include_players, include_spreadsheets)

    def get_all(self, include_brackets, include_spreadsheets, request_args):
        return None
        # tournaments = db.query(Team).where(**request_args).all()
        # tournaments_data = []
        # for tournament in tournaments:
        #    tournaments_data.append(get_tournament_data(tournament, include_brackets, include_spreadsheets))
        # return {"tournaments": tournaments_data}

    def assert_validate_body(self, body, tournament_id):
        assert_str_field_length(body, "name", 32, min_length=1)
        if "utc" in body and body["utc"]:
            if not re.match(r"^[-\+]" + TIME_REGEX + r"$", body["utc"]):
                raise exceptions.InvalidFieldValue("utc")
            try:
                dateparser.parse("now", settings={"TIMEZONE": body["utc"]})
            except Exception:
                raise exceptions.InvalidFieldValue("utc")
        if "bracket_id" in body and tournament_id:
            bracket = db.query(Bracket).where(Bracket.id == body["bracket_id"]).first()
            if not bracket:
                raise exceptions.InvalidFieldValue("bracket_id")

    @check_body_fields(Team)
    @is_authorized(user=True)
    def put(self, tournament_id):
        tournament = self._get_object(tournament_id)
        body = request.json
        if "guild_id" in body:
            del body["guild_id"]
        if "guild_id_snowflake" in body:
            if tournament.guild_id_snowflake != str(body["guild_id_snowflake"]):
                raise exceptions.BadRequest("guild_id_snowflake cannot be updated")
            del body["guild_id_snowflake"]
        if "challonge" in body:
            body["challonge"] = challonge_api.extract_tournament_id(body["challonge"])
        self.assert_validate_body(body, tournament_id)
        tournament.update(**body)
        db.update(tournament)
        logger.debug("Team {0} has been updated".format(tournament_id))
        return {}, 204

    @check_body_fields(Team, mandatory_fields=["guild_id", "name", "acronym"])
    @is_authorized(user=True)
    def post(self):
        body = request.json
        body["guild_id"] = str(body["guild_id"])
        body["guild_id_snowflake"] = str(body["guild_id"])
        self.assert_validate_body(body, None)
        tournament = Team(**body)
        db.add(tournament)
        bracket = Bracket(tournament_id=tournament.id, name=tournament.name)
        db.add(bracket)
        tournament.current_bracket_id = bracket.id
        db.update(tournament)
        logger.debug("Team {0} has been created".format(tournament.id))
        return None
        # return get_tournament_data(tournament, True), 201

    @is_authorized(user=True)
    def delete(self, tournament_id):
        tournament = self._get_object(tournament_id)
        brackets = db.query(Bracket).where(Bracket.tournament_id == tournament_id).all()
        for bracket in brackets:
            delete_bracket_and_associated_spreadsheets(bracket)
        allowed_reschedules = db.query(AllowedReschedule).where(AllowedReschedule.tournament_id == tournament_id).all()
        for allowed_reschedule in allowed_reschedules:
            logger.debug(
                "Allowed reschedule {0} for the match id {1} has been deleted".format(
                    allowed_reschedule.id, allowed_reschedule.match_id
                )
            )
            db.delete(allowed_reschedule)
        db.delete(tournament)
        logger.debug("Team {0} has been deleted".format(tournament_id))
        return {}, 204
