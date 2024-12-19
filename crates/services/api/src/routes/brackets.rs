use axum::extract::{Path, State};
use axum::http::StatusCode;
use ormlite::model::*;

use tosurnament_core::domain::bracket::*;

use crate::extractor::{FormOrJson, Json};
use crate::prelude::*;

#[tracing::instrument(skip_all, fields(?body_data.name))]
pub async fn create_bracket(
    State(context): State<Context>,
    FormOrJson(body_data): FormOrJson<InsertBracket>,
) -> Result<(StatusCode, Json<Bracket>)> {
    let result = body_data.insert(&context.db.pool).await?;
    Ok((StatusCode::CREATED, Json(result)))
}

#[tracing::instrument(skip_all)]
pub async fn get_brackets(State(context): State<Context>) -> Result<Json<Vec<Bracket>>> {
    let results = Bracket::select().fetch_all(&context.db.pool).await?;
    Ok(Json(results))
}

#[tracing::instrument(skip_all)]
pub async fn get_bracket(
    State(context): State<Context>,
    Path(id): Path<i32>,
) -> Result<Json<Bracket>> {
    let result = Bracket::fetch_one(id, &context.db.pool).await?;
    Ok(Json(result))
}
