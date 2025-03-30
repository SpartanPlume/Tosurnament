#[derive(thiserror::Error)]
pub enum RefchatError {
    #[error(transparent)]
    Disconnected(#[from] anyhow::Error),
    #[error(transparent)]
    Tera(#[from] tera::Error),
    #[error(transparent)]
    JsonDeserialization(#[from] serde_json::Error),
    #[error(transparent)]
    InvalidLogin(#[from] InvalidLoginError),
}

impl std::fmt::Debug for RefchatError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        error_chain_fmt(self, f)
    }
}

pub fn error_chain_fmt(
    e: &impl std::error::Error,
    f: &mut std::fmt::Formatter<'_>,
) -> std::fmt::Result {
    writeln!(f, "{}\n", e)?;
    let mut current = e.source();
    while let Some(cause) = current {
        writeln!(f, "Caused by:\n\t{}", cause)?;
        current = cause.source();
    }
    Ok(())
}

impl RefchatError {
    pub fn trace(&self) {
        match self {
            Self::Disconnected(_) => {
                tracing::info!(error = ?self);
            }
            _ => {
                tracing::error!(error = ?self);
            }
        }
    }
}

#[derive(Debug)]
pub struct InvalidLoginError;

impl std::error::Error for InvalidLoginError {}

impl std::fmt::Display for InvalidLoginError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Invalid username/password")
    }
}
