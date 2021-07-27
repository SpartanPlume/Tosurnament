from flask.views import MethodView
from flask import request, current_app

from server.api.globals import db, exceptions
from server.api.utils import is_authorized
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
                current_app.logger.debug(
                    "The {0} spreadsheet {1} has been deleted successfully.".format(
                        spreadsheet_type.replace("_", " "), spreadsheet_id
                    )
                )
    db.delete(bracket)
    current_app.logger.debug("The bracket {0} has been deleted successfully.".format(bracket.id))


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

    @is_authorized(user=True)
    def put(self, tournament_id, bracket_id):
        bracket = self._get_object(tournament_id, bracket_id)
        bracket.update(**request.json)
        db.update(bracket)
        current_app.logger.debug("The bracket {0} has been updated successfully.".format(bracket_id))
        return {}, 204

    @is_authorized(user=True)
    def post(self, tournament_id):
        body = request.json
        if not body or not body["name"]:
            raise exceptions.MissingRequiredInformation()
        if "tournament_id" in body:
            del body["tournament_id"]
        bracket = Bracket(**body, tournament_id=tournament_id)
        db.add(bracket)
        current_app.logger.debug("The bracket {0} has been created successfully.".format(bracket.id))
        return bracket.get_api_dict(), 201

    @is_authorized(user=True)
    def delete(self, tournament_id, bracket_id):
        brackets = db.query(Bracket).where(Bracket.tournament_id == tournament_id).all()
        if len(brackets) <= 1:
            raise exceptions.CannotRemoveLastBracket()
        bracket = self._get_object(tournament_id, bracket_id)
        delete_bracket_and_associated_spreadsheets(bracket)
        return {}, 204
