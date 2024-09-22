use serde::Deserialize;

use tosurnament_config::{get_config, ConfigError};

#[test]
fn get_config_with_valid_basic_config_file_and_env() {
    #[derive(Debug, PartialEq, Deserialize)]
    struct ConfigOne {
        parameter: String,
    }
    #[derive(Debug, PartialEq, Deserialize)]
    struct ConfigTwo {
        key: String,
    }
    #[derive(Debug, PartialEq, Deserialize)]
    struct Config {
        configone: ConfigOne,
        configtwo: ConfigTwo,
    }
    let _tmp_env = tosurnament_tmpenv::set_var("APP_CONFIGTWO__KEY", "v");

    let config = get_config();

    assert!(config.is_ok());
    let config = config.unwrap();
    let expected = Config {
        configone: ConfigOne {
            parameter: "value".to_owned(),
        },
        configtwo: ConfigTwo {
            key: "v".to_owned(),
        },
    };
    assert_eq!(expected, config);
}

#[test]
fn get_config_with_valid_config_containing_secret_from_env() {
    #[derive(Debug, PartialEq, Deserialize)]
    struct Config {
        secret: String,
    }
    let _tmp_env = tosurnament_tmpenv::set_var("APP_SECRET_FILE", "./config/secret.txt");

    let config = get_config();

    assert!(config.is_ok());
    let config = config.unwrap();
    let expected = Config {
        secret: "secretvalue".to_owned(),
    };
    assert_eq!(expected, config);
}

#[test]
fn get_config_with_invalid_config() {
    #[derive(Deserialize)]
    struct Config {
        _notaparameter: String,
    }

    let config: Result<Config, ConfigError> = get_config();

    assert!(config.is_err());
}
