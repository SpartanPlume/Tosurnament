#[derive(Debug, thiserror::Error)]
pub enum TelemetryError {
    #[error(transparent)]
    InitializationError(#[from] tracing_log::log_tracer::SetLoggerError),
    #[error(transparent)]
    SetGlobalDefaultError(#[from] tracing::subscriber::SetGlobalDefaultError),
}
