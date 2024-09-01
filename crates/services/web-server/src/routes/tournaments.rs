use axum::extract::State;
use axum::http::StatusCode;
use axum::Json;

use crate::prelude::*;
use tosurnament_core::domain::tournament::*;

use ormlite::model::*;

#[tracing::instrument(skip_all, fields(?body_data.name))]
pub async fn create_tournament(
    State(context): State<Context>,
    Json(body_data): Json<InsertTournament>,
) -> Result<(StatusCode, Json<Tournament>)> {
    let result = body_data.insert(&context.db.pool).await?;
    Ok((StatusCode::CREATED, Json(result)))
}

#[tracing::instrument(skip_all)]
pub async fn get_tournaments(State(context): State<Context>) -> Result<Json<Vec<Tournament>>> {
    let results = Tournament::select().fetch_all(&context.db.pool).await?;
    Ok(Json(results))
}
