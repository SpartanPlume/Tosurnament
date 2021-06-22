from flask import Flask
from flask_restful import Api
from server.api.exceptions import ERRORS
from server.api.resources.auth import AuthResource
from server.api.resources.user import UserResource


app = Flask(__name__)
app.config["BUNDLE_ERRORS"] = True
api = Api(app, errors=ERRORS)

# Resources
api.add_resource(AuthResource, "/auth")
api.add_resource(UserResource, "/user")

if __name__ == "__main__":
    app.run(debug=True)
