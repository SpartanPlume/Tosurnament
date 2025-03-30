mod display;
mod event;

use secrecy::SecretString;

use crate::{
    config::RefchatConfig,
    refchat::{ChatClient, RefchatError, WsSender},
};
use display::RefchatLoginDisplay;

#[derive(Clone)]
pub struct RefchatLoginInterface {
    display: RefchatLoginDisplay,
    chat_config: RefchatConfig,
    username: String,
}

impl RefchatLoginInterface {
    pub fn new(
        ws_sender: WsSender,
        chat_config: RefchatConfig,
        username: String,
        tera_context: tera::Context,
    ) -> Self {
        Self {
            display: RefchatLoginDisplay::new(ws_sender, tera_context),
            chat_config,
            username,
        }
    }

    pub async fn reset_display(&self) -> Result<(), RefchatError> {
        self.display.reset(&self.username).await
    }

    async fn wait_for_login(
        &mut self,
        username: String,
        password: SecretString,
    ) -> Result<ChatClient, RefchatError> {
        self.username = username;
        if self.username.is_empty() {
            return Err(self.display.show_login_error().await);
        }
        self.display.show_login_wait().await?;
        match ChatClient::try_new(&self.chat_config, self.username.clone(), password).await {
            Ok(mut chat_client) => {
                if chat_client.wait_until_ready().await.is_ok() {
                    return Ok(chat_client);
                }
            }
            Err(error) => {
                error.trace();
            }
        };
        Err(self.display.show_login_error().await)
    }
}
