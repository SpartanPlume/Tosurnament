"""Route to all users"""

from common.databases.user import User


def get(handler, parameters, url_parameters, *ids_parameters):
    """GET method"""
    results = handler.session.query(User).all()
    etag = handler.get_etag(results)
    if not etag:
        handler.send_error(304)
        return
    handler.send_object(results, etag)


def post(handler, parameters, url_parameters, *ids_parameters):
    """POST method"""
    if not parameters:
        handler.logger.debug("Ignoring")
        handler.send_json("{}")
        return
    obj = User()
    for key, value in parameters.items():
        if key in obj.__dict__:
            setattr(obj, key, value)
    obj = handler.session.add(obj)
    handler.logger.debug("Created successfully")
    handler.send_object(obj)
