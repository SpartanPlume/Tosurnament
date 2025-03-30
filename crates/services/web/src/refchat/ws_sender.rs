use anyhow::Context;
use axum::extract::ws::{self as axum_ws, WebSocket};
use futures::{sink::SinkExt, stream::SplitSink};
use std::sync::Arc;
use tokio::sync::RwLock;

use super::error::RefchatError;
use crate::TEMPLATES;

#[derive(Clone, Debug)]
pub struct WsSender(Arc<RwLock<SplitSink<WebSocket, axum_ws::Message>>>);

impl WsSender {
    pub fn new(inner: SplitSink<WebSocket, axum_ws::Message>) -> Self {
        Self(Arc::new(RwLock::new(inner)))
    }

    pub async fn send_html(
        &self,
        template_page: &str,
        tera_context: &tera::Context,
    ) -> Result<(), RefchatError> {
        let page = TEMPLATES.render(template_page, tera_context)?;
        tracing::debug!("Sending page {template_page}");
        // TODO: remove whitespaces in html
        self.send_text(page).await
    }

    pub async fn send_text(&self, text: String) -> Result<(), RefchatError> {
        self.0
            .write()
            .await
            .send(axum_ws::Message::Text(text.into()))
            .await
            .context("Client disconnected: could not send message")?;
        Ok(())
    }
}

impl From<SplitSink<WebSocket, axum_ws::Message>> for WsSender {
    fn from(sink: SplitSink<WebSocket, axum_ws::Message>) -> Self {
        Self::new(sink)
    }
}
