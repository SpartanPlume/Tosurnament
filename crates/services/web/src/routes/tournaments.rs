use anyhow::Context;
use axum::extract::{Query, State};
use axum::response::Html;

use crate::extractor::TeraContext;
use crate::prelude::*;
use crate::routes::Pagination;
use crate::TEMPLATES;
use tosurnament_core::domain::tournament::*;

#[tracing::instrument(skip_all)]
pub async fn show_more_tournaments(
    State(context): State<WebContext>,
    TeraContext(mut tera_context): TeraContext,
    Query(mut pagination): Query<Pagination>,
) -> Result<Html<String>> {
    if pagination.page.is_none() {
        pagination.page = Some(1);
    }
    let mut url_parameters =
        serde_qs::to_string(&pagination).context("Could not transform pagination to string")?;
    if !url_parameters.is_empty() {
        url_parameters = format!("?{}", url_parameters);
    }
    let results: Vec<Tournament> = reqwest::get(
        context
            .api
            .build_uri(&format!("/tournaments{}", url_parameters)),
    )
    .await?
    .json()
    .await?;
    tera_context.insert("tournaments", &results);
    let new_page = pagination.page.context("Missing page in pagination")? + 1;
    tera_context.insert("new_page", &new_page);
    Ok(Html(
        TEMPLATES.render("tournaments_panels.html", &tera_context)?,
    ))
}
