"""Route to all guilds"""

import requests
from common.databases.token import Token
from server import endpoints, errors


def get(handler, parameters, url_parameters, *ids_parameters):
    """GET method"""
    token = handler.session.query(Token).where(Token.session_token == handler.session_token).first()
    if not token:
        handler.logger.debug("Unauthorized")
        handler.send_error(401, "Unauthorized.")
        return
    headers = {"Authorization": "Bearer " + token.access_token}
    try:
        r = requests.get(endpoints.DISCORD_ME_GUILDS, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        handler.logger.exception(errors.DISCORD_API_GET_ERROR_MESSAGE)
        handler.logger.debug(r.text)
        handler.send_error(500, errors.DISCORD_API_GET_ERROR_MESSAGE)
        return
    etag = handler.get_etag(r.text)
    if not etag:
        handler.send_error(304)
        return
    handler.send_json(r.text, etag)
