mod display;
mod event;
pub mod login;

use super::{
    context::{Channel, ChannelUpdateType, ChatMessage, RefchatContext},
    error::RefchatError,
    WsSender,
};
use display::RefchatDisplay;

#[derive(Clone, Debug)]
pub struct RefchatInterface {
    display: RefchatDisplay,
    refchat_context: RefchatContext,
}

impl RefchatInterface {
    pub fn new(ws_sender: WsSender, username: String, tera_context: tera::Context) -> Self {
        Self {
            display: RefchatDisplay::new(ws_sender, tera_context),
            refchat_context: RefchatContext::new(username),
        }
    }

    pub fn get_username(&self) -> &str {
        self.refchat_context.get_username()
    }

    pub async fn reset_display(&self) -> Result<(), RefchatError> {
        self.display.reset().await
    }

    pub async fn show_channels(&self) -> Result<(), RefchatError> {
        let context_lock = self.refchat_context.get_read_lock().await;
        self.display
            .show_channels(
                context_lock.get_channels(),
                context_lock.get_current_channel().get_real_name(),
            )
            .await?;
        Ok(())
    }

    pub async fn select_channel(&self, channel_name: &str) -> Result<(), RefchatError> {
        let mut context_lock = self.refchat_context.get_write_lock().await;
        let current_channel = context_lock.get_current_channel();
        if !context_lock.is_on_new_channel_selection()
            && current_channel.is_name_matching(channel_name)
        {
            // It is already the correct channel, no need to update
            return Ok(());
        }
        let previous_channel = if context_lock.is_on_new_channel_selection() {
            None
        } else {
            Some(current_channel)
        };
        if let Some(selected_channel) = context_lock.get_channel(channel_name) {
            self.display
                .select_channel(selected_channel, &previous_channel)
                .await?;
            context_lock.set_current_channel(channel_name);
        } else {
            tracing::warn!("Trying to select an unexisting channel");
        }
        Ok(())
    }

    pub async fn add_channel(&self, channel_name: String) -> Result<(), RefchatError> {
        let mut context_lock = self.refchat_context.get_write_lock().await;
        if context_lock.add_channel(channel_name.clone()).is_none() {
            // This channel is already present
            return Ok(());
        }
        if let Some(added_channel) = context_lock.get_channel(&channel_name) {
            let previous_channel = if context_lock.is_on_new_channel_selection() {
                None
            } else {
                Some(context_lock.get_current_channel())
            };
            self.display
                .add_channel(added_channel, &previous_channel)
                .await?;
        } else {
            tracing::error!("Added channel has not been found");
            return Ok(());
        }
        context_lock.set_current_channel(&channel_name);
        Ok(())
    }

    pub async fn remove_channel(&self, channel_name: &str) -> Result<(), RefchatError> {
        let mut context_lock = self.refchat_context.get_write_lock().await;
        if !context_lock.remove_channel(channel_name) {
            // This channel did not exist
            return Ok(());
        }
        let current_channel = context_lock.get_current_channel();
        self.display
            .show_channels(context_lock.get_channels(), current_channel.get_real_name())
            .await?;
        self.display.select_channel(current_channel, &None).await?;
        Ok(())
    }

    pub async fn show_new_channel_selection(&self) -> Result<(), RefchatError> {
        let mut context_lock = self.refchat_context.get_write_lock().await;
        if context_lock.is_on_new_channel_selection() {
            // It is already the correct view, no need to update
            return Ok(());
        }
        self.display
            .show_new_channel_selection(context_lock.get_current_channel())
            .await?;
        context_lock.set_is_on_new_channel_selection(true);
        Ok(())
    }

    pub async fn reset_chat_input(&self) -> Result<(), RefchatError> {
        let mut context_lock = self.refchat_context.get_write_lock().await;
        context_lock.set_current_input(String::new());
        self.display.change_chat_input("").await
    }

    pub async fn add_message(
        &self,
        channel_name: String,
        message: ChatMessage,
    ) -> Result<(), RefchatError> {
        let mut context_lock = self.refchat_context.get_write_lock().await;
        let is_new_channel = !context_lock.has_channel(&channel_name);
        let updates = context_lock.add_message(channel_name.clone(), message.clone());
        let current_channel = context_lock.get_current_channel();
        if current_channel.is_name_matching(&channel_name) {
            self.handle_channel_updates(current_channel, &message, &updates)
                .await?;
        } else if is_new_channel {
            self.display
                .show_channels(context_lock.get_channels(), current_channel.get_real_name())
                .await?;
        }
        Ok(())
    }

    pub async fn add_message_to_current_channel(
        &self,
        message: ChatMessage,
    ) -> Result<(), RefchatError> {
        let mut context_lock = self.refchat_context.get_write_lock().await;
        let updates = context_lock.add_message_to_current_channel(message.clone());
        let current_channel = context_lock.get_current_channel();
        self.handle_channel_updates(current_channel, &message, &updates)
            .await?;
        Ok(())
    }

    pub async fn add_message_to_default_channel(
        &self,
        message: ChatMessage,
    ) -> Result<(), RefchatError> {
        let mut context_lock = self.refchat_context.get_write_lock().await;
        let updates = context_lock.add_message_to_default_channel(message.clone());
        let current_channel = context_lock.get_current_channel();
        if current_channel.is_default() {
            self.handle_channel_updates(current_channel, &message, &updates)
                .await?;
        }
        Ok(())
    }

    async fn handle_channel_updates(
        &self,
        current_channel: &Channel,
        message: &ChatMessage,
        updates: &Vec<ChannelUpdateType>,
    ) -> Result<(), RefchatError> {
        for update in updates {
            match update {
                ChannelUpdateType::AddMessage => self.display.add_message(message).await?,
                ChannelUpdateType::UpdateTab => {
                    if let Some(tab) = current_channel.get_current_tab() {
                        self.display.update_helper_tab(tab).await?
                    }
                }
            }
        }
        Ok(())
    }

    pub async fn show_previous_history_message(&self) -> Result<(), RefchatError> {
        let mut context_lock = self.refchat_context.get_write_lock().await;
        let new_input_text = context_lock.get_previous_history_message().unwrap_or("");
        self.display.change_chat_input(new_input_text).await
    }

    pub async fn show_next_history_message(&self) -> Result<(), RefchatError> {
        let mut context_lock = self.refchat_context.get_write_lock().await;
        if let Some(new_input_text) = context_lock.get_next_history_message() {
            return self.display.change_chat_input(new_input_text).await;
        }
        Ok(())
    }

    pub async fn select_helper_tab(&self, tab_name: &str) -> Result<(), RefchatError> {
        let mut context_lock = self.refchat_context.get_write_lock().await;
        let current_channel = context_lock.get_current_channel();
        if let Some(current_tab) = current_channel.get_current_tab() {
            if current_tab.is_name_matching(tab_name) {
                // It is already the correct tab, no need to update
                return Ok(());
            }
            let previous_tab = current_tab;
            if let Some(selected_tab) = current_channel.get_tab(tab_name) {
                self.display
                    .select_channel_helper_tab(selected_tab, previous_tab)
                    .await?;
                context_lock.set_current_channel_helper_tab(tab_name);
            } else {
                tracing::warn!("Trying to select an unexisting tab");
            }
        }
        Ok(())
    }
}
