from flask.views import MethodView
from flask import request, current_app

from server.api.globals import db, exceptions
from server.api.utils import is_authorized
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
            try:
                request_args["guild_id"] = int(guild_id)
            except ValueError:
                raise exceptions.BadRequest()
        return {"guilds": [guild.get_api_dict() for guild in db.query(Guild).where(**request_args).all()]}

    @is_authorized(user=True)
    def put(self, guild_id):
        guild = self._get_object(guild_id)
        guild.update(**request.json)
        db.update(guild)
        current_app.logger.debug("The guild {0} has been updated successfully.".format(guild_id))
        return {}, 204

    @is_authorized(user=True)
    def post(self):
        body = request.json
        if not body or not body["guild_id"] or not body["guild_id_snowflake"]:
            raise exceptions.MissingRequiredInformation()
        try:
            body["guild_id"] = int(body["guild_id"])
        except ValueError:
            raise exceptions.BadRequest()
        guild = Guild(**body)
        db.add(guild)
        current_app.logger.debug("The guild {0} has been created successfully.".format(guild.id))
        return guild.get_api_dict(), 201

    @is_authorized(user=True)
    def delete(self, guild_id):
        guild = self._get_object(guild_id)
        db.delete(guild)
        current_app.logger.debug("The guild {0} has been deleted successfully.".format(guild_id))
        return {}, 204
