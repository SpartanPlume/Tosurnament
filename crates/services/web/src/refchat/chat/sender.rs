use super::error::ChatError;

pub struct ChatSender {
    inner: irc::client::Client,
}

impl ChatSender {
    pub fn new(inner: irc::client::Client) -> Self {
        Self { inner }
    }

    pub fn get_username(&self) -> &str {
        self.inner.current_nickname()
    }

    pub async fn send_command(
        &self,
        channel_name: String,
        command: ChatCommand,
    ) -> Result<SendAfterEffect, ChatError> {
        match command {
            ChatCommand::Message { text } => {
                if !text.is_empty() {
                    self.inner.send_privmsg(channel_name, text.clone())?;
                    return Ok(SendAfterEffect::MessageToDisplay { text });
                }
            }
            ChatCommand::Join { channel_name } => {
                self.inner.send_join(channel_name)?;
            }
            ChatCommand::Query { .. } => (),
            ChatCommand::Part { channel_name } => {
                self.inner.send_part(channel_name)?;
            }
            ChatCommand::Quit {} => {
                self.inner.send_quit("")?;
            }
            ChatCommand::Invalid { command } => {
                return Ok(SendAfterEffect::Error {
                    text: format!("Invalid command: {}", command.as_str()),
                });
            }
        }
        Ok(SendAfterEffect::None)
    }

    pub fn parse_command_from_text(&self, text: &str) -> ChatCommand {
        let query_regex = regex::Regex::new(r"(?i)^/query\s+([^\s]+)").expect("Invalid regex"); // TODO: add test to check regex
        if let Some(query_captures) = query_regex.captures(text) {
            if let Some(query_channel) = query_captures.get(1) {
                return ChatCommand::Query {
                    channel_name: query_channel.as_str().to_string(),
                };
            }
        }
        let join_regex = regex::Regex::new(r"(?i)^/join\s+([^\s]+)").expect("Invalid regex"); // TODO: add test to check regex
        if let Some(join_captures) = join_regex.captures(text) {
            if let Some(join_channel) = join_captures.get(1) {
                let mut join_channel = join_channel.as_str().to_string();
                if !join_channel.starts_with('#') {
                    join_channel = format!("#{}", join_channel);
                }
                return ChatCommand::Join {
                    channel_name: join_channel,
                };
            }
        }
        let part_regex = regex::Regex::new(r"(?i)^/part\s+([^\s]+)").expect("Invalid regex");
        if let Some(part_captures) = part_regex.captures(text) {
            if let Some(part_channel) = part_captures.get(1) {
                return ChatCommand::Part {
                    channel_name: part_channel.as_str().to_string(),
                };
            }
        }
        let quit_regex = regex::Regex::new(r"(?i)^/quit\s+").expect("Invalid regex");
        if quit_regex.is_match(text) {
            return ChatCommand::Quit {};
        }
        let starts_with_slash_regex = regex::Regex::new(r"(?i)^/([^\s]*)").expect("Invalid regex");
        if let Some(slash_captures) = starts_with_slash_regex.captures(text) {
            if let Some(command) = slash_captures.get(1) {
                return ChatCommand::Invalid {
                    command: command.as_str().to_string(),
                };
            }
        }
        ChatCommand::Message {
            text: text.to_owned(),
        }
    }
}

pub enum ChatCommand {
    Message { text: String },
    Join { channel_name: String },
    Query { channel_name: String },
    Part { channel_name: String },
    Invalid { command: String },
    Quit {},
}

pub enum SendAfterEffect {
    None,
    Error { text: String },
    MessageToDisplay { text: String },
}
