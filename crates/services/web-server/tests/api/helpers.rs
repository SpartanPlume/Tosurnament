use std::collections::HashMap;

use once_cell::sync::Lazy;
use secrecy::ExposeSecret;
use sqlx::{Connection, Executor, PgConnection, PgPool};
use uuid::Uuid;

use tosurnament_config::get_config;
use tosurnament_core::MIGRATOR;
use tosurnament_web_server::config::{Config, DatabaseConfig};
use tosurnament_web_server::context::Context;
use tosurnament_web_server::startup::Application;
use tosurnament_web_server::telemetry::{get_subscriber, init_subscriber};

pub struct TestApp {
    pub address: String,
    pub context: Context,
}

impl TestApp {
    pub async fn post_tournaments(&self, body: HashMap<&str, &str>) -> reqwest::Response {
        reqwest::Client::new()
            .post(&format!("{}/tournaments", &self.address))
            .header("Content-Type", "application/json")
            .json(&body)
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
        c.database.database_name = Uuid::new_v4().to_string();
        c.application.port = 0;
        c
    };
    configure_database(&config.database).await;

    let application = Application::build(config.clone())
        .await
        .expect("Failed to build application");
    let address = format!("http://127.0.0.1:{}", application.port());
    let _ = tokio::spawn(application.run_until_stopped());

    TestApp {
        address,
        context: Context::from_config(&config).await,
    }
}

async fn configure_database(db_config: &DatabaseConfig) {
    let mut db_connection = PgConnection::connect(&db_config.without_db().expose_secret())
        .await
        .expect("Failed to connect to Postgres");
    db_connection
        .execute(format!(r#"CREATE DATABASE "{}";"#, db_config.database_name).as_str())
        .await
        .expect("Failed to create database");

    let db_pool = PgPool::connect(db_config.with_db().expose_secret())
        .await
        .expect("Failed to connect to Postgres");
    MIGRATOR
        .run(&db_pool)
        .await
        .expect("Failed to migrate the database");
}
