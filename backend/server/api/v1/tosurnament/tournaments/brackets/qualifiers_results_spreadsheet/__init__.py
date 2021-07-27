from flask.views import MethodView
from flask import request, current_app

from server.api.globals import db, exceptions
from server.api.utils import is_authorized
from common.databases.tosurnament.bracket import Bracket
from common.databases.tosurnament.spreadsheets.qualifiers_results_spreadsheet import QualifiersResultsSpreadsheet
from common.api import spreadsheet as spreadsheet_api


class QualifiersResultsSpreadsheetResource(MethodView):
    def _get_object(self, tournament_id, bracket_id, spreadsheet_id):
        bracket = (
            db.query(Bracket).where(Bracket.tournament_id == tournament_id).where(Bracket.id == bracket_id).first()
        )
        if not bracket or bracket.qualifiers_results_spreadsheet_id != spreadsheet_id:
            raise exceptions.NotFound()
        spreadsheet = (
            db.query(QualifiersResultsSpreadsheet).where(QualifiersResultsSpreadsheet.id == spreadsheet_id).first()
        )
        if not spreadsheet:
            raise exceptions.NotFound()
        return spreadsheet

    @is_authorized(user=True)
    def get(self, tournament_id, bracket_id, spreadsheet_id):
        return self._get_object(tournament_id, bracket_id, spreadsheet_id).get_api_dict()

    @is_authorized(user=True)
    def put(self, tournament_id, bracket_id, spreadsheet_id):
        spreadsheet = self._get_object(tournament_id, bracket_id, spreadsheet_id)
        spreadsheet.update(**request.json)
        db.update(spreadsheet)
        current_app.logger.debug(
            "The qualifiers results spreadsheet {0} has been updated successfully.".format(spreadsheet_id)
        )
        return {}, 204

    @is_authorized(user=True)
    def post(self, tournament_id, bracket_id):
        bracket = (
            db.query(Bracket).where(Bracket.tournament_id == tournament_id).where(Bracket.id == bracket_id).first()
        )
        if not bracket:
            raise exceptions.NotFound()
        body = request.json
        if not body or not body["spreadsheet_id"]:
            raise exceptions.MissingRequiredInformation()
        body["spreadsheet_id"] = spreadsheet_api.extract_spreadsheet_id(body["spreadsheet_id"])
        spreadsheet = QualifiersResultsSpreadsheet(**body)
        db.add(spreadsheet)
        bracket.qualifiers_results_spreadsheet_id = spreadsheet.id
        db.update(bracket)
        current_app.logger.debug(
            "The qualifiers results spreadsheet {0} for the bracket {1} has been created successfully.".format(
                spreadsheet.id, bracket_id
            )
        )
        return spreadsheet.get_api_dict(), 201

    @is_authorized(user=True)
    def delete(self, spreadsheet_id):
        spreadsheet = self._get_object(spreadsheet_id)
        db.delete(spreadsheet)
        current_app.logger.debug(
            "The qualifiers results spreadsheet {0} has been deleted successfully.".format(spreadsheet_id)
        )
        return {}, 204
