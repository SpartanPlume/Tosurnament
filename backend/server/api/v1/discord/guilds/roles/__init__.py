import requests

from flask.views import MethodView

from server.api.globals import endpoints, exceptions
from server.api.utils import is_authorized

from common.config import constants


class DiscordRolesResource(MethodView):
    @is_authorized(user=True)
    def get(self, guild_id, role_id):
        if role_id is None:
            return self.get_all(guild_id)
        raise exceptions.NotFound()

    def get_all(self, guild_id):
        headers = {"Authorization": "Bot " + constants.BOT_TOKEN}
        try:
            r = requests.get(endpoints.DISCORD_GUILD_ROLES.format(guild_id), headers=headers)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise exceptions.DiscordGetError()
        return {"roles": r.json()}
