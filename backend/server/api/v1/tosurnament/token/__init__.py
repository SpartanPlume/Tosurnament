import requests
import time
import uuid
import json

from flask.views import MethodView
from flask import request, current_app

from server.api.globals import db, endpoints, exceptions
from common.config import constants
from common.databases.tosurnament.token import Token


def get_user_id(access_token):
    headers = {"Authorization": "Bearer " + access_token}
    try:
        r = requests.get(endpoints.DISCORD_ME, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        raise exceptions.DiscordMeError()
    user = json.loads(r.text)
    return user["id"]


def store_token(data):
    token = None
    session_token = request.headers.get("Authorization")
    if session_token:
        token = db.query(Token).where(Token.session_token == session_token).first()
    if not token:
        token = Token()
        token.discord_user_id = get_user_id(data["access_token"])
        session_token = str(uuid.uuid4())
        token.session_token = session_token
        token.expiry_date = str(int(time.time()) + 2592000)
        db.add(token)
    token.access_token = data["access_token"]
    token.token_type = "user"
    token.access_token_expiry_date = str(int(time.time()) + data["expires_in"])
    token.refresh_token = data["refresh_token"]
    token.scope = data["scope"]
    db.update(token)
    current_app.logger.debug(
        "A token has successfully been created/updated for the user {0}".format(token.discord_user_id)
    )
    return session_token


class TokenResource(MethodView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # if request.remote_addr == "127.0.0.1":
        #    raise exceptions.Forbidden()

    def post(self):
        """POST method"""
        if "code" not in request.json:
            raise exceptions.BadRequest()
        data = {
            "client_id": constants.CLIENT_ID,
            "client_secret": constants.CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": request.json["code"],
            "redirect_uri": constants.DISCORD_REDIRECT_URI,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            r = requests.post(constants.DISCORD_OAUTH2_ENDPOINT + "/token", data=data, headers=headers)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise exceptions.DiscordTokenError()
        session_token = store_token(r.json())
        return {"session_token": session_token}
