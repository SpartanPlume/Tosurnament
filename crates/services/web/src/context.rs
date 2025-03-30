use crate::config::{ApiConfig, Config, RefchatConfig};

#[derive(Clone)]
#[non_exhaustive]
pub struct WebContext {
    pub api: ApiConfig,
    pub refchat: RefchatConfig,
}

impl WebContext {
    pub async fn from_config(config: &Config) -> WebContext {
        WebContext {
            api: config.api.clone(),
            refchat: config.refchat.clone(),
        }
    }
}
