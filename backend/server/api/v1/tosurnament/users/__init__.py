from flask.views import MethodView
from flask import request, current_app

from server.api.globals import db, exceptions
from common.databases.tosurnament.user import User
from server.api.utils import is_authorized


class UsersResource(MethodView):
    def _get_object(self, user_id):
        user = db.query(User).where(User.id == user_id).first()
        if not user:
            raise exceptions.NotFound()
        return user

    @is_authorized(user=False)
    def get(self, user_id):
        if user_id is None:
            return self.get_all()
        return self._get_object(user_id).get_api_dict()

    def get_all(self):
        request_args = request.args.to_dict()
        discord_id = request_args.pop("discord_id", None)
        if discord_id:
            request_args["discord_id"] = str(discord_id)
        if "osu_name_hash" in request_args:
            request_args["osu_name_hash"] = request_args["osu_name_hash"].casefold()
        return {"users": [user.get_api_dict() for user in db.query(User).where(**request_args).all()]}

    @is_authorized(user=False)
    def put(self, user_id):
        user = self._get_object(user_id)
        body = request.json
        if "discord_id" in body:
            del body["discord_id"]
        if "discord_id_snowflake" in body:
            del body["discord_id_snowflake"]
        if "osu_name_hash" in body:
            body["osu_name_hash"] = body["osu_name_hash"].casefold()
        user.update(**body)
        db.update(user)
        current_app.logger.debug("The user {0} has been updated successfully.".format(user_id))
        return {}, 204

    @is_authorized(user=False)
    def post(self):
        body = request.json
        if not body or not body["discord_id"] or not body["discord_id_snowflake"]:
            raise exceptions.MissingRequiredInformation()
        body["discord_id"] = str(body["discord_id"])
        if "osu_name_hash" in body:
            body["osu_name_hash"] = body["osu_name_hash"].casefold()
        user = User(**body)
        db.add(user)
        current_app.logger.debug("The user {0} has been created successfully.".format(user.id))
        return user.get_api_dict(), 201

    @is_authorized(user=False)
    def delete(self, user_id):
        user = self._get_object(user_id)
        db.delete(user)
        current_app.logger.debug("The user {0} has been deleted successfully.".format(user_id))
        return {}, 204
