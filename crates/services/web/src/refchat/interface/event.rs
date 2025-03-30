use secrecy::SecretString;
use serde::Deserialize;

use super::RefchatInterface;
use crate::refchat::{
    chat::{ChatCommand, ChatSender, SendAfterEffect},
    context::ChatMessage,
    error::RefchatError,
    ws_receiver::WsReceiver,
};

impl RefchatInterface {
    pub async fn listen(
        &self,
        ws_receiver: &mut WsReceiver,
        chat_sender: &ChatSender,
    ) -> Result<(), RefchatError> {
        loop {
            let event = self.next_event(ws_receiver).await?;
            match event {
                InterfaceEvent::NewMessage { text } => {
                    tracing::debug!("Received NewMessage event with: {text}");
                    self.reset_chat_input().await?;
                    self.send_text_to_chat(chat_sender, text).await?;
                }
                InterfaceEvent::SelectChannel { channel_name } => {
                    tracing::debug!("Received SelectChannel event with: {channel_name}");
                    self.select_channel(&channel_name).await?;
                }
                InterfaceEvent::NewChannelSelection {} => {
                    tracing::debug!("Received NewChannelSelection event");
                    self.show_new_channel_selection().await?;
                }
                InterfaceEvent::JoinChannel { channel_name } => {
                    tracing::debug!("Received JoinChannel event with: {channel_name}");
                    let command = format!("/join {}", channel_name);
                    self.send_text_to_chat(chat_sender, command).await?;
                }
                InterfaceEvent::QueryUser { user } => {
                    let command = format!("/query {}", user);
                    self.send_text_to_chat(chat_sender, command).await?;
                }
                InterfaceEvent::PartChannel { channel_name } => {
                    tracing::debug!("Received PartChannel event with: {channel_name}");
                    if !channel_name.is_empty() {
                        let command = format!("/part {}", channel_name);
                        self.send_text_to_chat(chat_sender, command).await?;
                    }
                }
                InterfaceEvent::ChangeChatInput { text } => {
                    tracing::debug!("Received ChangeChatInput event with: {text}");
                    self.refchat_context
                        .get_write_lock()
                        .await
                        .set_current_input(text);
                }
                InterfaceEvent::ShowPreviousHistoryMessage {} => {
                    tracing::debug!("Received NewChannelSelection event");
                    self.show_previous_history_message().await?;
                }
                InterfaceEvent::ShowNextHistoryMessage {} => {
                    tracing::debug!("Received NewChannelSelection event");
                    self.show_next_history_message().await?;
                }
                InterfaceEvent::SelectHelperTab { tab_name } => {
                    tracing::debug!("Received SelectHelperTab event with: {tab_name}");
                    self.select_helper_tab(&tab_name).await?;
                }
                InterfaceEvent::SyncRoom {} => {
                    tracing::debug!("Received SyncRoom event");
                    self.send_text_to_chat(chat_sender, "!mp settings".to_owned())
                        .await?;
                }
                InterfaceEvent::InvitePlayers {} => {
                    tracing::debug!("Received InvitePlayers event");
                    // TODO later when we have the info
                }
                InterfaceEvent::PickBanTimer {} => {
                    tracing::debug!("Received PickBanTimer event");
                    self.send_text_to_chat(chat_sender, "!mp timer 90".to_owned())
                        .await?;
                }
                InterfaceEvent::ReadyUpTimer {} => {
                    tracing::debug!("Received ReadyUpTimer event");
                    self.send_text_to_chat(chat_sender, "!mp timer 60".to_owned())
                        .await?;
                }
                InterfaceEvent::StartMatch {} => {
                    tracing::debug!("Received StartMatch event");
                    self.send_text_to_chat(chat_sender, "!mp start 5".to_owned())
                        .await?;
                }
                InterfaceEvent::Abort {} => {
                    tracing::debug!("Received Abort event");
                    self.send_text_to_chat(chat_sender, "!mp abort".to_owned())
                        .await?;
                }
                InterfaceEvent::Login { .. } => {
                    tracing::warn!("Received login event after being logged in");
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

    async fn send_text_to_chat(
        &self,
        chat_sender: &ChatSender,
        text: String,
    ) -> Result<(), RefchatError> {
        let command = chat_sender.parse_command_from_text(&text);
        match command {
            ChatCommand::Message { .. } => {
                if self.refchat_context.is_on_default_channel().await {
                    let message =
                        ChatMessage::new(None, "You are not in a channel.".to_string(), false);
                    self.add_message_to_default_channel(message).await?;
                    return Ok(());
                }
            }
            // If the channel is already present, switch to it
            ChatCommand::Query { ref channel_name } | ChatCommand::Join { ref channel_name } => {
                if self.refchat_context.has_channel(channel_name).await {
                    self.select_channel(channel_name).await?;
                    return Ok(());
                }
            }
            // If the channel is not present, do nothing
            // If the channel is not a room, just remove the display of the channel
            ChatCommand::Part { ref channel_name } => {
                if let Some(channel) = self
                    .refchat_context
                    .get_read_lock()
                    .await
                    .get_channel(channel_name)
                {
                    if !channel.is_room() {
                        self.remove_channel(channel_name).await?;
                        return Ok(());
                    }
                } else {
                    return Ok(());
                }
            }
            _ => (),
        }
        // For /query: no command must be sent in the chat, so we only display the channel
        if let ChatCommand::Query { ref channel_name } = command {
            self.add_channel(channel_name.clone()).await?;
        } else {
            match chat_sender
                .send_command(
                    self.refchat_context.get_current_channel_real_name().await,
                    command,
                )
                .await
            {
                Ok(after_effect) => match after_effect {
                    SendAfterEffect::MessageToDisplay { text } => {
                        let message = ChatMessage::new(
                            Some(self.refchat_context.get_username().to_owned()),
                            text,
                            true,
                        );
                        self.add_message_to_current_channel(message).await?;
                    }
                    SendAfterEffect::Error { text } => {
                        let message = ChatMessage::new(None, text, false);
                        self.add_message_to_current_channel(message).await?;
                    }
                    _ => (),
                },
                Err(error) => {
                    tracing::warn!("Could not send message in chat client: {}", error);
                }
            }
        }
        Ok(())
    }
}

#[derive(Deserialize)]
pub enum InterfaceEvent {
    Login {
        username: String,
        password: SecretString,
    },
    NewMessage {
        text: String,
    },
    SelectChannel {
        channel_name: String,
    },
    NewChannelSelection {},
    JoinChannel {
        channel_name: String,
    },
    QueryUser {
        user: String,
    },
    PartChannel {
        channel_name: String,
    },
    ChangeChatInput {
        text: String,
    },
    ShowPreviousHistoryMessage {},
    ShowNextHistoryMessage {},
    SelectHelperTab {
        tab_name: String,
    },
    SyncRoom {},
    InvitePlayers {},
    PickBanTimer {},
    ReadyUpTimer {},
    StartMatch {},
    Abort {},
}
