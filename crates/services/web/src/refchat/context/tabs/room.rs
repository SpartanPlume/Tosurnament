use once_cell::sync::Lazy;
use regex::Regex;
use serde::Serialize;

use crate::refchat::context::ChatMessage;

#[derive(PartialEq, Clone, Debug, Serialize)]
pub struct RoomTab {
    name: String,
    player_slots: Vec<PlayerSlot>,
    current_map: Option<Map>,
}

static ROOM_REGEX: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"(?i)^Room name:\s+(?<room_name>.*?),\s+History:\s+(?<mp_link>.*)")
        .expect("Invalid regex")
});
static PLAYER_SLOT_REGEX: Lazy<Regex> = Lazy::new(|| {
    Regex::new(
        r"(?i)^Slot\s+(?<slot_id>\d+)\s+(?<player_status>Ready|Not Ready)\s+(?<player_link>[^\s]+)\s+(?<player_name>.*)",
    )
    .expect("Invalid regex")
});

impl RoomTab {
    pub fn new() -> Self {
        Self {
            name: "Room".to_string(),
            player_slots: vec![PlayerSlot::new(); 16],
            current_map: None,
            // current_map: Some(Map {
            //     id: "95382".to_string(),
            //     set_id: "27752".to_string(),
            //     name: "t+pazolite - chipscape".to_string(),
            // }),
        }
    }

    pub fn get_name(&self) -> &str {
        &self.name
    }

    pub fn _is_room_sync_message(message: &ChatMessage) -> bool {
        ROOM_REGEX.is_match(&message.text)
    }

    pub fn get_number_of_player_slots(message: &ChatMessage) -> Option<usize> {
        let players_regex =
            Regex::new(r"(?i)^Players:\s+(?<n_players>\d+)").expect("Invalid regex");
        if let Some(players_captures) = players_regex.captures(&message.text) {
            if let Ok(n_players) = players_captures["n_players"].parse::<usize>() {
                return Some(n_players);
            } else {
                tracing::warn!("Invalid number of players");
            }
        }
        None
    }

    pub fn is_player_slot_sync_message(message: &ChatMessage) -> bool {
        PLAYER_SLOT_REGEX.is_match(&message.text)
    }

    pub fn sync_from_message(&mut self, message: &ChatMessage) {
        // Jan 26 14:22:36 <BanchoBot>	Room name: DBHS: (Welter) vs (xayoto), History: https://osu.ppy.sh/mp/116954007
        // Jan 26 14:22:36 <BanchoBot>	Beatmap: https://osu.ppy.sh/b/95382 t+pazolite - chipscape
        // Jan 26 14:22:36 <BanchoBot>	Team mode: HeadToHead, Win condition: ScoreV2
        // Jan 26 14:22:36 <BanchoBot>	Active mods: NoFail
        // Jan 26 14:22:36 <BanchoBot>	Players: 2
        // Jan 26 14:22:36 <BanchoBot>	Slot 1  Ready     https://osu.ppy.sh/u/11552867 Welter
        // Jan 26 14:22:36 <BanchoBot>	Slot 2  Not Ready https://osu.ppy.sh/u/13334336 xayoto

        self.sync_room_details(message);
        self.sync_current_map(message);
        self.sync_player_slot(message);
    }

    fn sync_room_details(&mut self, message: &ChatMessage) -> bool {
        if ROOM_REGEX.is_match(&message.text) {
            self.player_slots = vec![PlayerSlot::new(); 16];
            return true;
        }
        false
    }

    fn sync_current_map(&mut self, message: &ChatMessage) -> bool {
        let map_regex = Regex::new(r"(?i)^Beatmap:\s+(?<map_link>[^\s]+)\s+(?<map_name>.*)")
            .expect("Invalid regex");
        if let Some(map_captures) = map_regex.captures(&message.text) {
            let map_id = map_captures["map_link"].split("/").last().unwrap_or("");
            self.current_map = Some(Map {
                id: map_id.to_owned(),
                set_id: "27752".to_owned(),
                name: map_captures["map_name"].to_owned(),
            });
            return true;
        }
        false
    }

    fn sync_player_slot(&mut self, message: &ChatMessage) -> bool {
        if let Some(slot_captures) = PLAYER_SLOT_REGEX.captures(&message.text) {
            let slot_id = slot_captures["slot_id"].parse::<usize>().unwrap_or(0);
            if slot_id == 0 {
                tracing::warn!("Slot with an invalid id has been found");
                return false;
            }
            if let Some(slot) = self.player_slots.get_mut(slot_id.saturating_sub(1)) {
                slot.is_player_ready = slot_captures["player_status"].eq_ignore_ascii_case("Ready");
                let player_id = slot_captures["player_link"].split("/").last().unwrap_or("");
                if !player_id.is_empty() {
                    slot.player = Some(Player {
                        id: player_id.to_owned(),
                        name: slot_captures["player_name"].to_owned(),
                    })
                }
            } else {
                tracing::warn!("Slot with a number higher than supported has been found");
            }
            return true;
        }
        false
    }
}

#[derive(PartialEq, Clone, Debug, Serialize)]
struct PlayerSlot {
    player: Option<Player>,
    team: u8,
    is_player_ready: bool,
}

impl PlayerSlot {
    pub fn new() -> Self {
        Self {
            player: None,
            team: 0,
            is_player_ready: false,
        }
    }
}

#[derive(PartialEq, Clone, Debug, Serialize)]
struct Player {
    id: String,
    name: String,
}

#[derive(PartialEq, Clone, Debug, Serialize)]
struct Map {
    id: String,
    set_id: String,
    name: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn room_details_message_reset_player_slots() {
        let message = ChatMessage::new(
            Some("BanchoBot".to_string()),
            "Room name: DBHS: (Welter) vs (xayoto), History: https://osu.ppy.sh/mp/116954007"
                .to_string(),
            false,
        );
        let mut room_helper_tab = RoomTab::new();
        room_helper_tab.player_slots[0].is_player_ready = true;

        room_helper_tab.sync_room_details(&message);

        assert_eq!(false, room_helper_tab.player_slots[0].is_player_ready);
    }

    #[test]
    fn current_map_message_sync_current_map() {
        let message = ChatMessage::new(
            Some("BanchoBot".to_string()),
            "Beatmap: https://osu.ppy.sh/b/95382 t+pazolite - chipscape".to_string(),
            false,
        );
        let mut room_helper_tab = RoomTab::new();

        room_helper_tab.sync_current_map(&message);

        assert_eq!(
            Some(Map {
                id: "95382".to_string(),
                set_id: "27752".to_string(),
                name: "t+pazolite - chipscape".to_string()
            }),
            room_helper_tab.current_map
        );
    }

    #[test]
    fn ready_player_slot_message_sync_player_slot() {
        let message = ChatMessage::new(
            Some("BanchoBot".to_string()),
            "Slot 1  Ready     https://osu.ppy.sh/u/11552867 Welter".to_string(),
            false,
        );
        let mut room_helper_tab = RoomTab::new();

        room_helper_tab.sync_player_slot(&message);

        assert_eq!(
            PlayerSlot {
                player: Some(Player {
                    id: "11552867".to_string(),
                    name: "Welter".to_string()
                }),
                team: 0,
                is_player_ready: true
            },
            room_helper_tab.player_slots[0]
        );
    }

    #[test]
    fn not_ready_player_slot_message_sync_player_slot() {
        let message = ChatMessage::new(
            Some("BanchoBot".to_string()),
            "Slot 2  Not Ready https://osu.ppy.sh/u/13334336 xayoto".to_string(),
            false,
        );
        let mut room_helper_tab = RoomTab::new();

        room_helper_tab.sync_player_slot(&message);

        assert_eq!(
            PlayerSlot {
                player: Some(Player {
                    id: "13334336".to_string(),
                    name: "xayoto".to_string()
                }),
                team: 0,
                is_player_ready: false
            },
            room_helper_tab.player_slots[1]
        );
    }

    #[test]
    fn get_number_of_players_from_players_message() {
        let message = ChatMessage::new(
            Some("BanchoBot".to_string()),
            "Players: 2".to_string(),
            false,
        );

        let n_of_players = RoomTab::get_number_of_player_slots(&message);

        assert_eq!(Some(2), n_of_players);
    }
}
