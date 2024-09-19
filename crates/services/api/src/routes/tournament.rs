use axum::extract::{Path, State};
use ormlite::model::*;

use crate::extractor::Json;
use crate::prelude::*;
use tosurnament_core::domain::tournament::*;

#[tracing::instrument(skip_all)]
pub async fn get_tournament(
    State(context): State<Context>,
    Path(id): Path<i32>,
) -> Result<Json<Tournament>> {
    let result = Tournament::fetch_one(id, &context.db.pool).await?;
    Ok(Json(result))
}
