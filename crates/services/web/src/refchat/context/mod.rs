mod channel;
mod chat_message;
mod tabs;

use std::sync::Arc;
use tokio::sync::{RwLock, RwLockReadGuard, RwLockWriteGuard};

pub use channel::UpdateType as ChannelUpdateType;
pub use channel::{Channel, ChannelTab};
pub use chat_message::ChatMessage;

#[derive(Clone, Debug)]
pub struct RefchatContext {
    lock: Arc<RwLock<RefchatContextLock>>,
    username: String,
}

impl RefchatContext {
    pub fn new(username: String) -> Self {
        Self {
            lock: Arc::new(RwLock::new(RefchatContextLock::new())),
            username,
        }
    }

    pub fn get_username(&self) -> &str {
        &self.username
    }

    pub async fn get_read_lock(&self) -> RwLockReadGuard<'_, RefchatContextLock> {
        self.lock.read().await
    }

    pub async fn get_write_lock(&self) -> RwLockWriteGuard<'_, RefchatContextLock> {
        self.lock.write().await
    }

    pub async fn get_current_channel_real_name(&self) -> String {
        self.lock
            .read()
            .await
            .get_current_channel()
            .get_real_name()
            .to_owned()
    }

    pub async fn is_on_default_channel(&self) -> bool {
        self.lock.read().await.current_channel_index == 0
    }

    pub async fn has_channel(&self, channel_name: &str) -> bool {
        self.lock.read().await.has_channel(channel_name)
    }
}

#[derive(Debug)]
pub struct RefchatContextLock {
    channels: Vec<Channel>,
    current_channel_index: usize,
    is_on_new_channel_selection: bool,
}

impl RefchatContextLock {
    pub fn new() -> Self {
        let default_channel = Channel::default();
        Self {
            channels: vec![default_channel],
            current_channel_index: 0,
            is_on_new_channel_selection: false,
        }
    }

    fn get_index_of_channel_from_name(&self, name: &str) -> Option<usize> {
        self.channels.iter().position(|c| c.is_name_matching(name))
    }

    pub fn _get_default_channel(&self) -> &Channel {
        if let Some(default_channel) = self.channels.first() {
            return default_channel;
        }
        tracing::error!("Default channel is missing");
        panic!();
    }

    pub fn get_default_channel_mut(&mut self) -> &mut Channel {
        if let Some(default_channel) = self.channels.first_mut() {
            return default_channel;
        }
        tracing::error!("Default channel is missing");
        panic!();
    }

    pub fn get_channel(&self, channel_name: &str) -> Option<&Channel> {
        self.channels
            .iter()
            .find(|c| c.is_name_matching(channel_name))
    }

    fn get_channel_mut(&mut self, channel_name: &str) -> Option<&mut Channel> {
        self.channels
            .iter_mut()
            .find(|c| c.is_name_matching(channel_name))
    }

    pub fn get_current_channel(&self) -> &Channel {
        if let Some(current_channel) = self.channels.get(self.current_channel_index) {
            return current_channel;
        }
        tracing::error!("Current channel is missing");
        panic!();
    }

    fn get_current_channel_mut(&mut self) -> &mut Channel {
        if let Some(current_channel) = self.channels.get_mut(self.current_channel_index) {
            return current_channel;
        }
        tracing::error!("Current channel is missing");
        panic!();
    }

    pub fn set_current_channel(&mut self, channel_name: &str) -> bool {
        let index = self.get_index_of_channel_from_name(channel_name);
        if let Some(index) = index {
            self.current_channel_index = index;
            self.is_on_new_channel_selection = false;
            return true;
        }
        false
    }

    pub fn add_channel(&mut self, channel_name: String) -> Option<&Channel> {
        if !self.has_channel(&channel_name) {
            let channel = Channel::new(channel_name);
            self.channels.push(channel);
            return self.channels.last();
        }
        None
    }

    pub fn remove_channel(&mut self, channel_name: &str) -> bool {
        if let Some(channel_index) = self.get_index_of_channel_from_name(channel_name) {
            if channel_index == 0 {
                tracing::error!("Trying to remove the default channel. This is not permitted.");
                return false;
            }
            let current_channel_name = self.get_current_channel().get_real_name().to_owned();
            self.channels.remove(channel_index);
            if let Some(index) = self.get_index_of_channel_from_name(&current_channel_name) {
                self.current_channel_index = index;
            } else {
                self.current_channel_index = 0;
            }
            return true;
        }
        false
    }

    pub fn has_channel(&self, channel_name: &str) -> bool {
        self.get_channel(channel_name).is_some()
    }

    pub fn get_channels(&self) -> &Vec<Channel> {
        &self.channels
    }

    pub fn add_message(
        &mut self,
        channel_name: String,
        message: ChatMessage,
    ) -> Vec<ChannelUpdateType> {
        if let Some(channel) = self.get_channel_mut(&channel_name) {
            channel.add_message(message)
        } else {
            let mut channel = Channel::new(channel_name);
            let updates = channel.add_message(message);
            self.channels.push(channel);
            updates
        }
    }

    pub fn add_message_to_current_channel(
        &mut self,
        message: ChatMessage,
    ) -> Vec<ChannelUpdateType> {
        self.get_current_channel_mut().add_message(message)
    }

    pub fn add_message_to_default_channel(
        &mut self,
        message: ChatMessage,
    ) -> Vec<ChannelUpdateType> {
        self.get_default_channel_mut().add_message(message)
    }

    pub fn set_current_input(&mut self, text: String) {
        self.get_current_channel_mut().set_current_input(text);
    }

    pub fn _get_current_input(&self) -> &str {
        self.get_current_channel()._get_current_input()
    }

    pub fn get_previous_history_message(&mut self) -> Option<&str> {
        let current_channel_index = self.current_channel_index;
        if let Some(channel) = self.channels.get_mut(current_channel_index) {
            channel.get_previous_history_message()
        } else {
            None
        }
    }

    pub fn get_next_history_message(&mut self) -> Option<&str> {
        let current_channel_index = self.current_channel_index;
        if let Some(channel) = self.channels.get_mut(current_channel_index) {
            channel.get_next_history_message()
        } else {
            None
        }
    }

    pub fn set_is_on_new_channel_selection(&mut self, is_on_new_channel_selection: bool) {
        self.is_on_new_channel_selection = is_on_new_channel_selection;
    }

    pub fn is_on_new_channel_selection(&self) -> bool {
        self.is_on_new_channel_selection
    }

    pub fn set_current_channel_helper_tab(&mut self, tab_name: &str) {
        self.get_current_channel_mut().set_tab(tab_name);
    }
}
