"""Route to all brackets"""

from common.databases.bracket import Bracket


def get(handler, parameters, url_parameters, *ids_parameters):
    """GET method"""
    tournament_id = ids_parameters
    results = handler.session.query(Bracket).where(Bracket.tournament_id == tournament_id).all()
    etag = handler.get_etag(results)
    if not etag:
        handler.send_error(304)
        return
    handler.send_object(results, etag)


def post(handler, parameters, url_parameters, *ids_parameters):
    """POST method"""
    tournament_id = ids_parameters
    if not parameters:
        handler.logger.debug("Ignoring")
        handler.send_json("{}")
        return
    obj = Bracket()
    for key, value in parameters.items():
        if key in obj.__dict__:
            setattr(obj, key, value)
    setattr(obj, "tournament_id", tournament_id)
    obj = handler.session.add(obj)
    handler.logger.debug("Created successfully")
    handler.send_object(obj)
