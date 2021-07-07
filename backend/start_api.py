from flask import Flask
from flask_restful import Api
from server.api.exceptions import ERRORS
from server.api.resources.auth import AuthResource
from server.api.resources.users import UsersResource


app = Flask(__name__)
app.config["BUNDLE_ERRORS"] = True
api = Api(app, errors=ERRORS)

# Resources
api.add_resource(AuthResource, "/auth")
api.add_resource(UsersResource, "/users")

if __name__ == "__main__":
    app.run(debug=True)
