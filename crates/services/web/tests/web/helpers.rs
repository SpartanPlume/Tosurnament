use std::collections::HashMap;

use once_cell::sync::Lazy;

use tosurnament_config::get_config;
use tosurnament_telemetry::{get_subscriber, init_subscriber};
use tosurnament_web::config::Config;
use tosurnament_web::startup::Application;

pub struct TestApp {
    pub port: u16,
}

impl TestApp {
    pub fn get_uri(&self) -> String {
        format!("http://127.0.0.1:{}", self.port)
    }

    pub async fn show_tournament(&self, id: i32) -> reqwest::Response {
        reqwest::Client::new()
            .get(&format!("{}/tournaments/{}", self.get_uri(), id))
            .send()
            .await
            .expect("Failed to execute request")
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

pub async fn spawn_app() -> TestApp {
    Lazy::force(&TRACING);

    let api_app = tosurnament_api::test_utils::spawn_app().await;

    let config = {
        let mut c: Config = get_config().expect("Failed to read config");
        c.application.port = 0;
        c.api.port = api_app.port;
        c
    };
    let application = Application::build(config.clone())
        .await
        .expect("Failed to build application");
    let application_port = application.port();
    let _ = tokio::spawn(application.run_until_stopped());

    TestApp {
        port: application_port,
    }
}

pub fn assert_ids(html: String, ids_and_values: HashMap<&str, &str>) {
    let dom =
        tl::parse(&html, tl::ParserOptions::default()).expect("Could not parse response into HTML");
    let parser = dom.parser();
    for (id, value) in ids_and_values {
        let element = dom
            .get_element_by_id(id)
            .expect(&format!("Failed to find element with id {} in HTML", id))
            .get(parser)
            .expect("Invalid parser");
        assert_eq!(value, element.inner_text(parser));
    }
}
