use std::collections::HashMap;

use secrecy::ExposeSecret;
use sqlx::migrate::Migrator;
use sqlx::{Connection, Executor, PgConnection, PgPool};

use tosurnament_config::get_config;
use tosurnament_core::MIGRATOR;

use crate::config::{Config, DatabaseConfig};
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
    static TEST_MIGRATOR: Migrator = sqlx::migrate!("./tests-data");
    for migration in TEST_MIGRATOR.iter() {
        db_pool
            .execute(&*migration.sql)
            .await
            .expect("Failed to add test data");
    }
}
