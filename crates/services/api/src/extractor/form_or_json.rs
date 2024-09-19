use axum::{
    async_trait,
    extract::{FromRequest, Request},
};
use serde::de::DeserializeOwned;

use crate::error::{DecodeError, Error};

pub struct FormOrJson<T>(pub T);

#[async_trait]
impl<S, T> FromRequest<S> for FormOrJson<T>
where
    T: DeserializeOwned,
    S: Send + Sync,
{
    type Rejection = Error;

    async fn from_request(req: Request, state: &S) -> Result<Self, Self::Rejection> {
        let (parts, body) = req.into_parts();
        let req = Request::from_parts(parts, body);

        let content_type = req
            .headers()
            .get(axum::http::header::CONTENT_TYPE)
            .map(|value| value.to_str())
            .transpose()?;
        match content_type {
            Some("application/json") => match axum::Json::<T>::from_request(req, state).await {
                Ok(value) => Ok(Self(value.0)),
                Err(rejection) => Err(DecodeError::from(rejection).into()),
            },
            Some("application/x-www-form-urlencoded") => {
                match axum::Form::<T>::from_request(req, state).await {
                    Ok(value) => Ok(Self(value.0)),
                    Err(rejection) => Err(DecodeError::from(rejection).into()),
                }
            }
            _ => Err(Error::UnsupportedHeader),
        }
    }
}
