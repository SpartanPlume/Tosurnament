use axum::extract::ws::{self as axum_ws, WebSocket};
use futures::stream::{SplitStream, StreamExt};

use super::error::RefchatError;

pub struct WsReceiver(SplitStream<WebSocket>);

impl WsReceiver {
    pub fn new(inner: SplitStream<WebSocket>) -> Self {
        Self(inner)
    }

    pub async fn next(&mut self) -> Result<serde_json::Value, RefchatError> {
        while let Some(msg) = self.0.next().await {
            if let Ok(msg) = msg {
                match msg {
                    axum_ws::Message::Text(t) => {
                        let json_value = serde_json::from_str::<serde_json::Value>(&t)?;
                        return Ok(json_value);
                    }
                    axum_ws::Message::Binary(b) => {
                        let json_value = serde_json::from_slice::<serde_json::Value>(&b)?;
                        return Ok(json_value);
                    }
                    axum_ws::Message::Close(_) => {
                        // Not a real error, but it simplifies the disconnection handling
                        return Err(anyhow::Error::msg("Client disconnected").into());
                    }
                    _ => (),
                };
            } else {
                return Err(anyhow::Error::msg("Server disconnected abruptly").into());
            }
        }
        Err(anyhow::Error::msg("Client disconnected abruptly++").into())
    }
}

impl From<SplitStream<WebSocket>> for WsReceiver {
    fn from(stream: SplitStream<WebSocket>) -> Self {
        Self::new(stream)
    }
}
