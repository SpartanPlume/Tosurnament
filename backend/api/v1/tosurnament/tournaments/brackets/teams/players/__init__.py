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
from api.v1.tosurnament.players.brackets import get_bracket_data, delete_bracket_and_associated_spreadsheets
from common.databases.tosurnament.bracket import Bracket
from common.databases.tosurnament.team import Team
from common.databases.tosurnament.player import Player
from common.databases.tosurnament.user import User
from common.databases.tosurnament.allowed_reschedule import AllowedReschedule
from common.api import challonge as challonge_api


def get_player_data(player):
    user = db.query(User).where(User.id == player.user_id).first()
    if not user:
        logger.error("Could not find user of id {0} linked to the player of id {1}")
        raise exceptions.NotFound()
    return {**user.get_api_dict(), **player.get_api_dict()}


class PlayersResource(MethodView):
    def _get_object(self, player_id):
        player = db.query(Player).where(Player.id == player_id).first()
        if not player:
            raise exceptions.NotFound()
        return player

    @is_authorized(user=True)
    def get(self, player_id):
        request_args = request.args.to_dict()
        if player_id is None:
            return self.get_all(request_args)
        player = self._get_object(player_id)
        return get_player_data(player)

    def get_all(self, request_args):
        players = db.query(Player).where(**request_args).all()
        players_data = []
        for player in players:
            players_data.append(get_player_data(player))
        return {"players": players_data}

    def assert_validate_body(self, body, player_id):
        assert_str_field_length(body, "name", 32, min_length=1)
        if "utc" in body and body["utc"]:
            if not re.match(r"^[-\+]" + TIME_REGEX + r"$", body["utc"]):
                raise exceptions.InvalidFieldValue("utc")
            try:
                dateparser.parse("now", settings={"TIMEZONE": body["utc"]})
            except Exception:
                raise exceptions.InvalidFieldValue("utc")
        if "team_id" in body and player_id:
            team = db.query(Team).where(Team.id == body["team_id"]).first()
            if not team:
                raise exceptions.InvalidFieldValue("team_id")

    @check_body_fields(Player)
    @is_authorized(user=True)
    def put(self, player_id):
        player = self._get_object(player_id)
        body = request.json
        if "guild_id" in body:
            del body["guild_id"]
        if "guild_id_snowflake" in body:
            if player.guild_id_snowflake != str(body["guild_id_snowflake"]):
                raise exceptions.BadRequest("guild_id_snowflake cannot be updated")
            del body["guild_id_snowflake"]
        if "challonge" in body:
            body["challonge"] = challonge_api.extract_player_id(body["challonge"])
        self.assert_validate_body(body, player_id)
        player.update(**body)
        db.update(player)
        logger.debug("Player {0} has been updated".format(player_id))
        return {}, 204

    @check_body_fields(Player, mandatory_fields=["guild_id", "name", "acronym"])
    @is_authorized(user=True)
    def post(self):
        body = request.json
        body["guild_id"] = str(body["guild_id"])
        body["guild_id_snowflake"] = str(body["guild_id"])
        self.assert_validate_body(body, None)
        player = Player(**body)
        db.add(player)
        bracket = Bracket(player_id=player.id, name=player.name)
        db.add(bracket)
        player.current_bracket_id = bracket.id
        db.update(player)
        logger.debug("Player {0} has been created".format(player.id))
        return get_player_data(player, True), 201

    @is_authorized(user=True)
    def delete(self, player_id):
        player = self._get_object(player_id)
        brackets = db.query(Bracket).where(Bracket.player_id == player_id).all()
        for bracket in brackets:
            delete_bracket_and_associated_spreadsheets(bracket)
        allowed_reschedules = db.query(AllowedReschedule).where(AllowedReschedule.player_id == player_id).all()
        for allowed_reschedule in allowed_reschedules:
            logger.debug(
                "Allowed reschedule {0} for the match id {1} has been deleted".format(
                    allowed_reschedule.id, allowed_reschedule.match_id
                )
            )
            db.delete(allowed_reschedule)
        db.delete(player)
        logger.debug("Player {0} has been deleted".format(player_id))
        return {}, 204
