use crate::config::Config;
use tosurnament_core::context::DatabaseContext;

#[derive(Clone)]
#[non_exhaustive]
pub struct Context {
    pub db: DatabaseContext,
}

impl Context {
    pub async fn from_config(config: &Config) -> Context {
        let db_context = DatabaseContext::from_database_config(&config.database).await;
        Context { db: db_context }
    }
}
