import requests

from flask.views import MethodView
from flask import g

from server.api.globals import db, endpoints, exceptions
from server.api.utils import is_authorized
from server.api import logger
from common.config import constants


class RevokeTokenResource(MethodView):
    @is_authorized(local=False, user=True)
    def post(self):
        """POST method"""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": str(constants.DISCORD_CLIENT_ID),
            "client_secret": constants.DISCORD_CLIENT_SECRET,
            "token": g.token.access_token,
        }
        db.delete(g.token)
        try:
            r = requests.post(endpoints.DISCORD_TOKEN_REVOKE, data=data, headers=headers)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise exceptions.DiscordRevokeTokenError()
        logger.debug("Token has been deleted")
        return {}, 204
