use axum::{
    async_trait,
    extract::{Extension, FromRequestParts},
    http::request::Parts,
};
use std::convert::Infallible;

#[derive(Debug, Clone)]
pub struct TeraContext(pub tera::Context);

#[async_trait]
impl<S> FromRequestParts<S> for TeraContext
where
    S: Send + Sync,
{
    type Rejection = Infallible;

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        let tera_context = Extension::<Self>::from_request_parts(parts, state)
            .await
            .unwrap_or_else(|_| {
                let mut tera_context = tera::Context::new();
                tera_context.insert("uri", &parts.uri.to_string());
                Extension(TeraContext(tera_context))
            })
            .0;

        Ok(tera_context)
    }
}
