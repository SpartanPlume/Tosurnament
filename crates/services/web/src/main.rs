use tosurnament_config::get_config;
use tosurnament_telemetry::{get_subscriber, init_subscriber};
use tosurnament_web::config::Config;
use tosurnament_web::startup::Application;
use tosurnament_web::TEMPLATES;

#[tokio::main]
async fn main() -> Result<(), std::io::Error> {
    let config: Config = get_config().expect("Failed to read config");

    let subscriber = get_subscriber(
        "tosurnament-web".to_owned(),
        config.log_level.clone(),
        std::io::stdout,
    );
    init_subscriber(subscriber).expect("Failed to initialize subscriber");

    let template_names: Vec<&str> = TEMPLATES.get_template_names().collect();
    tracing::info!("Loaded templates: {:?}", template_names);

    let application = Application::build(config).await?;
    let _ = tokio::spawn(application.run_until_stopped()).await?;
    Ok(())
}
