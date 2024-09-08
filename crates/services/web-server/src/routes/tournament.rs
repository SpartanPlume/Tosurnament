use axum::extract::{Path, State};
use axum::response::Html;
use ormlite::model::*;

use crate::extractor::{Json, TeraContext};
use crate::prelude::*;
use crate::TEMPLATES;
use tosurnament_core::domain::tournament::*;

#[tracing::instrument(skip_all)]
pub async fn get_tournament(
    State(context): State<Context>,
    Path(id): Path<i32>,
) -> Result<Json<Tournament>> {
    let result = Tournament::fetch_one(id, &context.db.pool).await?;
    Ok(Json(result))
}

#[tracing::instrument(skip_all)]
pub async fn show_tournament(
    State(context): State<Context>,
    TeraContext(mut tera_context): TeraContext,
    Path(id): Path<i32>,
) -> Result<Html<String>> {
    let result = Tournament::fetch_one(id, &context.db.pool).await?;
    tera_context.insert("tournament", &result);
    Ok(Html(TEMPLATES.render("tournament.html", &tera_context)?))
}
