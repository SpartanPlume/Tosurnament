import datetime

from flask.views import MethodView
from flask import request, current_app

from server.api.globals import db, exceptions
from server.api.utils import is_authorized
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

    @is_authorized(user=True)
    def put(self, tournament_id, allowed_reschedule_id):
        allowed_reschedule = self._get_object(tournament_id, allowed_reschedule_id)
        allowed_reschedule.update(**request.json)
        db.update(allowed_reschedule)
        current_app.logger.debug(
            "The allowed reschedule {0} for match id {1} has been updated successfully.".format(
                allowed_reschedule_id, allowed_reschedule.match_id
            )
        )
        return {}, 204

    @is_authorized(user=True)
    def post(self, tournament_id):
        body = request.json
        if not body or not body["match_id"]:
            raise exceptions.MissingRequiredInformation()
        if "tournament_id" in body:
            del body["tournament_id"]
        allowed_reschedule = AllowedReschedule(**body, tournament_id=tournament_id)
        db.add(allowed_reschedule)
        current_app.logger.debug(
            "The allowed reschedule {0} for match id {1} has been created successfully.".format(
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
        current_app.logger.debug(
            "The allowed reschedule {0} for match id {1} has been deleted successfully.".format(
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
            raise exceptions.BadRequest()
        for allowed_reschedule in allowed_reschedules:
            db.delete(allowed_reschedule)
            current_app.logger.debug(
                "The allowed reschedule {0} for match id {1} has been deleted successfully.".format(
                    allowed_reschedule.id, allowed_reschedule.match_id
                )
            )
        return {}, 204
