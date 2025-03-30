use serde::Serialize;

#[derive(PartialEq, Debug, Serialize)]
pub struct RulesTab {
    name: String,
}

impl RulesTab {
    pub fn new() -> Self {
        Self {
            name: "Rules".to_string(),
        }
    }

    pub fn get_name(&self) -> &str {
        &self.name
    }
}
