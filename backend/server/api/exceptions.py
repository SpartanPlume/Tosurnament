from werkzeug.exceptions import HTTPException

ERRORS = {
    "OsuTokenError": {"message": "Authentification on osu! side failed", "status": 400},
    "OsuMeError": {"message": "Error while getting osu! profile information", "status": 400},
    "InternalServerError": {"message": "An internal server error occurred", "status": 500},
    "UserAlreadyVerified": {"message": "User is already verified", "status": 200},
}


class InternalServerError(HTTPException):
    pass


class OsuTokenError(HTTPException):
    pass


class OsuMeError(HTTPException):
    pass


class UserAlreadyVerified(HTTPException):
    pass
