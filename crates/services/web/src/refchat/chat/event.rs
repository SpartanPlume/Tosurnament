#[derive(PartialEq, Eq, Debug)]
pub enum ChatEvent {
    Message {
        channel_name: Option<String>,
        username: Option<String>,
        text: String,
    },
    Join {
        username: String,
        channel_name: String,
    },
    Part {
        username: String,
        channel_name: String,
    },
    Quit {
        username: String,
    },
}
