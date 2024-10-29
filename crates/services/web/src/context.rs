use crate::config::{ApiConfig, Config};

#[derive(Clone)]
#[non_exhaustive]
pub struct WebContext {
    pub api: ApiConfig,
}

impl WebContext {
    pub async fn from_config(config: &Config) -> WebContext {
        WebContext {
            api: config.api.clone(),
        }
    }
}
