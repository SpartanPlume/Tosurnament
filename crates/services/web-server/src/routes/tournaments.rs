use axum::extract::{Path, State};
use axum::http::StatusCode;
use axum::response::Html;
use ormlite::model::*;

use crate::extractor::{FormOrJson, Json};
use crate::prelude::*;
use crate::TEMPLATES;
use tosurnament_core::domain::tournament::*;

#[tracing::instrument(skip_all, fields(?body_data.name))]
pub async fn create_tournament(
    State(context): State<Context>,
    FormOrJson(body_data): FormOrJson<InsertTournament>,
) -> Result<(StatusCode, Json<Tournament>)> {
    let result = body_data.insert(&context.db.pool).await?;
    Ok((StatusCode::CREATED, Json(result)))
}

#[tracing::instrument(skip_all)]
pub async fn get_tournaments(State(context): State<Context>) -> Result<Json<Vec<Tournament>>> {
    let results = Tournament::select().fetch_all(&context.db.pool).await?;
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

#[tracing::instrument(skip_all)]
pub async fn show_tournaments(State(context): State<Context>) -> Result<Html<String>> {
    let results = Tournament::select().fetch_all(&context.db.pool).await?;
    let mut tera_context = tera::Context::new();
    tera_context.insert("tournaments", &results);
    Ok(Html(TEMPLATES.render("tournaments.html", &tera_context)?))
}

#[tracing::instrument(skip_all)]
pub async fn show_tournament(
    State(context): State<Context>,
    Path(id): Path<i32>,
) -> Result<Html<String>> {
    let result = Tournament::fetch_one(id, &context.db.pool).await?;
    Ok(Html(TEMPLATES.render(
        "tournament.html",
        &tera::Context::from_serialize(result)?,
    )?))
}
