import re

import dateparser
from flask.views import MethodView
from flask import request

from server.api.globals import db, exceptions
from server.api.utils import (
    assert_int_field,
    is_authorized,
    check_body_fields,
    assert_str_field_length,
    DAY_REGEX,
    TIME_REGEX,
)
from server.api import logger
from server.api.v1.tosurnament.tournaments.brackets import get_bracket_data, delete_bracket_and_associated_spreadsheets
from common.databases.tosurnament.tournament import Tournament
from common.databases.tosurnament.bracket import Bracket
from common.databases.tosurnament.allowed_reschedule import AllowedReschedule
from common.api import challonge as challonge_api


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
        tournaments = db.query(Tournament).where(**request_args).all()
        tournaments_data = []
        for tournament in tournaments:
            tournaments_data.append(get_tournament_data(tournament, include_brackets, include_spreadsheets))
        return {"tournaments": tournaments_data}

    def assert_validate_body(self, body, tournament_id):
        assert_str_field_length(body, "acronym", 16, min_length=1)
        assert_str_field_length(body, "name", 128, min_length=1)
        assert_str_field_length(body, "staff_channel_id", 32)
        assert_str_field_length(body, "match_notification_channel_id", 32)
        assert_str_field_length(body, "referee_role_id", 32)
        assert_str_field_length(body, "streamer_role_id", 32)
        assert_str_field_length(body, "commentator_role_id", 32)
        assert_str_field_length(body, "player_role_id", 32)
        assert_str_field_length(body, "team_captain_role_id", 32)
        assert_str_field_length(body, "post_result_message", 1024)
        assert_str_field_length(body, "post_result_message_team1_with_score", 128)
        assert_str_field_length(body, "post_result_message_team2_with_score", 128)
        assert_str_field_length(body, "post_result_message_mp_link", 128)
        assert_str_field_length(body, "post_result_message_rolls", 128)
        assert_str_field_length(body, "post_result_message_bans", 128)
        assert_str_field_length(body, "post_result_message_tb_bans", 128)
        assert_int_field(body, "reschedule_deadline_hours_before_current_time", 0, 72)
        assert_int_field(body, "reschedule_deadline_hours_before_new_time", 0, 72)
        assert_str_field_length(body, "matches_to_ignore", 2048)
        assert_str_field_length(body, "template_code", 16)
        assert_int_field(body, "game_mode", 0, 3)
        assert_str_field_length(body, "date_format", 32)
        if "reschedule_deadline_end" in body and body["reschedule_deadline_end"]:
            if not re.match(
                r"^" + DAY_REGEX + r" " + TIME_REGEX + r"$",
                body["reschedule_deadline_end"],
            ):
                raise exceptions.InvalidFieldValue("reschedule_deadline_end")
        if "reschedule_before_date" in body and body["reschedule_before_date"]:
            if not re.match(
                r"^" + DAY_REGEX + r" " + TIME_REGEX + r"$",
                body["reschedule_before_date"],
            ):
                raise exceptions.InvalidFieldValue("reschedule_before_date")
        if "utc" in body and body["utc"]:
            if not re.match(r"^[-\+]" + TIME_REGEX + r"$", body["utc"]):
                raise exceptions.InvalidFieldValue("utc")
            try:
                dateparser.parse("now", settings={"TIMEZONE": body["utc"]})
            except Exception:
                raise exceptions.InvalidFieldValue("utc")
        if "current_bracket_id" in body and tournament_id:
            bracket = db.query(Bracket).where(Bracket.id == body["current_bracket_id"]).first()
            if not bracket or bracket.tournament_id != tournament_id:
                raise exceptions.InvalidFieldValue("current_bracket_id")

    @check_body_fields(Tournament)
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
        logger.debug("Tournament {0} has been updated".format(tournament_id))
        return {}, 204

    @check_body_fields(Tournament, mandatory_fields=["guild_id", "name", "acronym"])
    @is_authorized(user=True)
    def post(self):
        body = request.json
        body["guild_id"] = str(body["guild_id"])
        body["guild_id_snowflake"] = str(body["guild_id"])
        self.assert_validate_body(body, None)
        tournament = Tournament(**body)
        db.add(tournament)
        bracket = Bracket(tournament_id=tournament.id, name=tournament.name)
        db.add(bracket)
        tournament.current_bracket_id = bracket.id
        db.update(tournament)
        logger.debug("Tournament {0} has been created".format(tournament.id))
        return get_tournament_data(tournament, True), 201

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
        logger.debug("Tournament {0} has been deleted".format(tournament_id))
        return {}, 204
