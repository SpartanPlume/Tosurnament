use std::collections::HashMap;

use tosurnament_config::get_config;
use tosurnament_core::test_utils::configure_database;

use crate::config::Config;
use crate::context::Context;
use crate::startup::Application;

pub struct TestApp {
    pub port: u16,
    pub context: Context,
}

impl TestApp {
    pub async fn http_get(&self, path: &str) -> reqwest::Response {
        reqwest::Client::new()
            .get(&self.build_uri(path))
            .send()
            .await
            .expect("Failed to execute request")
    }

    pub async fn http_post(&self, path: &str, body: HashMap<&str, &str>) -> reqwest::Response {
        reqwest::Client::new()
            .post(&self.build_uri(path))
            .json(&body)
            .send()
            .await
            .expect("Failed to execute request")
    }

    pub async fn http_post_form(&self, path: &str, body: HashMap<&str, &str>) -> reqwest::Response {
        reqwest::Client::new()
            .post(&self.build_uri(path))
            .form(&body)
            .send()
            .await
            .expect("Failed to execute request")
    }

    pub async fn http_put(&self, path: &str, body: HashMap<&str, &str>) -> reqwest::Response {
        reqwest::Client::new()
            .put(&self.build_uri(path))
            .json(&body)
            .send()
            .await
            .expect("Failed to execute request")
    }

    pub async fn http_delete(&self, path: &str, body: HashMap<&str, &str>) -> reqwest::Response {
        reqwest::Client::new()
            .delete(&self.build_uri(path))
            .json(&body)
            .send()
            .await
            .expect("Failed to execute request")
    }

    fn build_uri(&self, path: &str) -> String {
        self.get_uri() + path
    }

    pub fn get_uri(&self) -> String {
        format!("http://127.0.0.1:{}", self.port)
    }
}

pub async fn spawn_app() -> TestApp {
    let config = {
        let mut c: Config = get_config().expect("Failed to read config");
        c.database.database_name = uuid::Uuid::new_v4().to_string();
        c.application.port = 0;
        c
    };
    configure_database(&config.database).await;

    let application = Application::build(config.clone())
        .await
        .expect("Failed to build application");
    let application_port = application.port();
    let _ = tokio::spawn(application.run_until_stopped());

    TestApp {
        port: application_port,
        context: Context::from_config(&config).await,
    }
}
