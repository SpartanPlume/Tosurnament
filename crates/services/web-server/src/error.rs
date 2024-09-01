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
    DecodeError(#[from] axum::extract::rejection::JsonRejection),
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
            Self::SqlxError(sqlx_error) => sqlx_error.into_server_error(),
            _ => ServerError::InternalDatabaseError,
        }
    }
}

impl IntoServerError for ormlite::SqlxError {
    fn into_server_error(&self) -> ServerError {
        match self {
            Self::Database(database_error) => {
                if database_error.is_unique_violation() {
                    ServerError::DuplicateEntry
                } else {
                    ServerError::InternalDatabaseError
                }
            }
            _ => ServerError::InternalDatabaseError,
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
