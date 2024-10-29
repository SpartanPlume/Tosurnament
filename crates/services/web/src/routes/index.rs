use axum::response::Html;

use crate::extractor::TeraContext;
use crate::prelude::*;
use crate::TEMPLATES;

#[tracing::instrument(skip_all)]
pub async fn index(TeraContext(tera_context): TeraContext) -> Result<Html<String>> {
    Ok(Html(TEMPLATES.render("index.html", &tera_context)?))
}
