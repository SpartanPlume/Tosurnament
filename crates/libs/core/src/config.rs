use secrecy::{ExposeSecret, SecretString};
use serde::Deserialize;
use serde_aux::field_attributes::deserialize_number_from_string;

#[derive(Debug, Deserialize, Clone)]
pub struct DatabaseConfig {
    pub username: String,
    pub password: SecretString,
    pub host: String,
    #[serde(deserialize_with = "deserialize_number_from_string")]
    pub port: u16,
    pub database_name: String,
    pub require_ssl: bool,
}

impl DatabaseConfig {
    fn base(&self) -> SecretString {
        format!(
            "postgres://{}:{}@{}:{}",
            self.username,
            self.password.expose_secret(),
            self.host,
            self.port,
        )
        .into()
    }

    fn add_ssl_mode(&self, database_url: SecretString) -> SecretString {
        let ssl_mode = if self.require_ssl {
            "sslmode=require"
        } else {
            "sslmode=prefer"
        };
        format!("{}?{}", database_url.expose_secret(), ssl_mode).into()
    }

    pub fn without_db(&self) -> SecretString {
        self.add_ssl_mode(self.base())
    }

    pub fn with_db(&self) -> SecretString {
        let base_with_db = format!("{}/{}", self.base().expose_secret(), self.database_name).into();
        self.add_ssl_mode(base_with_db)
    }
}
