import re

from flask.views import MethodView
from flask import request

from server.api.globals import db, exceptions
from server.api.utils import is_authorized, check_body_fields, assert_str_field_length
from server.api import logger
from common.databases.tosurnament.guild import Guild


class GuildsResource(MethodView):
    def _get_object(self, guild_id):
        guild = db.query(Guild).where(Guild.id == guild_id).first()
        if not guild:
            raise exceptions.NotFound()
        return guild

    @is_authorized(user=True)
    def get(self, guild_id):
        if guild_id is None:
            return self.get_all()
        return self._get_object(guild_id).get_api_dict()

    def get_all(self):
        request_args = request.args.to_dict()
        guild_id = request_args.pop("guild_id", None)
        if guild_id:
            request_args["guild_id"] = str(guild_id)
        return {"guilds": [guild.get_api_dict() for guild in db.query(Guild).where(**request_args).all()]}

    def assert_validate_body(self, body):
        assert_str_field_length(body, "verified_role_id", 32)
        assert_str_field_length(body, "admin_role_id", 32)
        assert_str_field_length(body, "language", 8)

    @check_body_fields(Guild)
    @is_authorized(user=True)
    def put(self, guild_id):
        guild = self._get_object(guild_id)
        body = request.json
        if "guild_id" in body:
            del body["guild_id"]
        if "guild_id_snowflake" in body:
            if guild.guild_id_snowflake != str(body["guild_id_snowflake"]):
                raise exceptions.BadRequest("guild_id_snowflake cannot be updated")
            del body["guild_id_snowflake"]
        self.assert_validate_body(body)
        guild.update(**body)
        db.update(guild)
        logger.debug("Guild {0} has been updated".format(guild_id))
        return {}, 204

    @check_body_fields(Guild, mandatory_fields=["guild_id"])
    @is_authorized(user=True)
    def post(self):
        body = request.json
        body["guild_id"] = str(body["guild_id"])
        body["guild_id_snowflake"] = str(body["guild_id"])
        self.assert_validate_body(body)
        guild = Guild(**body)
        db.add(guild)
        logger.debug("Guild {0} has been created".format(guild.id))
        return guild.get_api_dict(), 201

    @is_authorized(user=True)
    def delete(self, guild_id):
        guild = self._get_object(guild_id)
        db.delete(guild)
        logger.debug("Guild {0} has been deleted".format(guild_id))
        return {}, 204
