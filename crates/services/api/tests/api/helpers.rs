use once_cell::sync::Lazy;

use tosurnament_api::test_utils;
use tosurnament_telemetry::{get_subscriber, init_subscriber};

static TRACING: Lazy<()> = Lazy::new(|| {
    let default_filter_level = "info".to_string();
    let subscriber_name = "tosurnament".to_string();
    if std::env::var("TEST_LOG").is_ok_and(|v| v == "1") {
        let subscriber = get_subscriber(subscriber_name, default_filter_level, std::io::stdout);
        init_subscriber(subscriber).expect("Failed to initialize subscriber");
    } else {
        let subscriber = get_subscriber(subscriber_name, default_filter_level, std::io::sink);
        init_subscriber(subscriber).expect("Failed to initialize subscriber");
    }
});

pub async fn spawn_app() -> test_utils::TestApp {
    Lazy::force(&TRACING);

    test_utils::spawn_app().await
}
