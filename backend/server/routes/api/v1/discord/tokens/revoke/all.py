"""Route to revoke a token"""

import requests
from common.config import constants
from common.databases.token import Token
from server import endpoints, errors


def post(handler, parameters, url_parameters, *ids_parameters):
    """POST method"""
    token = handler.session.query(Token).where(Token.session_token == handler.session_token).first()
    if not token:
        handler.logger.debug("Invalid token")
        handler.send_json(401, "This token doesn't exist.")
        return
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"client_id": constants.CLIENT_ID, "client_secret": constants.CLIENT_SECRET, "token": token.access_token}
    try:
        r = requests.post(endpoints.DISCORD_TOKEN_REVOKE, headers=headers, data=data)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        handler.logger.exception(errors.DISCORD_API_POST_ERROR_MESSAGE)
        handler.logger.debug(r.text)
        handler.send_error(500, errors.DISCORD_API_POST_ERROR_MESSAGE)
        return
    handler.session.delete(token)
    handler.send_json("{}")
