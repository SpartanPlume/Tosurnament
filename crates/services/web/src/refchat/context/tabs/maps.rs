use serde::Serialize;

#[derive(PartialEq, Debug, Serialize)]
pub struct MapsTab {
    name: String,
}

impl MapsTab {
    pub fn new() -> Self {
        Self {
            name: "Maps".to_string(),
        }
    }

    pub fn get_name(&self) -> &str {
        &self.name
    }
}
