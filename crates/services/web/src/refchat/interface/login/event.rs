use super::RefchatLoginInterface;
use crate::refchat::{
    chat::ChatClient, error::RefchatError, interface::event::InterfaceEvent,
    ws_receiver::WsReceiver,
};

impl RefchatLoginInterface {
    pub async fn listen(
        &mut self,
        ws_receiver: &mut WsReceiver,
    ) -> Result<ChatClient, RefchatError> {
        loop {
            let event = self.next_event(ws_receiver).await?;
            match event {
                InterfaceEvent::Login { username, password } => {
                    match self.wait_for_login(username, password).await {
                        Ok(chat_client) => return Ok(chat_client),
                        Err(error) => error.trace(),
                    }
                }
                _ => {
                    tracing::warn!("Received another event than login");
                }
            }
        }
    }

    async fn next_event(
        &self,
        ws_receiver: &mut WsReceiver,
    ) -> Result<InterfaceEvent, RefchatError> {
        loop {
            let json_value = ws_receiver.next().await?;
            if let Some(event_type) = json_value["event_type"].as_str() {
                let mut json_event = serde_json::Map::new();
                json_event.insert(event_type.to_string(), json_value);
                let event = serde_json::from_value::<InterfaceEvent>(json_event.into())?;
                return Ok(event);
            }
        }
    }
}
