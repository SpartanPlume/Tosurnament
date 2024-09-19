use secrecy::ExposeSecret;

use crate::config::Config;
use tosurnament_core::context::DatabaseContext;

#[derive(Clone)]
#[non_exhaustive]
pub struct Context {
    pub db: DatabaseContext,
}

impl Context {
    pub async fn from_config(config: &Config) -> Context {
        let db_context =
            DatabaseContext::from_connection_string(config.database.with_db().expose_secret())
                .await;
        Context { db: db_context }
    }
}
