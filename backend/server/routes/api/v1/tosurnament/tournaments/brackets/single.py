"""Route to a single bracket"""

from common.databases.bracket import Bracket

BRACKET_DOES_NOT_EXIST_ERROR = "The bracket {0} does not exist."


def get(handler, parameters, url_parameters, *ids_parameters):
    """GET method"""
    tournament_id, bracket_id = ids_parameters
    bracket = (
        handler.session.query(Bracket)
        .where(Bracket.tournament_id == int(tournament_id))
        .where(Bracket.id == int(bracket_id))
        .first()
    )
    if not bracket:
        error_message = BRACKET_DOES_NOT_EXIST_ERROR.format(bracket_id)
        handler.logger.debug(error_message)
        handler.send_error(404, error_message)
        return
    etag = handler.get_etag(bracket)
    if not etag:
        handler.send_error(304)
        return
    handler.send_object(bracket, etag)


def put(handler, parameters, url_parameters, *ids_parameters):
    """PUT method"""
    tournament_id, bracket_id = ids_parameters
    bracket = (
        handler.session.query(Bracket)
        .where(Bracket.tournament_id == int(tournament_id))
        .where(Bracket.id == int(bracket_id))
        .first()
    )
    if not bracket:
        error_message = BRACKET_DOES_NOT_EXIST_ERROR.format(bracket_id)
        handler.logger.debug(error_message)
        handler.send_error(404, error_message)
        return
    bracket.update(parameters)
    handler.session.update(bracket)
    handler.logger.debug("Updated successfully")
    handler.send_json("{}")


def delete(handler, parameters, url_parameters, *ids_parameters):
    """DELETE method"""
    tournament_id, bracket_id = ids_parameters
    bracket = (
        handler.session.query(Bracket)
        .where(Bracket.tournament_id == int(tournament_id))
        .where(Bracket.id == int(bracket_id))
        .first()
    )
    if not bracket:
        error_message = BRACKET_DOES_NOT_EXIST_ERROR.format(bracket_id)
        handler.logger.debug(error_message)
        handler.send_error(404, error_message)
        return
    handler.session.delete(bracket)
    handler.logger.debug("Deleted successfully")
    handler.send_json("{}")
