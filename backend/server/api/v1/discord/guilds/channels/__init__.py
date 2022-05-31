import requests

from flask.views import MethodView

from server.api.globals import endpoints, exceptions
from server.api.utils import is_authorized
from server.api import logger

from common.config import constants


class DiscordChannelsResource(MethodView):
    @is_authorized(user=True)
    def get(self, guild_id, channel_id):
        if channel_id is None:
            return self.get_all(guild_id)
        raise exceptions.NotFound()

    def get_all(self, guild_id):
        headers = {"Authorization": "Bot " + constants.BOT_TOKEN}
        try:
            r = requests.get(endpoints.DISCORD_GUILD_CHANNELS.format(guild_id), headers=headers)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error = r.json()
            raise exceptions.ExternalException(r.status_code, e.response.reason, error["message"])
        except requests.exceptions.ConnectionError:
            raise exceptions.DiscordError()
        return {"channels": r.json()}
