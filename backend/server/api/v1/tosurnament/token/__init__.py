import datetime
import requests
import uuid
import json

from flask.views import MethodView
from flask import request, g

from server.api.globals import db, endpoints, exceptions
from common.config import constants
from common.databases.tosurnament.token import Token
from server.api import logger


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
        token.expiry_date = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        db.add(token)
    token.access_token = data["access_token"]
    token.token_type = "user"
    token.access_token_expiry_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=data["expires_in"])
    token.refresh_token = data["refresh_token"]
    token.scope = data["scope"]
    db.update(token)
    g.token = token
    logger.debug("Token has been created")
    return session_token


class TokenResource(MethodView):
    def post(self):
        """POST method"""
        if "code" not in request.json:
            raise exceptions.MissingRequiredInformation(["code"])
        data = {
            "client_id": str(constants.DISCORD_CLIENT_ID),
            "client_secret": constants.DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": request.json["code"],
            "redirect_uri": constants.DISCORD_REDIRECT_URI,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            r = requests.post(endpoints.DISCORD_TOKEN, data=data, headers=headers)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error = r.json()
            raise exceptions.ExternalException(r.status_code, e.response.reason, error["message"])
        except requests.exceptions.ConnectionError:
            raise exceptions.DiscordError()
        session_token = store_token(r.json())
        return {"session_token": session_token}
