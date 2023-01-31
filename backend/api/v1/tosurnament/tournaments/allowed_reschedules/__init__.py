import datetime

from flask.views import MethodView
from flask import request

from api.globals import db, exceptions
from api.utils import is_authorized, check_body_fields, assert_str_field_length, assert_int_field
from api import logger
from common.databases.tosurnament.allowed_reschedule import AllowedReschedule


class AllowedReschedulesResource(MethodView):
    def _get_object(self, tournament_id, allowed_reschedule_id):
        allowed_reschedule = (
            db.query(AllowedReschedule)
            .where(AllowedReschedule.tournament_id == tournament_id)
            .where(AllowedReschedule.id == allowed_reschedule_id)
            .first()
        )
        if not allowed_reschedule:
            raise exceptions.NotFound()
        now = datetime.datetime.utcnow()
        max_allowed_date = datetime.datetime.fromtimestamp(allowed_reschedule.created_at) + datetime.timedelta(
            hours=allowed_reschedule.allowed_hours
        )
        if now >= max_allowed_date:
            db.delete(allowed_reschedule)
            raise exceptions.NotFound()
        return allowed_reschedule

    @is_authorized(user=True)
    def get(self, tournament_id, allowed_reschedule_id):
        if allowed_reschedule_id is None:
            return self.get_all(tournament_id)
        return self._get_object(tournament_id, allowed_reschedule_id).get_api_dict()

    def get_all(self, tournament_id):
        allowed_reschedules = (
            db.query(AllowedReschedule)
            .where(AllowedReschedule.tournament_id == tournament_id)
            .where(**request.args.to_dict())
            .all()
        )
        real_allowed_reschedules = []
        now = datetime.datetime.utcnow()
        for allowed_reschedule in allowed_reschedules:
            max_allowed_date = datetime.datetime.fromtimestamp(allowed_reschedule.created_at) + datetime.timedelta(
                hours=allowed_reschedule.allowed_hours
            )
            if now >= max_allowed_date:
                db.delete(allowed_reschedule)
            else:
                real_allowed_reschedules.append(allowed_reschedule)
        return {
            "allowed_reschedules": [
                allowed_reschedule.get_api_dict() for allowed_reschedule in real_allowed_reschedules
            ]
        }

    def assert_validate_body(self, body):
        assert_str_field_length(body, "match_id", 32)
        assert_int_field(body, "allowed_hours", 1, 72)

    @check_body_fields(AllowedReschedule)
    @is_authorized(user=True)
    def put(self, tournament_id, allowed_reschedule_id):
        allowed_reschedule = self._get_object(tournament_id, allowed_reschedule_id)
        body = request.json
        if "tournament_id" in body:
            if tournament_id != body["tournament_id"]:
                raise exceptions.BadRequest("tournament_id cannot be updated")
            del body["tournament_id"]
        if "match_id" in body:
            if allowed_reschedule.match_id != body["match_id"]:
                raise exceptions.BadRequest("match_id cannot be updated")
            del body["match_id"]
        self.assert_validate_body(body)
        allowed_reschedule.update(**body)
        db.update(allowed_reschedule)
        logger.debug(
            "Allowed reschedule {0} for match id {1} has been updated".format(
                allowed_reschedule_id, allowed_reschedule.match_id
            )
        )
        return {}, 204

    @check_body_fields(AllowedReschedule, mandatory_fields=["match_id"])
    @is_authorized(user=True)
    def post(self, tournament_id):
        body = request.json
        if "tournament_id" in body:
            if tournament_id != body["tournament_id"]:
                raise exceptions.BadRequest("tournament_id in body and request do not match")
            del body["tournament_id"]
        allowed_reschedule = AllowedReschedule(**body, tournament_id=tournament_id)
        db.add(allowed_reschedule)
        logger.debug(
            "Allowed reschedule {0} for match id {1} has been created".format(
                allowed_reschedule.id, allowed_reschedule.match_id
            )
        )
        return allowed_reschedule.get_api_dict(), 201

    @is_authorized(user=True)
    def delete(self, tournament_id, allowed_reschedule_id):
        if allowed_reschedule_id is None:
            return self.delete_all(tournament_id)
        allowed_reschedule = self._get_object(tournament_id, allowed_reschedule_id)
        db.delete(allowed_reschedule)
        logger.debug(
            "Allowed reschedule {0} for match id {1} has been deleted".format(
                allowed_reschedule_id, allowed_reschedule.match_id
            )
        )
        return {}, 204

    def delete_all(self, tournament_id):
        try:
            allowed_reschedules = (
                db.query(AllowedReschedule)
                .where(AllowedReschedule.tournament_id == tournament_id)
                .where(**request.args.to_dict())
                .all()
            )
        except AttributeError:
            raise exceptions.BadRequest("Invalid arguments are present in the request")
        for allowed_reschedule in allowed_reschedules:
            db.delete(allowed_reschedule)
            logger.debug(
                "Allowed reschedule {0} for match id {1} has been deleted".format(
                    allowed_reschedule.id, allowed_reschedule.match_id
                )
            )
        return {}, 204
