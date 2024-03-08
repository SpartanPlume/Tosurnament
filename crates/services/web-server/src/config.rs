use secrecy::{ExposeSecret, Secret};
use serde::Deserialize;
use serde_aux::field_attributes::deserialize_number_from_string;

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

#[derive(Deserialize, Clone)]
pub struct DatabaseConfig {
    pub username: String,
    pub password: Secret<String>,
    pub host: String,
    #[serde(deserialize_with = "deserialize_number_from_string")]
    pub port: u16,
    pub database_name: String,
    pub require_ssl: bool,
}

impl DatabaseConfig {
    fn base(&self) -> Secret<String> {
        format!(
            "postgres://{}:{}@{}:{}",
            self.username,
            self.password.expose_secret(),
            self.host,
            self.port,
        )
        .into()
    }

    fn add_ssl_mode(&self, database_url: Secret<String>) -> Secret<String> {
        let ssl_mode = if self.require_ssl {
            "sslmode=require"
        } else {
            "sslmode=prefer"
        };
        format!("{}?{}", database_url.expose_secret(), ssl_mode).into()
    }

    pub fn without_db(&self) -> Secret<String> {
        self.add_ssl_mode(self.base())
    }

    pub fn with_db(&self) -> Secret<String> {
        let base_with_db = format!("{}/{}", self.base().expose_secret(), self.database_name).into();
        self.add_ssl_mode(base_with_db)
    }
}
