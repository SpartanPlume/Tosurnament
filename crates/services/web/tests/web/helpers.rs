use once_cell::sync::Lazy;

use tosurnament_config::get_config;
use tosurnament_web::config::Config;
use tosurnament_web::startup::Application;
use tosurnament_web::telemetry::{get_subscriber, init_subscriber};

pub struct TestApp {
    pub address: String,
}

static TRACING: Lazy<()> = Lazy::new(|| {
    let default_filter_level = "info".to_string();
    let subscriber_name = "tosurnament".to_string();
    if std::env::var("TEST_LOG").is_ok() {
        let subscriber = get_subscriber(subscriber_name, default_filter_level, std::io::stdout);
        init_subscriber(subscriber);
    } else {
        let subscriber = get_subscriber(subscriber_name, default_filter_level, std::io::sink);
        init_subscriber(subscriber);
    }
});

pub async fn spawn_app() -> TestApp {
    Lazy::force(&TRACING);

    let config = {
        let mut c: Config = get_config().expect("Failed to read config");
        c.application.port = 0;
        c
    };

    let application = Application::build(config.clone())
        .await
        .expect("Failed to build application");
    let address = format!("http://127.0.0.1:{}", application.port());
    let _ = tokio::spawn(application.run_until_stopped());

    TestApp { address }
}
