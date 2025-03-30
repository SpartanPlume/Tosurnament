use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
};

#[derive(thiserror::Error)]
pub enum Error {
    #[error(transparent)]
    Server(#[from] anyhow::Error),
    #[error(transparent)]
    InvalidHeader(#[from] axum::http::header::ToStrError),
    #[error("A header is not supported")]
    UnsupportedHeader,
    #[error(transparent)]
    Decode(#[from] DecodeError),
    #[error(transparent)]
    Tera(#[from] tera::Error),
    #[error(transparent)]
    Reqwest(#[from] reqwest::Error),
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
        tracing::error!(error = ?self);

        let status_code = match self {
            Self::Server(_) => StatusCode::INTERNAL_SERVER_ERROR,
            Self::InvalidHeader(_) => StatusCode::BAD_REQUEST,
            Self::UnsupportedHeader => StatusCode::BAD_REQUEST,
            Self::Decode(error) => error.into_status_code(),
            Self::Tera(_) => StatusCode::INTERNAL_SERVER_ERROR,
            Self::Reqwest(_) => StatusCode::INTERNAL_SERVER_ERROR,
        };
        status_code.into_response()
    }
}

trait IntoStatusCode {
    fn into_status_code(self) -> StatusCode;
}

impl IntoStatusCode for DecodeError {
    fn into_status_code(self) -> StatusCode {
        match self {
            Self::Json(error) => error.into_status_code(),
            Self::Form(error) => error.into_status_code(),
        }
    }
}

impl IntoStatusCode for axum::extract::rejection::JsonRejection {
    fn into_status_code(self) -> StatusCode {
        match self {
            Self::JsonDataError(_) => StatusCode::UNPROCESSABLE_ENTITY,
            _ => StatusCode::BAD_REQUEST,
        }
    }
}

impl IntoStatusCode for axum::extract::rejection::FormRejection {
    fn into_status_code(self) -> StatusCode {
        match self {
            Self::FailedToDeserializeForm(_) | Self::FailedToDeserializeFormBody(_) => {
                StatusCode::UNPROCESSABLE_ENTITY
            }
            _ => StatusCode::BAD_REQUEST,
        }
    }
}
