import requests
from flask.views import MethodView
from flask import request, current_app

from server.api.globals import db, exceptions, endpoints
from common.databases.tosurnament.user import User
from common.config import constants


class AuthResource(MethodView):
    def post(self):
        body = request.json
        if "tosurnament_code" not in body or "osu_code" not in body:
            raise exceptions.BadRequest()
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
        token_request = requests.post(endpoints.OSU_TOKEN, data=parameters)
        if not token_request.ok:
            raise exceptions.OsuTokenError()
        token_results = token_request.json()
        me_headers = {"Authorization": "Bearer " + token_results["access_token"]}
        me_request = requests.get(endpoints.OSU_ME, headers=me_headers)
        if not me_request.ok:
            raise exceptions.OsuMeError()
        me_results = me_request.json()
        user.osu_id = str(me_results["id"])
        user.osu_name = me_results["username"]
        user.osu_name_hash = me_results["username"]
        if me_results["previous_usernames"]:
            user.osu_previous_name = me_results["previous_usernames"][-1]
        user.verified = True
        db.update(user)
        current_app.logger.debug(
            "The user with the osu id {0} has been authentificated successfully.".format(user.osu_id)
        )
        return {}, 204
