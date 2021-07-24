from flask.views import MethodView
from flask import request, current_app

from server.api.globals import db, exceptions
from common.databases.tosurnament.bracket import Bracket
from common.databases.tosurnament.spreadsheets.schedules_spreadsheet import SchedulesSpreadsheet
from common.api import spreadsheet as spreadsheet_api


class SchedulesSpreadsheetResource(MethodView):
    def _get_object(self, tournament_id, bracket_id, spreadsheet_id):
        bracket = (
            db.query(Bracket).where(Bracket.tournament_id == tournament_id).where(Bracket.id == bracket_id).first()
        )
        if not bracket or bracket.schedules_spreadsheet_id != spreadsheet_id:
            raise exceptions.NotFound()
        spreadsheet = db.query(SchedulesSpreadsheet).where(SchedulesSpreadsheet.id == spreadsheet_id).first()
        if not spreadsheet:
            raise exceptions.NotFound()
        return spreadsheet

    def get(self, tournament_id, bracket_id, spreadsheet_id):
        return self._get_object(tournament_id, bracket_id, spreadsheet_id).get_api_dict()

    def put(self, tournament_id, bracket_id, spreadsheet_id):
        spreadsheet = self._get_object(tournament_id, bracket_id, spreadsheet_id)
        spreadsheet.update(**request.json)
        db.update(spreadsheet)
        current_app.logger.debug("The schedules spreadsheet {0} has been updated successfully.".format(spreadsheet_id))
        return {}, 204

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
        spreadsheet = SchedulesSpreadsheet(**body)
        db.add(spreadsheet)
        bracket.schedules_spreadsheet_id = spreadsheet.id
        db.update(bracket)
        current_app.logger.debug(
            "The schedules spreadsheet {0} for the bracket {1} has been created successfully.".format(
                spreadsheet.id, bracket_id
            )
        )
        return spreadsheet.get_api_dict(), 201

    def delete(self, spreadsheet_id):
        spreadsheet = self._get_object(spreadsheet_id)
        db.delete(spreadsheet)
        current_app.logger.debug("The schedules spreadsheet {0} has been deleted successfully.".format(spreadsheet_id))
        return {}, 204
