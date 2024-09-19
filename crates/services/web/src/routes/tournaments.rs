use axum::extract::State;
use axum::response::Html;

use crate::extractor::TeraContext;
use crate::prelude::*;
use crate::TEMPLATES;
use tosurnament_core::domain::tournament::*;

#[tracing::instrument(skip_all)]
pub async fn show_tournaments(
    State(context): State<Context>,
    TeraContext(mut tera_context): TeraContext,
) -> Result<Html<String>> {
    let results: Vec<Tournament> = reqwest::get(context.api.build_uri("/tournaments"))
        .await?
        .json()
        .await?;
    tera_context.insert("tournaments", &results);
    Ok(Html(TEMPLATES.render("tournaments.html", &tera_context)?))
}
