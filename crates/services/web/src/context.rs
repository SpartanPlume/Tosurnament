use crate::config::{ApiConfig, Config};

#[derive(Clone)]
#[non_exhaustive]
pub struct Context {
    pub api: ApiConfig,
}

impl Context {
    pub async fn from_config(config: &Config) -> Context {
        Context {
            api: config.api.clone(),
        }
    }
}
