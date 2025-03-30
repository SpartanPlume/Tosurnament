use futures::prelude::*;
use irc::proto::{Command, Message, Response};

use super::{error::ChatError, event::ChatEvent};

pub struct ChatReceiver(irc::client::ClientStream);

impl ChatReceiver {
    pub fn new(inner: irc::client::ClientStream) -> Self {
        Self(inner)
    }

    async fn next(&mut self) -> Result<irc::client::prelude::Message, ChatError> {
        if let Some(message) = self.0.next().await {
            match message {
                Ok(message) => {
                    return Ok(message);
                }
                Err(error) => {
                    return Err(anyhow::Error::msg(format!(
                        "Error received from IRC client: {}",
                        error
                    ))
                    .into());
                }
            }
        }
        Err(anyhow::Error::msg("IRC client disconnected").into())
    }

    pub async fn next_event(&mut self) -> Result<ChatEvent, ChatError> {
        loop {
            let irc_message = self.next().await?;
            if let Some(event) = Self::transform_command_to_event(irc_message) {
                return Ok(event);
            }
        }
    }

    fn transform_command_to_event(irc_message: Message) -> Option<ChatEvent> {
        match irc_message.command {
            Command::QUIT(_) | Command::SQUIT(_, _) => {
                if let Some(username) = irc_message.source_nickname() {
                    tracing::debug!("Received QUIT command (from {username})");
                    return Some(ChatEvent::Quit {
                        username: username.to_owned(),
                    });
                }
            }
            Command::JOIN(ref channel_name, _, _) => {
                if let Some(username) = irc_message.source_nickname() {
                    tracing::debug!("Received JOIN command (from {username}) with: {channel_name}");
                    return Some(ChatEvent::Join {
                        username: username.to_owned(),
                        channel_name: channel_name.clone(),
                    });
                }
            }
            Command::PART(ref channel_name, _) => {
                if let Some(username) = irc_message.source_nickname() {
                    tracing::debug!("Received PART command (from {username}) with: {channel_name}");
                    return Some(ChatEvent::Part {
                        username: username.to_owned(),
                        channel_name: channel_name.clone(),
                    });
                }
            }
            Command::PRIVMSG(_, ref text) | Command::NOTICE(_, ref text) => {
                if let Some(channel_name) = irc_message.response_target() {
                    if let Some(username) = irc_message.source_nickname() {
                        tracing::debug!("Received PRIVMSG command (from {channel_name}/{username}) with: {text}");
                        return Some(ChatEvent::Message {
                            channel_name: Some(channel_name.to_owned()),
                            username: Some(username.to_owned()),
                            text: text.to_owned(),
                        });
                    }
                }
            }
            Command::PING(_server1, _server2) => {
                // Reply is automatic
            }
            Command::PONG(_server1, _server2) => {
                // No need to process
            }
            Command::ERROR(error) => {
                tracing::info!("IRC error: {}", error);
            }
            Command::Response(response_type, args) => match response_type {
                Response::ERR_NOSUCHNICK => {
                    tracing::debug!("Received ERR_NOSUCHNICK command");
                    let channel_name = if args.len() >= 2 {
                        Some(args[1].clone())
                    } else {
                        None
                    };
                    return Some(ChatEvent::Message {
                        channel_name,
                        username: None,
                        text: "This user is not connected or does not exist.".to_string(),
                    });
                }
                _ => {
                    tracing::info!(
                        "Received Response command of type {:?} with args {:?}",
                        response_type,
                        args
                    );
                }
            },
            other => {
                tracing::info!("Received command {:?}", other);
            }
        }
        None
    }

    pub async fn wait_until_ready(&mut self) -> Result<(), ChatError> {
        loop {
            let irc_message = self.next().await?;
            if let Command::Response(Response::RPL_ENDOFMOTD | Response::ERR_NOMOTD, _) =
                irc_message.command
            {
                return Ok(());
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use irc::proto::Message;

    use super::ChatEvent;
    use super::ChatReceiver;

    #[test]
    fn quit_command_is_transformed_into_quit_event() {
        let message = Message::new(Some("nickname!username@hostname"), "QUIT", vec![])
            .expect("Could not create IRC message");
        let event = ChatReceiver::transform_command_to_event(message);
        assert!(event.is_some());
        let event = event.unwrap();
        assert_eq!(
            ChatEvent::Quit {
                username: "nickname".to_string(),
            },
            event
        );
    }

    #[test]
    fn join_command_is_transformed_into_join_event() {
        let message = Message::new(Some("nickname!username@hostname"), "JOIN", vec!["#channel"])
            .expect("Could not create IRC message");
        let event = ChatReceiver::transform_command_to_event(message);
        assert!(event.is_some());
        let event = event.unwrap();
        assert_eq!(
            ChatEvent::Join {
                username: "nickname".to_string(),
                channel_name: "#channel".to_string()
            },
            event
        );
    }

    #[test]
    fn part_command_is_transformed_into_part_event() {
        let message = Message::new(Some("nickname!username@hostname"), "PART", vec!["#channel"])
            .expect("Could not create IRC message");
        let event = ChatReceiver::transform_command_to_event(message);
        assert!(event.is_some());
        let event = event.unwrap();
        assert_eq!(
            ChatEvent::Part {
                username: "nickname".to_string(),
                channel_name: "#channel".to_string()
            },
            event
        );
    }

    #[test]
    fn privmsg_command_is_transformed_into_message_event() {
        let message = Message::new(
            Some("nickname!username@hostname"),
            "PRIVMSG",
            vec!["target", "message"],
        )
        .expect("Could not create IRC message");
        let event = ChatReceiver::transform_command_to_event(message);
        assert!(event.is_some());
        let event = event.unwrap();
        assert_eq!(
            ChatEvent::Message {
                channel_name: Some("nickname".to_string()),
                username: Some("nickname".to_string()),
                text: "message".to_string(),
            },
            event
        );
    }

    #[test]
    fn invalid_privmsg_command_is_ignored() {
        let message = Message::new(None, "PRIVMSG", vec!["target", "message"])
            .expect("Could not create IRC message");
        let event = ChatReceiver::transform_command_to_event(message);
        assert!(event.is_none());
    }
}
