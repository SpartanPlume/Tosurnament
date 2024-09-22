mod error;

use tracing::subscriber::set_global_default;
use tracing::Subscriber;
use tracing_bunyan_formatter::{BunyanFormattingLayer, JsonStorageLayer};
use tracing_log::LogTracer;
use tracing_subscriber::{fmt::MakeWriter, layer::SubscriberExt, EnvFilter, Registry};

pub use error::TelemetryError;

pub fn get_subscriber<Sink>(
    name: String,
    env_filter: String,
    sink: Sink,
) -> impl Subscriber + Send + Sync
where
    Sink: for<'a> MakeWriter<'a> + Send + Sync + 'static,
{
    let env_filter =
        EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new(env_filter));
    let formatting_layer = BunyanFormattingLayer::new(name, sink);
    Registry::default()
        .with(env_filter)
        .with(JsonStorageLayer)
        .with(formatting_layer)
}

pub fn init_subscriber(subscriber: impl Subscriber + Send + Sync) -> Result<(), TelemetryError> {
    LogTracer::init()?;
    set_global_default(subscriber)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use tracing_subscriber::Registry;

    use super::get_subscriber;
    use super::init_subscriber;

    #[test]
    fn get_subscriber_does_not_panic() {
        get_subscriber("telemetry".to_owned(), "info".to_owned(), std::io::sink);
    }

    #[test]
    fn init_subscriber_is_ok() {
        let result = init_subscriber(Registry::default());

        assert!(result.is_ok());
    }
}
