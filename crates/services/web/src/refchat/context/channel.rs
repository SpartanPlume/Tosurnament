use educe::Educe;
use serde::Serialize;

use super::{
    chat_message::ChatMessage,
    tabs::{MapsTab, RoomTab, RulesTab},
};

pub use super::tabs::ChannelTab;

#[derive(Debug, PartialEq)]
struct RoomSync {
    room_player_slots: usize,
    n_player_slots_found: usize,
}

impl RoomSync {
    pub fn new() -> Self {
        Self {
            room_player_slots: 0,
            n_player_slots_found: 0,
        }
    }
}

#[derive(Debug, Serialize, Educe)]
#[educe(PartialEq)]
pub struct Channel {
    real_name: String,
    display_name: String,
    category: ChannelCategory,
    messages: Vec<ChatMessage>,
    history: Vec<String>,
    current_input: String,
    history_index: Option<usize>,
    tabs: Vec<ChannelTab>,
    current_tab_index: usize,
    #[serde(skip_serializing)]
    #[educe(PartialEq(ignore))]
    room_sync: RoomSync,
}

impl Channel {
    pub fn new(name: String) -> Self {
        let mut display_name = name.clone();
        let mut category = ChannelCategory::DirectMessage;
        let mut tabs = Vec::new();
        if let Some(new_name) = name.strip_prefix('#') {
            display_name = new_name.to_string();
            category = ChannelCategory::Room;
            tabs = vec![
                ChannelTab::Room(RoomTab::new()),
                ChannelTab::Maps(MapsTab::new()),
                ChannelTab::Rules(RulesTab::new()),
            ];
        }
        Self {
            real_name: name,
            display_name,
            category,
            tabs,
            ..Self::default()
        }
    }

    pub fn default() -> Self {
        Self {
            real_name: "".to_string(),
            display_name: "Server".to_string(),
            category: ChannelCategory::System,
            messages: Vec::new(),
            history: Vec::new(),
            current_input: String::new(),
            history_index: None,
            tabs: Vec::new(),
            current_tab_index: 0,
            room_sync: RoomSync::new(),
        }
    }

    pub fn is_default(&self) -> bool {
        self.category == ChannelCategory::System
    }

    pub fn get_real_name(&self) -> &str {
        &self.real_name
    }

    pub fn is_name_matching(&self, name: &str) -> bool {
        self.get_real_name() == name
    }

    pub fn is_room(&self) -> bool {
        self.category == ChannelCategory::Room
    }

    pub fn add_message(&mut self, message: ChatMessage) -> Vec<UpdateType> {
        let mut update_types = vec![UpdateType::AddMessage];

        // TODO: check if BanchoBot sent message
        if let Some(room_tab) = self.get_room_tab_mut() {
            room_tab.sync_from_message(&message);

            if let Some(n_player_slots) = RoomTab::get_number_of_player_slots(&message) {
                tracing::debug!("Number of player slots to sync: {n_player_slots}");
                self.room_sync.room_player_slots = n_player_slots;
                self.room_sync.n_player_slots_found = 0;
            } else if RoomTab::is_player_slot_sync_message(&message) {
                tracing::debug!("Player slot synced");
                self.room_sync.n_player_slots_found += 1;
                if self.room_sync.n_player_slots_found == self.room_sync.room_player_slots {
                    tracing::debug!("All player slots synced");
                    // If the current tab is room, then we update the view
                    if let Some(ChannelTab::Room(_)) = self.get_current_tab() {
                        update_types.push(UpdateType::UpdateTab);
                    }
                }
            }
        }

        if message.sent {
            // When adding a new message from current user, the history changes and we reset the index
            self.history.push(message.text.clone());
            self.history_index = None;
        }
        self.messages.push(message);
        update_types
    }

    pub fn _get_messages(&self) -> &Vec<ChatMessage> {
        &self.messages
    }

    pub fn get_previous_history_message(&mut self) -> Option<&str> {
        if self.history.is_empty() {
            return None;
        }
        if self.history_index.is_none() || self.history_index == Some(0) {
            self.history_index = None;
            None
        } else {
            let new_index = self.history_index.unwrap() - 1;
            self.history_index = Some(new_index);
            Some(&self.history[self.history.len() - 1 - new_index])
        }
    }

    pub fn get_next_history_message(&mut self) -> Option<&str> {
        if self.history.is_empty() {
            return None;
        }
        let mut new_index = self.history_index.map_or(0, |i| i + 1);
        if new_index >= self.history.len() {
            new_index = self.history.len() - 1;
        }
        self.history_index = Some(new_index);
        Some(&self.history[self.history.len() - 1 - new_index])
    }

    pub fn set_current_input(&mut self, text: String) {
        self.current_input = text;
    }

    pub fn _get_current_input(&self) -> &str {
        &self.current_input
    }

    pub fn get_current_tab(&self) -> Option<&ChannelTab> {
        self.tabs.get(self.current_tab_index)
    }

    fn _get_current_tab_mut(&mut self) -> Option<&mut ChannelTab> {
        self.tabs.get_mut(self.current_tab_index)
    }

    pub fn get_tab(&self, tab_name: &str) -> Option<&ChannelTab> {
        self.tabs.iter().find(|t| t.is_name_matching(tab_name))
    }

    pub fn set_tab(&mut self, tab_name: &str) {
        if let Some(index) = self.tabs.iter().position(|t| t.is_name_matching(tab_name)) {
            self.current_tab_index = index;
        }
    }

    fn _get_room_tab(&self) -> Option<&RoomTab> {
        for tab in &self.tabs {
            if let ChannelTab::Room(room) = tab {
                return Some(room);
            }
        }
        None
    }

    fn get_room_tab_mut(&mut self) -> Option<&mut RoomTab> {
        for tab in &mut self.tabs {
            if let ChannelTab::Room(room) = tab {
                return Some(room);
            }
        }
        None
    }
}

#[derive(PartialEq, Eq, Clone, Debug, Serialize)]
enum ChannelCategory {
    System,
    Room,
    DirectMessage,
}

pub enum UpdateType {
    AddMessage,
    UpdateTab,
}

#[cfg(test)]
mod tests {
    use super::Channel;
    use super::ChannelCategory;

    #[test]
    fn string_starting_with_hashtag_is_channel_channel() {
        let channel = Channel::new("#test".to_string());

        assert_eq!("#test", channel.real_name);
        assert_eq!("test", channel.display_name);
        assert_eq!(ChannelCategory::Room, channel.category);
    }

    #[test]
    fn string_not_starting_with_hashtag_is_people_channel() {
        let channel = Channel::new("test".to_string());

        assert_eq!("test", channel.real_name);
        assert_eq!("test", channel.display_name);
        assert_eq!(ChannelCategory::DirectMessage, channel.category);
    }
}
