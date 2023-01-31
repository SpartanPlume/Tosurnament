from flask import request, current_app, g


def get_string_with_session_id(string):
    session_id = "BOT"
    if "token" in g and g.token:
        session_id = str(g.token.discord_user_id)
    # TODO
    # elif request.headers
    return "[session: {0}] {1}".format(session_id, string)


def debug(string):
    current_app.logger.debug(get_string_with_session_id(string))


def info(string):
    current_app.logger.info(get_string_with_session_id(string))


def warn(string):
    current_app.logger.warn(get_string_with_session_id(string))


def error(string):
    current_app.logger.error(get_string_with_session_id(string))
