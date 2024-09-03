use axum::response::Html;

pub async fn index() -> crate::prelude::Result<Html<String>> {
    Ok(Html(
        crate::TEMPLATES.render("index.html", &tera::Context::new())?,
    ))
}
