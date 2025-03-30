use educe::Educe;
use serde::Serialize;

#[derive(Clone, Serialize, Educe, Debug)]
#[educe(PartialEq, Eq)]
pub struct ChatMessage {
    pub username: Option<String>,
    pub text: String,
    pub sent: bool,
    #[educe(Eq(ignore))]
    pub time: String,
}

impl ChatMessage {
    pub fn new(username: Option<String>, text: String, sent: bool) -> Self {
        Self {
            username,
            text,
            sent,
            time: format!("{}", chrono::offset::Utc::now().format("%H:%M")),
        }
    }
}
