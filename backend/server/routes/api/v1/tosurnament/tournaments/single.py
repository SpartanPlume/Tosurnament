"""Route to a single tournament"""

from common.databases.tournament import Tournament

TOURNAMENT_DOES_NOT_EXIST_ERROR = "The tournament {0} does not exist."


def put(handler, parameters, url_parameters, *ids_parameters):
    """PUT method"""
    tournament_id = ids_parameters
    tournament = handler.session.query(Tournament).where(Tournament.id == int(tournament_id)).first()
    if not tournament:
        error_message = TOURNAMENT_DOES_NOT_EXIST_ERROR.format(tournament_id)
        handler.logger.debug(error_message)
        handler.send_error(404, error_message)
        return
    tournament.update(parameters)
    handler.session.update(tournament)
    handler.logger.debug("Updated successfully")
    handler.send_json("{}")


def delete(handler, parameters, url_parameters, *ids_parameters):
    """DELETE method"""
    tournament_id = ids_parameters
    tournament = handler.session.query(Tournament).where(Tournament.id == int(tournament_id)).first()
    if not tournament:
        error_message = TOURNAMENT_DOES_NOT_EXIST_ERROR.format(tournament_id)
        handler.logger.debug(error_message)
        handler.send_error(404, error_message)
        return
    handler.session.delete(tournament)
    handler.logger.debug("Deleted successfully")
    handler.send_json("{}")
