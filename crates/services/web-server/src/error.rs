use axum::response::{IntoResponse, Response};
use tracing::error;

use crate::server_error::ServerError;

#[derive(thiserror::Error)]
pub enum Error {
    #[error(transparent)]
    ServerError(#[from] anyhow::Error),
    #[error(transparent)]
    DatabaseError(#[from] ormlite::Error),
    #[error(transparent)]
    InvalidHeader(#[from] axum::http::header::ToStrError),
    #[error("A header is not supported")]
    UnsupportedHeader,
    #[error(transparent)]
    DecodeError(#[from] DecodeError),
}

#[derive(Debug, thiserror::Error)]
pub enum DecodeError {
    #[error(transparent)]
    Json(#[from] axum::extract::rejection::JsonRejection),
    #[error(transparent)]
    Form(#[from] axum::extract::rejection::FormRejection),
}

impl std::fmt::Debug for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        error_chain_fmt(self, f)
    }
}

pub fn error_chain_fmt(
    e: &impl std::error::Error,
    f: &mut std::fmt::Formatter<'_>,
) -> std::fmt::Result {
    writeln!(f, "{}\n", e)?;
    let mut current = e.source();
    while let Some(cause) = current {
        writeln!(f, "Caused by:\n\t{}", cause)?;
        current = cause.source();
    }
    Ok(())
}

impl IntoResponse for Error {
    fn into_response(self) -> Response {
        let _error_details = self.to_string();
        error!(error = ?self);

        let server_error = match self {
            Self::ServerError(_) => ServerError::InternalServerError,
            Self::DatabaseError(error) => error.into_server_error(),
            Self::InvalidHeader(_) => ServerError::InvalidHeader,
            Self::UnsupportedHeader => ServerError::InvalidHeader,
            Self::DecodeError(error) => error.into_server_error(),
        };
        server_error.into_response()
    }
}

trait IntoServerError {
    fn into_server_error(&self) -> ServerError;
}

impl IntoServerError for ormlite::Error {
    fn into_server_error(&self) -> ServerError {
        match self {
            Self::SqlxError(error) => error.into_server_error(),
            _ => ServerError::InternalDatabaseError,
        }
    }
}

impl IntoServerError for ormlite::SqlxError {
    fn into_server_error(&self) -> ServerError {
        match self {
            Self::Database(error) => {
                if error.is_unique_violation() {
                    ServerError::DuplicateEntry
                } else {
                    ServerError::InternalDatabaseError
                }
            }
            _ => ServerError::InternalDatabaseError,
        }
    }
}

impl IntoServerError for DecodeError {
    fn into_server_error(&self) -> ServerError {
        match self {
            Self::Json(error) => error.into_server_error(),
            Self::Form(error) => error.into_server_error(),
        }
    }
}

impl IntoServerError for axum::extract::rejection::JsonRejection {
    fn into_server_error(&self) -> ServerError {
        match self {
            Self::JsonDataError(_) => ServerError::InvalidData,
            _ => ServerError::InvalidRequest,
        }
    }
}

impl IntoServerError for axum::extract::rejection::FormRejection {
    fn into_server_error(&self) -> ServerError {
        match self {
            Self::FailedToDeserializeForm(_) | Self::FailedToDeserializeFormBody(_) => {
                ServerError::InvalidData
            }
            _ => ServerError::InvalidRequest,
        }
    }
}
