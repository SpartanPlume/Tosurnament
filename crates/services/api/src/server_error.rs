use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::Serialize;

#[derive(thiserror::Error, Debug)]
pub enum ServerError {
    #[error("An unexpected error occurred")]
    InternalServerError,
    #[error("An unexpected database error occurred")]
    InternalDatabaseError,
    #[error("Invalid header")]
    InvalidHeader,
    #[error("A duplicate entry already exists")]
    DuplicateEntry,
    #[error("Invalid request")]
    InvalidRequest,
    #[error("Invalid data")]
    InvalidData,
    #[error("Not found")]
    NotFoundError,
}

pub trait IntoServerError {
    fn into_server_error(self) -> ServerError;
}

#[derive(Serialize)]
struct ErrorResponse {
    message: String,
}

impl IntoResponse for ServerError {
    fn into_response(self) -> Response {
        let status_code = match self {
            Self::InternalServerError => StatusCode::INTERNAL_SERVER_ERROR,
            Self::InternalDatabaseError => StatusCode::INTERNAL_SERVER_ERROR,
            Self::InvalidHeader => StatusCode::BAD_REQUEST,
            Self::DuplicateEntry => StatusCode::CONFLICT,
            Self::InvalidRequest => StatusCode::BAD_REQUEST,
            Self::InvalidData => StatusCode::UNPROCESSABLE_ENTITY,
            Self::NotFoundError => StatusCode::NOT_FOUND,
        };
        (
            status_code,
            Json(ErrorResponse {
                message: self.to_string(),
            }),
        )
            .into_response()
    }
}
