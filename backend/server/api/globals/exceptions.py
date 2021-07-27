from werkzeug.exceptions import HTTPException


class BadRequest(HTTPException):
    code = 400
    title = "Bad Request"
    description = "Bad Request"


class UserAlreadyVerified(BadRequest):
    description = "User is already verified"


class CannotRemoveLastBracket(BadRequest):
    description = "Cannot remove the last bracket of a tournament"


class MissingRequiredInformation(BadRequest):
    description = "This request is missing mandatory information"


class Unauthorized(HTTPException):
    code = 401
    title = "Unauthorized"
    description = "You need to be authentificated to access resources"


class Forbidden(HTTPException):
    code = 403
    title = "Forbidden"
    description = "You do not have the required permissions to access this resource"


class NotFound(HTTPException):
    code = 404
    title = "Not Found"
    description = "The requested resource has not been found"


class InternalServerError(HTTPException):
    code = 500
    title = "Internal Server Error"
    description = "An internal server error occurred"


class OsuTokenError(InternalServerError):
    description = "Authentification on osu! side failed"


class OsuMeError(InternalServerError):
    description = "Error getting osu! profile information"


class DiscordTokenError(InternalServerError):
    description = "Authentification on discord side failed"


class DiscordMeError(InternalServerError):
    description = "Error getting discord user information"


class DiscordGetError(InternalServerError):
    description = "Couldn't get the data from Discord API"
