mod environment;
mod error;

use figment::{
    providers::{Env, Format, Yaml},
    Figment,
};
use figment_file_provider_adapter::FileAdapter;
use serde::Deserialize;

use crate::environment::Environment;
pub use crate::error::ConfigError;

fn get_config_dir() -> Result<std::path::PathBuf, ConfigError> {
    let base_path = match std::env::var("CARGO_MANIFEST_DIR") {
        Ok(path) => std::path::PathBuf::from(path),
        Err(_) => std::env::current_dir()?,
    };
    let config_dir = base_path.join("config");
    Ok(config_dir)
}

fn get_environment_filename() -> Result<String, ConfigError> {
    let environment: Environment = std::env::var("APP_ENVIRONMENT")
        .unwrap_or_else(|_| "local".into())
        .try_into()
        .map_err(|e| ConfigError::InvalidEnvironment(e))?;
    let environment_filename = format!("{}.yml", environment.as_str());
    Ok(environment_filename)
}

pub fn get_config<T: for<'a> Deserialize<'a>>() -> Result<T, ConfigError> {
    let config_dir = get_config_dir()?;
    let environment_filename = get_environment_filename()?;

    Figment::new()
        .merge(Yaml::file(config_dir.join("base.yml")))
        .merge(Yaml::file(config_dir.join(environment_filename)))
        .merge(FileAdapter::wrap(Env::prefixed("APP_").split("__")))
        .extract()
        .map_err(|e| e.into())
}

#[cfg(test)]
#[serial_test::serial]
mod tests {
    use super::get_config_dir;
    use super::get_environment_filename;

    #[test]
    fn get_config_dir_with_default_cargo_manifest_dir_env_set() {
        let config_dir = get_config_dir();

        assert!(config_dir.is_ok());
        let config_dir = config_dir.unwrap();
        assert!(config_dir.ends_with("crates/libs/config/config"));
    }

    #[test]
    fn get_config_dir_with_overridden_cargo_manifest_dir_env_set() {
        let cargo_manifest_dir =
            std::path::PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
        let new_dir = cargo_manifest_dir.parent().unwrap();
        let _tmp_env = tosurnament_tmpenv::set_var("CARGO_MANIFEST_DIR", new_dir.to_str().unwrap());

        let config_dir = get_config_dir();

        assert!(config_dir.is_ok());
        let config_dir = config_dir.unwrap();
        assert!(config_dir.ends_with("crates/libs/config"));
    }

    #[test]
    fn get_config_dir_with_cargo_manifest_dir_env_unset_uses_current_dir() {
        let _tmp_env = tosurnament_tmpenv::remove_var("CARGO_MANIFEST_DIR");

        let config_dir = get_config_dir();

        assert!(config_dir.is_ok());
        let config_dir = config_dir.unwrap();
        assert!(config_dir.ends_with("crates/libs/config/config"));
    }

    #[test]
    fn get_config_dir_with_invalid_current_dir_returns_error() {
        let _tmp_env = tosurnament_tmpenv::remove_var("CARGO_MANIFEST_DIR");
        std::fs::create_dir("tmp").unwrap();
        let _tmp_current_dir = tosurnament_tmpenv::set_current_dir("tmp").unwrap();
        std::fs::remove_dir("../tmp").expect("Failed to remove tmp directory");

        let config_dir = get_config_dir();

        assert!(config_dir.is_err());
    }

    #[test]
    fn get_environment_filename_with_valid_app_environment_set() {
        let _tmp_env = tosurnament_tmpenv::set_var("APP_ENVIRONMENT", "production");

        let environment_filename = get_environment_filename();

        assert!(environment_filename.is_ok());
        let environment_filename = environment_filename.unwrap();
        assert_eq!("production.yml", &environment_filename);
    }

    #[test]
    fn get_environment_filename_with_app_environment_unset_is_local() {
        let environment_filename = get_environment_filename();

        assert!(environment_filename.is_ok());
        let environment_filename = environment_filename.unwrap();
        assert_eq!("local.yml", &environment_filename);
    }

    #[test]
    fn get_environment_filename_with_invalid_app_environment_unset_returns_error() {
        let _tmp_env = tosurnament_tmpenv::set_var("APP_ENVIRONMENT", "unknown");

        let environment_filename = get_environment_filename();

        assert!(environment_filename.is_err());
    }
}
