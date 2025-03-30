use axum::extract::ws::WebSocketUpgrade;
use axum::extract::State;
use axum::response::IntoResponse;

use crate::extractor::TeraContext;
use crate::prelude::*;
use crate::refchat::handle_socket;

#[tracing::instrument(skip_all)]
pub async fn handle_refchat_ws(
    State(context): State<WebContext>,
    ws: WebSocketUpgrade,
    TeraContext(tera_context): TeraContext,
) -> impl IntoResponse {
    ws.on_upgrade(move |socket| handle_socket(socket, tera_context, context.refchat))
}
