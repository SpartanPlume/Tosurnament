"""Route to a single guild"""

import requests
from common.config import constants
from server import endpoints, errors


def get(handler, parameters, url_parameters, *ids_parameters):
    """GET method"""
    headers = {"Authorization": "Bot " + constants.BOT_TOKEN}
    try:
        r = requests.get(endpoints.DISCORD_GUILD.format(*ids_parameters), headers=headers)
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
