mod environment;

use figment::{
    providers::{Env, Format, Yaml},
    Figment,
};
use figment_file_provider_adapter::FileAdapter;
use serde::Deserialize;

use crate::environment::Environment;

pub type ConfigError = figment::Error;

pub fn get_config<T: for<'a> Deserialize<'a>>() -> Result<T, ConfigError> {
    let base_path = match std::env::var("CARGO_MANIFEST_DIR") {
        Ok(path) => std::path::PathBuf::from(path),
        Err(_) => std::env::current_dir().expect("Failed to determine the current directory"),
    };
    let config_dir = base_path.join("config");
    let environment: Environment = std::env::var("APP_ENVIRONMENT")
        .unwrap_or_else(|_| "local".into())
        .try_into()
        .expect("Failed to parse APP_ENVIRONMENT");
    let environment_filename = format!("{}.yml", environment.as_str());

    Figment::new()
        .merge(Yaml::file(config_dir.join("base.yml")))
        .merge(Yaml::file(config_dir.join(environment_filename)))
        .merge(FileAdapter::wrap(Env::prefixed("APP_").split("__")))
        .extract()
}
