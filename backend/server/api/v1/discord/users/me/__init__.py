import requests

from flask import g
from flask.views import MethodView

from server.api.globals import endpoints, exceptions
from server.api.utils import is_authorized


class DiscordUsersMeResource(MethodView):
    @is_authorized(local=False, user=True)
    def get(self):
        headers = {"Authorization": "Bearer " + g.token.access_token}
        try:
            r = requests.get(endpoints.DISCORD_ME, headers=headers)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error = r.json()
            raise exceptions.DiscordException(r.status_code, e.response.reason, error)
        except requests.exceptions.ConnectionError:
            raise exceptions.DiscordError()
        user = r.json()
        return user, 200
