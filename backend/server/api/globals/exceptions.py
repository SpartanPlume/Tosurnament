from werkzeug.exceptions import HTTPException


class ApiException(HTTPException):
    code = 500
    title = "Unknown Error"
    description = "Unknown Error"


class ExternalException(ApiException):
    def __init__(self, code, title, description):
        self.code = code
        self.title = title
        self.description = description


class BadRequest(ApiException):
    code = 400
    title = "Bad Request"
    description = "Bad Request"

    def __init__(self, description="Bad Request"):
        self.description = description


class UserAlreadyVerified(BadRequest):
    description = "User is already verified"

    def __init__(self):
        pass


class CannotRemoveLastBracket(BadRequest):
    description = "Cannot remove the last bracket of a tournament"

    def __init__(self):
        pass


class MissingRequiredInformation(BadRequest):
    def __init__(self, missing_mandatory_fields):
        self.description = "Missing mandatory information: " + ",".join(missing_mandatory_fields)


class UnknownField(BadRequest):
    def __init__(self, field_name):
        self.description = "Unknown field: " + field_name


class IncorrectFieldType(BadRequest):
    def __init__(self, field_name):
        self.description = "Incorrect field type for field: " + field_name


class InvalidFieldValue(BadRequest):
    def __init__(self, field_name):
        self.description = "Invalid field value for field: " + field_name


class Unauthorized(ApiException):
    code = 401
    title = "Unauthorized"
    description = "You need to be authentificated to access resources"


class Forbidden(ApiException):
    code = 403
    title = "Forbidden"
    description = "You do not have the required permissions to access this resource"


class NotFound(ApiException):
    code = 404
    title = "Not Found"
    description = "Resource not found"


class InternalServerError(ApiException):
    code = 500
    title = "Internal Server Error"
    description = "An internal server error occurred"


class OsuError(InternalServerError):
    description = "Error connecting to osu! API, please retry later"


class DiscordError(InternalServerError):
    description = "Error connecting to Discord API, please retry later"
