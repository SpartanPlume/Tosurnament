#[derive(Debug, thiserror::Error)]
pub enum ConfigError {
    #[error("Failed to determine the current directory")]
    IoError(#[from] std::io::Error),
    #[error("{0}")]
    InvalidEnvironment(String),
    #[error(transparent)]
    InvalidConfig(#[from] Box<figment::Error>),
}

impl From<figment::Error> for ConfigError {
    fn from(e: figment::Error) -> Self {
        ConfigError::InvalidConfig(Box::new(e))
    }
}
