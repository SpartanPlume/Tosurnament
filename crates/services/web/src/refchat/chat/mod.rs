mod error;
mod event;
mod receiver;
mod sender;

use secrecy::{ExposeSecret, SecretString};

use super::{context::ChatMessage, interface::RefchatInterface};
use crate::config::RefchatConfig;
use error::ChatError;

pub use event::ChatEvent;
pub use receiver::ChatReceiver;
pub use sender::{ChatCommand, ChatSender, SendAfterEffect};

pub struct ChatClient {
    inner: irc::client::Client,
    receiver: ChatReceiver,
}

impl ChatClient {
    pub async fn try_new(
        config: &RefchatConfig,
        username: String,
        password: SecretString,
    ) -> Result<Self, ChatError> {
        let irc_config = irc::client::prelude::Config {
            nickname: Some(username.clone()),
            username: Some(username.clone()),
            password: Some(password.expose_secret().to_string()),
            server: Some(config.host.clone()),
            port: Some(config.port),
            use_tls: Some(false),
            channels: vec![],
            ..irc::client::prelude::Config::default()
        };
        let mut irc_client = irc::client::Client::from_config(irc_config).await?;
        irc_client.identify()?;

        let irc_receiver = ChatReceiver::new(irc_client.stream()?);

        Ok(Self {
            inner: irc_client,
            receiver: irc_receiver,
        })
    }

    pub fn get_username(&self) -> &str {
        self.inner.current_nickname()
    }

    pub async fn wait_until_ready(&mut self) -> Result<(), ChatError> {
        self.receiver.wait_until_ready().await
    }

    pub fn split(self) -> Result<(ChatSender, ChatReceiver), ChatError> {
        Ok((ChatSender::new(self.inner), self.receiver))
    }
}

pub async fn handle_chat(interface: RefchatInterface, chat_receiver: ChatReceiver) {
    if let Err(error) = do_chat_loop(interface, chat_receiver).await {
        error.trace();
    }
}

async fn do_chat_loop(
    interface: RefchatInterface,
    mut chat_receiver: ChatReceiver,
) -> Result<(), ChatError> {
    interface.show_channels().await?;
    loop {
        let event = chat_receiver.next_event().await?;
        match event {
            ChatEvent::Quit { username } => {
                if interface.get_username() == username {
                    tracing::info!("Quit refchat");
                    return Err(anyhow::Error::msg("IRC client disconnected").into());
                }
            }
            ChatEvent::Join {
                username,
                channel_name,
            } => {
                if interface.get_username() == username {
                    tracing::info!("Join channel {}", channel_name);
                    interface.add_channel(channel_name).await?;
                }
            }
            ChatEvent::Part {
                username,
                channel_name,
            } => {
                if interface.get_username() == username {
                    tracing::info!("Part channel {}", channel_name);
                    interface.remove_channel(&channel_name).await?;
                }
            }
            ChatEvent::Message {
                channel_name,
                username,
                text,
            } => {
                let message = ChatMessage::new(username, text, false);
                if let Some(channel_name) = channel_name {
                    interface.add_message(channel_name, message).await?;
                } else {
                    interface.add_message_to_default_channel(message).await?;
                }
            }
        }
    }
}
