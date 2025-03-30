mod maps;
mod room;
mod rules;

use serde::Serialize;

pub use maps::MapsTab;
pub use room::RoomTab;
pub use rules::RulesTab;

#[derive(Debug, Serialize, PartialEq)]
#[serde(untagged)]
pub enum ChannelTab {
    Room(RoomTab),
    Maps(MapsTab),
    Rules(RulesTab),
}

impl ChannelTab {
    pub fn is_name_matching(&self, tab_name: &str) -> bool {
        match self {
            ChannelTab::Room(room) => room.get_name() == tab_name,
            ChannelTab::Maps(maps) => maps.get_name() == tab_name,
            ChannelTab::Rules(rules) => rules.get_name() == tab_name,
        }
    }
}
