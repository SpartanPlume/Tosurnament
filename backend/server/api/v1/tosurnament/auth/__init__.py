import requests
from flask.views import MethodView
from flask import request

from server.api.globals import db, exceptions, endpoints
from server.api import logger
from common.databases.tosurnament.user import User
from common.config import constants


class AuthResource(MethodView):
    def post(self):
        body = request.json
        if "tosurnament_code" not in body or "osu_code" not in body:
            raise exceptions.MissingRequiredInformation(["tournament_code", "osu_code"])
        user = db.query(User).where(User.code == body["tosurnament_code"]).first()
        if not user:
            raise exceptions.InternalServerError()
        if user.verified:
            raise exceptions.UserAlreadyVerified()
        parameters = {
            "client_id": constants.OSU_CLIENT_ID,
            "client_secret": constants.OSU_CLIENT_SECRET,
            "code": body["osu_code"],
            "grant_type": "authorization_code",
            "redirect_uri": constants.OSU_REDIRECT_URI,
        }
        try:
            token_request = requests.post(endpoints.OSU_TOKEN, data=parameters)
            token_request.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise exceptions.ExternalException(token_request.status_code, e.response.reason, "Could not exchange token")
        except requests.exceptions.ConnectionError:
            raise exceptions.OsuError()
        token_results = token_request.json()
        me_headers = {"Authorization": "Bearer " + token_results["access_token"]}
        try:
            me_request = requests.get(endpoints.OSU_ME, headers=me_headers)
            me_request.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise exceptions.ExternalException(
                me_request.status_code, e.response.reason, "Could not get profile information"
            )
        except requests.exceptions.ConnectionError:
            raise exceptions.OsuError()
        me_results = me_request.json()
        user.osu_id = str(me_results["id"])
        user.osu_name = me_results["username"]
        user.osu_name_hash = me_results["username"].casefold()
        if me_results["previous_usernames"]:
            user.osu_previous_name = me_results["previous_usernames"][-1]
        user.verified = True
        db.update(user)
        logger.debug("User with the osu id {0} has been authentificated".format(user.osu_id))
        return {}, 204
