use axum::response::Html;

use crate::extractor::TeraContext;
use crate::prelude::*;
use crate::TEMPLATES;

#[tracing::instrument(skip_all)]
pub async fn show_refchat(TeraContext(tera_context): TeraContext) -> Result<Html<String>> {
    Ok(Html(TEMPLATES.render("refchat/index.html", &tera_context)?))
}
