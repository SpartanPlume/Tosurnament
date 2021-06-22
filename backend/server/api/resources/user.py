from flask_restful import Resource

from server.api.db import db
from common.databases.user import User


class UserResource(Resource):
    def get(self):
        users = db.query(User).all()
        response = []
        for user in users:
            user_table_dict = user.get_table_dict()
            tmp_response = {}
            for key, value in user_table_dict.items():
                if not isinstance(value, bytes):
                    tmp_response[key] = value
            response.append(tmp_response)
        return response
