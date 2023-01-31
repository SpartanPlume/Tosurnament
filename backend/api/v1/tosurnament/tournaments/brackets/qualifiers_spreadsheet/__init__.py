from flask.views import MethodView
from flask import request

from api.globals import db, exceptions
from api.utils import is_authorized, check_body_fields, assert_range_field, assert_str_field_length
from api import logger
from common.databases.tosurnament.bracket import Bracket
from common.databases.tosurnament.spreadsheets.qualifiers_spreadsheet import QualifiersSpreadsheet
from common.api import spreadsheet as spreadsheet_api


class QualifiersSpreadsheetResource(MethodView):
    def _get_object(self, tournament_id, bracket_id, spreadsheet_id):
        bracket = (
            db.query(Bracket).where(Bracket.tournament_id == tournament_id).where(Bracket.id == bracket_id).first()
        )
        if not bracket or bracket.qualifiers_spreadsheet_id != spreadsheet_id:
            raise exceptions.NotFound()
        spreadsheet = db.query(QualifiersSpreadsheet).where(QualifiersSpreadsheet.id == spreadsheet_id).first()
        if not spreadsheet:
            raise exceptions.NotFound()
        return spreadsheet

    @is_authorized(user=True)
    def get(self, tournament_id, bracket_id, spreadsheet_id):
        return self._get_object(tournament_id, bracket_id, spreadsheet_id).get_api_dict()

    def assert_validate_body(self, body):
        assert_str_field_length(body, "spreadsheet_id", 64, min_length=1)
        assert_str_field_length(body, "sheet_name", 128)
        assert_range_field(body, "range_lobby_id")
        assert_range_field(body, "range_teams")
        assert_range_field(body, "range_referee")
        assert_range_field(body, "range_date")
        assert_range_field(body, "range_time")

    @check_body_fields(QualifiersSpreadsheet)
    @is_authorized(user=True)
    def put(self, tournament_id, bracket_id, spreadsheet_id):
        spreadsheet = self._get_object(tournament_id, bracket_id, spreadsheet_id)
        body = request.json
        if "spreadsheet_id" in body:
            body["spreadsheet_id"] = spreadsheet_api.extract_spreadsheet_id(body["spreadsheet_id"])
        self.assert_validate_body(body)
        spreadsheet.update(**body)
        db.update(spreadsheet)
        logger.debug("Qualifiers spreadsheet {0} has been updated".format(spreadsheet_id))
        return {}, 204

    @check_body_fields(QualifiersSpreadsheet, mandatory_fields=["spreadsheet_id"])
    @is_authorized(user=True)
    def post(self, tournament_id, bracket_id):
        bracket = (
            db.query(Bracket).where(Bracket.tournament_id == tournament_id).where(Bracket.id == bracket_id).first()
        )
        if not bracket:
            raise exceptions.NotFound()
        body = request.json
        body["spreadsheet_id"] = spreadsheet_api.extract_spreadsheet_id(body["spreadsheet_id"])
        self.assert_validate_body(body)
        spreadsheet = QualifiersSpreadsheet(**body)
        db.add(spreadsheet)
        bracket.qualifiers_spreadsheet_id = spreadsheet.id
        db.update(bracket)
        logger.debug(
            "Qualifiers spreadsheet {0} for the bracket {1} has been created".format(spreadsheet.id, bracket_id)
        )
        return spreadsheet.get_api_dict(), 201

    @is_authorized(user=True)
    def delete(self, tournament_id, bracket_id, spreadsheet_id):
        spreadsheet = self._get_object(tournament_id, bracket_id, spreadsheet_id)
        db.delete(spreadsheet)
        logger.debug("Qualifiers spreadsheet {0} has been deleted".format(spreadsheet_id))
        return {}, 204
