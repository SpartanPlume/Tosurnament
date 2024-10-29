use axum::extract::{Path, State};
use axum::response::Html;

use crate::extractor::TeraContext;
use crate::prelude::*;
use crate::TEMPLATES;
use tosurnament_core::domain::tournament::*;

#[tracing::instrument(skip_all)]
pub async fn show_tournament(
    State(context): State<WebContext>,
    TeraContext(mut tera_context): TeraContext,
    Path(id): Path<i32>,
) -> Result<Html<String>> {
    let path = format!("/tournaments/{}", id);
    let result: Tournament = reqwest::get(context.api.build_uri(&path))
        .await?
        .json()
        .await?;
    tera_context.insert("tournament", &result);
    Ok(Html(TEMPLATES.render("tournament.html", &tera_context)?))
}
