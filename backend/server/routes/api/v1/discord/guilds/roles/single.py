"""Route to a single role"""

import requests
from common.config import constants
from server import endpoints


def patch(handler, parameters, url_parameters, *ids_parameters):
    """PATCH method"""
    if not parameters:
        handler.logger.debug("Ignoring")
        handler.send_json("{}")
        return
    headers = {"Authorization": "Bot " + constants.BOT_TOKEN, "Content-Type": "application/json"}
    try:
        r = requests.patch(endpoints.DISCORD_GUILD_ROLE.format(*ids_parameters), headers=headers, data=parameters)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        handler.logger.exception("Couldn't patch the data from Discord API.")
        handler.logger.debug(r.text)
        handler.send_error(500, "Couldn't patch the data to Discord API.")
        return
    handler.send_json(r.text)


def delete(handler, parameters, url_parameters, *ids_parameters):
    """DELETE method"""
    headers = {"Authorization": "Bot " + constants.BOT_TOKEN}
    try:
        r = requests.delete(endpoints.DISCORD_GUILD_ROLE.format(*ids_parameters), headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        handler.logger.exception("Couldn't delete the data from Discord API.")
        handler.logger.debug(r.text)
        handler.send_error(500, "Couldn't delete the data from Discord API.")
        return
    handler.send_json(r.text)
