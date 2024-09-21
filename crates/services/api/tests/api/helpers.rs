use std::collections::HashMap;

use once_cell::sync::Lazy;

use tosurnament_api::test_utils;
use tosurnament_telemetry::{get_subscriber, init_subscriber};

pub trait Routes {
    fn build_uri(&self, path: &str) -> String;

    async fn post_tournament(&self, body: HashMap<&str, &str>) -> reqwest::Response {
        reqwest::Client::new()
            .post(&self.build_uri("/tournaments"))
            .json(&body)
            .send()
            .await
            .expect("Failed to execute request")
    }

    async fn post_tournament_with_form(&self, body: HashMap<&str, &str>) -> reqwest::Response {
        reqwest::Client::new()
            .post(&self.build_uri("/tournaments"))
            .form(&body)
            .send()
            .await
            .expect("Failed to execute request")
    }
}

impl Routes for test_utils::TestApp {
    fn build_uri(&self, path: &str) -> String {
        self.get_uri() + path
    }
}

static TRACING: Lazy<()> = Lazy::new(|| {
    let default_filter_level = "info".to_string();
    let subscriber_name = "tosurnament".to_string();
    if std::env::var("TEST_LOG").is_ok() {
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
