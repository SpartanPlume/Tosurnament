import requests
from flask_restful import Resource, reqparse
from server.api import exceptions
from server.api.db import db
from common.config import constants

from common.databases.user import User


class AuthResource(Resource):
    def post(self):
        post_parser = reqparse.RequestParser()
        post_parser.add_argument(
            "tosurnament_code",
            required=True,
            type=str,
        )
        post_parser.add_argument(
            "osu_code",
            required=True,
            type=str,
        )
        args = post_parser.parse_args()
        user = db.query(User).where(User.code == args.tosurnament_code).first()
        if not user:
            raise exceptions.InternalServerError()
        if user.verified:
            raise exceptions.UserAlreadyVerified()
        parameters = {
            "client_id": constants.OSU_CLIENT_ID,
            "client_secret": constants.OSU_CLIENT_SECRET,
            "code": args.osu_code,
            "grant_type": "authorization_code",
            "redirect_uri": constants.OSU_REDIRECT_URI,
        }
        token_request = requests.post("https://osu.ppy.sh/oauth/token", data=parameters)
        if not token_request.ok:
            raise exceptions.OsuTokenError()
        token_results = token_request.json()
        me_headers = {"Authorization": "Bearer " + token_results["access_token"]}
        me_request = requests.get("https://osu.ppy.sh/api/v2/me/osu", headers=me_headers)
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
