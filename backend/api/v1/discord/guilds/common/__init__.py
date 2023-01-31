import requests

from flask import g
from flask.views import MethodView

from api.globals import endpoints, exceptions
from api.utils import is_authorized

from common.config import constants


class DiscordCommonGuildsResource(MethodView):
    @is_authorized(local=False, user=True)
    def get(self):
        headers = {"Authorization": "Bot " + constants.BOT_TOKEN}
        try:
            r_bot = requests.get(endpoints.DISCORD_ME_GUILDS, params={"limit": 200}, headers=headers)
            r_bot.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error = r_bot.json()
            raise exceptions.DiscordException(r_bot.status_code, e.response.reason, error)
        except requests.exceptions.ConnectionError:
            raise exceptions.DiscordError()
        bot_guilds = r_bot.json()
        headers = {"Authorization": "Bearer " + g.token.access_token}
        try:
            r_user = requests.get(endpoints.DISCORD_ME_GUILDS, headers=headers)
            r_user.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error = r_user.json()
            raise exceptions.DiscordException(r_user.status_code, e.response.reason, error)
        except requests.exceptions.ConnectionError:
            raise exceptions.DiscordError()
        user_guilds = r_user.json()
        common_guilds = []
        for bot_guild in bot_guilds:
            for user_guild in user_guilds:
                if user_guild["id"] == bot_guild["id"]:
                    common_guilds.append(bot_guild)
        return {"guilds": common_guilds}
