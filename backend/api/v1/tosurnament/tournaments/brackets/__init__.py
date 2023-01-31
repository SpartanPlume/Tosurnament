import re

from flask.views import MethodView
from flask import request

from api.globals import db, exceptions
from api.utils import is_authorized, check_body_fields, assert_str_field_length, DATABASE_DATE_REGEX
from api import logger
from common.databases.tosurnament.bracket import Bracket


def get_spreadsheets_data_of_bracket(bracket):
    response_spreadsheets = {}
    for spreadsheet_type, spreadsheet_class in Bracket.get_spreadsheet_types().items():
        spreadsheet = (
            db.query(spreadsheet_class).where(id=getattr(bracket, spreadsheet_type + "_spreadsheet_id")).first()
        )
        if spreadsheet:
            response_spreadsheets[spreadsheet_type + "_spreadsheet"] = spreadsheet.get_api_dict()
    return response_spreadsheets


def get_bracket_data(bracket, include_spreadsheets=False):
    bracket_data = bracket.get_api_dict()
    if include_spreadsheets:
        bracket_data = {**bracket_data, **get_spreadsheets_data_of_bracket(bracket)}
    return bracket_data


def delete_bracket_and_associated_spreadsheets(bracket):
    for spreadsheet_type, spreadsheet_class in Bracket.get_spreadsheet_types().items():
        spreadsheet_id = getattr(bracket, spreadsheet_type + "_spreadsheet_id")
        if spreadsheet_id > 0:
            spreadsheet = db.query(spreadsheet_class).where(id=spreadsheet_id).first()
            if spreadsheet:
                db.delete(spreadsheet)
                logger.debug(
                    "{0} spreadsheet {1} has been deleted".format(
                        spreadsheet_type.replace("_", " ").capitalize(), spreadsheet_id
                    )
                )
    bracket_id = bracket.id
    db.delete(bracket)
    logger.debug("Bracket {0} has been deleted".format(bracket_id))


class BracketsResource(MethodView):
    def _get_object(self, tournament_id, bracket_id):
        bracket = (
            db.query(Bracket).where(Bracket.tournament_id == tournament_id).where(Bracket.id == bracket_id).first()
        )
        if not bracket:
            raise exceptions.NotFound()
        return bracket

    @is_authorized(user=True)
    def get(self, tournament_id, bracket_id):
        request_args = request.args.to_dict()
        include_spreadsheets = request_args.pop("include_spreadsheets", "false").casefold() == "true"
        if bracket_id is None:
            return self.get_all(tournament_id, include_spreadsheets, request_args)
        bracket = self._get_object(tournament_id, bracket_id)
        return get_bracket_data(bracket, include_spreadsheets)

    def get_all(self, tournament_id, include_spreadsheets, request_args):
        brackets = db.query(Bracket).where(Bracket.tournament_id == tournament_id).where(**request_args).all()
        brackets_data = []
        for tournament in brackets:
            brackets_data.append(get_bracket_data(tournament, include_spreadsheets))
        return {
            "brackets": [bracket.get_api_dict() for bracket in db.query(Bracket).where(**request.args.to_dict()).all()]
        }

    def assert_validate_body(self, body):
        assert_str_field_length(body, "name", 128, min_length=1)
        assert_str_field_length(body, "role_id", 32)
        assert_str_field_length(body, "challonge", 64)
        assert_str_field_length(body, "post_result_channel_id", 32)
        assert_str_field_length(body, "current_round", 16)
        if "registration_end_date" in body and body["registration_end_date"]:
            if not re.match(DATABASE_DATE_REGEX, body["registration_end_date"]):
                raise exceptions.InvalidFieldValue("registration_end_date")
        for spreadsheet_type in Bracket.get_spreadsheet_types().keys():
            spreadsheet_id_field = spreadsheet_type + "_id"
            if spreadsheet_id_field in body:
                bracket_with_id = db.query(Bracket).where((spreadsheet_id_field, body[spreadsheet_id_field])).first()
                if bracket_with_id:
                    raise exceptions.InvalidFieldValue(spreadsheet_id_field)

    @check_body_fields(Bracket)
    @is_authorized(user=True)
    def put(self, tournament_id, bracket_id):
        bracket = self._get_object(tournament_id, bracket_id)
        body = request.json
        if "tournament_id" in body:
            if tournament_id != body["tournament_id"]:
                raise exceptions.BadRequest("tournament_id cannot be updated")
            del body["tournament_id"]
        self.assert_validate_body(body)
        bracket.update(**body)
        db.update(bracket)
        logger.debug("Bracket {0} has been updated".format(bracket_id))
        return {}, 204

    @check_body_fields(Bracket, mandatory_fields=["name"])
    @is_authorized(user=True)
    def post(self, tournament_id):
        body = request.json
        if "tournament_id" in body:
            if tournament_id != body["tournament_id"]:
                raise exceptions.BadRequest("tournament_id in body and request do not match")
            del body["tournament_id"]
        self.assert_validate_body(body)
        bracket = Bracket(**body, tournament_id=tournament_id)
        db.add(bracket)
        logger.debug("Bracket {0} has been created".format(bracket.id))
        return bracket.get_api_dict(), 201

    @is_authorized(user=True)
    def delete(self, tournament_id, bracket_id):
        brackets = db.query(Bracket).where(Bracket.tournament_id == tournament_id).all()
        if len(brackets) <= 1:
            raise exceptions.CannotRemoveLastBracket()
        bracket = self._get_object(tournament_id, bracket_id)
        delete_bracket_and_associated_spreadsheets(bracket)
        return {}, 204
