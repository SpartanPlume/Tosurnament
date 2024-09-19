use tosurnament_api::startup::Application;
use tosurnament_api::telemetry::{get_subscriber, init_subscriber};
use tosurnament_config::get_config;

#[tokio::main]
async fn main() -> Result<(), std::io::Error> {
    let subscriber = get_subscriber("tosurnament".into(), "info".into(), std::io::stdout);
    init_subscriber(subscriber);

    let config = get_config().expect("Failed to read config");
    let application = Application::build(config).await?;
    let _ = tokio::spawn(application.run_until_stopped()).await?;
    Ok(())
}
