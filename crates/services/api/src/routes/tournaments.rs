use axum::extract::{Path, Query, State};
use axum::http::StatusCode;
use ormlite::model::*;

use tosurnament_core::domain::tournament::*;

use crate::extractor::{FormOrJson, Json};
use crate::prelude::*;
use crate::routes::Pagination;

#[tracing::instrument(skip_all, fields(?body_data.name))]
pub async fn create_tournament(
    State(context): State<Context>,
    FormOrJson(body_data): FormOrJson<InsertTournament>,
) -> Result<(StatusCode, Json<Tournament>)> {
    let result = body_data.insert(&context.db.pool).await?;
    Ok((StatusCode::CREATED, Json(result)))
}

#[tracing::instrument(skip_all)]
pub async fn get_tournaments(
    State(context): State<Context>,
    Query(pagination): Query<Pagination>,
) -> Result<Json<Vec<Tournament>>> {
    let mut query_builder = Tournament::select();
    if pagination.per_page.is_some() {
        let per_page = pagination.per_page.unwrap();
        query_builder = query_builder.limit(per_page);
        if pagination.page.is_some() {
            let page = pagination.page.unwrap().saturating_sub(1);
            query_builder = query_builder.offset(page * per_page);
        }
    }
    let results = query_builder.fetch_all(&context.db.pool).await?;
    Ok(Json(results))
}

#[tracing::instrument(skip_all)]
pub async fn get_tournament(
    State(context): State<Context>,
    Path(id): Path<i32>,
) -> Result<Json<Tournament>> {
    let result = Tournament::fetch_one(id, &context.db.pool).await?;
    Ok(Json(result))
}
