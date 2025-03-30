use crate::refchat::error::RefchatError;

#[derive(thiserror::Error)]
pub enum ChatError {
    #[error(transparent)]
    Disconnected(#[from] anyhow::Error),
    #[error(transparent)]
    Irc(#[from] irc::error::Error),
    #[error(transparent)]
    Refchat(#[from] RefchatError),
}

impl std::fmt::Debug for ChatError {
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

impl ChatError {
    pub fn trace(&self) {
        match self {
            Self::Disconnected(_) => {
                tracing::info!(error = ?self);
            }
            Self::Refchat(error) => {
                error.trace();
            }
            Self::Irc(_) => {
                tracing::warn!(error = ?self);
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
