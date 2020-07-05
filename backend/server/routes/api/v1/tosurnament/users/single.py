"""Route to a single user"""

from common.databases.user import User

USER_DOES_NOT_EXIST_ERROR = "The user {0} does not exist."


def get(handler, parameters, url_parameters, *ids_parameters):
    """GET method"""
    user_id = ids_parameters
    user = handler.session.query(User).where(User.id == int(user_id)).first()
    if not user:
        error_message = USER_DOES_NOT_EXIST_ERROR.format(user_id)
        handler.logger.debug(error_message)
        handler.send_error(404, error_message)
        return
    etag = handler.get_etag(user)
    if not etag:
        handler.send_error(304)
        return
    handler.send_object(user, etag)


def put(handler, parameters, url_parameters, *ids_parameters):
    """PUT method"""
    user_id = ids_parameters
    user = handler.session.query(User).where(User.id == int(user_id)).first()
    if not user:
        error_message = USER_DOES_NOT_EXIST_ERROR.format(user_id)
        handler.logger.debug(error_message)
        handler.send_error(404, error_message)
        return
    user.update(parameters)
    handler.session.update(user)
    handler.logger.debug("Updated successfully")
    handler.send_json("{}")


def delete(handler, parameters, url_parameters, *ids_parameters):
    """DELETE method"""
    user_id = ids_parameters
    user = handler.session.query(User).where(User.id == int(user_id)).first()
    if not user:
        error_message = USER_DOES_NOT_EXIST_ERROR.format(user_id)
        handler.logger.debug(error_message)
        handler.send_error(404, error_message)
        return
    handler.session.delete(user)
    handler.logger.debug("Deleted successfully")
    handler.send_json("{}")
