use serde::Deserialize;
use serde_aux::field_attributes::deserialize_number_from_string;

use tosurnament_core::config::DatabaseConfig;

#[derive(Deserialize, Clone)]
pub struct Config {
    pub database: DatabaseConfig,
    pub application: ApplicationConfig,
}

#[derive(Deserialize, Clone)]
pub struct ApplicationConfig {
    pub host: String,
    #[serde(deserialize_with = "deserialize_number_from_string")]
    pub port: u16,
}
