use std::{collections::HashMap, net::TcpListener};

use once_cell::sync::Lazy;
use sqlx::{Connection, Executor, PgConnection, PgPool};
use uuid::Uuid;

use tosurnament::configuration::{get_configuration, DatabaseSettings};
use tosurnament::startup::run;
use tosurnament::telemetry::{get_subscriber, init_subscriber};

pub struct TestApp {
    pub address: String,
    pub db_pool: PgPool,
}

static TRACING: Lazy<()> = Lazy::new(|| {
    let default_filter_level = "info".to_string();
    let subscriber_name = "test".to_string();
    if std::env::var("TEST_LOG").is_ok() {
        let subscriber = get_subscriber(subscriber_name, default_filter_level, std::io::stdout);
        init_subscriber(subscriber);
    } else {
        let subscriber = get_subscriber(subscriber_name, default_filter_level, std::io::sink);
        init_subscriber(subscriber);
    }
});

async fn spawn_app() -> TestApp {
    Lazy::force(&TRACING);

    let listener = TcpListener::bind("127.0.0.1:0").expect("Failed to bind random port");
    let port = listener.local_addr().unwrap().port();
    let address = format!("http://127.0.0.1:{}", port);

    let mut configuration = get_configuration().expect("Failed to read configuration");
    configuration.database.database_name = Uuid::new_v4().to_string();
    let db_pool = configure_database(&configuration.database).await;

    let server = run(listener, db_pool.clone()).expect("Failed to bind address");
    let _ = tokio::spawn(server);

    TestApp { address, db_pool }
}

async fn configure_database(db_config: &DatabaseSettings) -> PgPool {
    let mut db_connection = PgConnection::connect_with(&db_config.without_db())
        .await
        .expect("Failed to connect to Postgres");
    db_connection
        .execute(format!(r#"CREATE DATABASE "{}";"#, db_config.database_name).as_str())
        .await
        .expect("Failed to create database");

    let db_pool = PgPool::connect_with(db_config.with_db())
        .await
        .expect("Failed to connect to Postgres");
    sqlx::migrate!("./migrations")
        .run(&db_pool)
        .await
        .expect("Failed to migrate the database");

    db_pool
}

#[tokio::test]
async fn health_check_works() {
    let app = spawn_app().await;
    let client = reqwest::Client::new();

    let response = client
        .get(&format!("{}/health_check", &app.address))
        .send()
        .await
        .expect("Failed to execute request");

    assert!(response.status().is_success());
    assert_eq!(Some(0), response.content_length());
}

#[tokio::test]
async fn create_tournament_returns_200_for_valid_data() {
    let app = spawn_app().await;
    let client = reqwest::Client::new();
    let mut body = HashMap::new();
    body.insert("name", "Tournament name");
    body.insert("acronym", "TN");

    let response = client
        .post(&format!("{}/tournaments", &app.address))
        .header("Content-Type", "application/json")
        .json(&body)
        .send()
        .await
        .expect("Failed to execute request");

    assert_eq!(200, response.status().as_u16());
    let saved = sqlx::query!("SELECT name, acronym FROM tournaments")
        .fetch_one(&app.db_pool)
        .await
        .expect("Failed to fetch saved tournament");
    assert_eq!(saved.name, "Tournament name");
    assert_eq!(saved.acronym, "TN");
}

#[tokio::test]
async fn create_tournament_returns_400_when_data_is_missing() {
    let app = spawn_app().await;
    let client = reqwest::Client::new();
    let test_cases = vec![
        (
            HashMap::from([("name", "Tournament name")]),
            "missing acronym",
        ),
        (HashMap::from([("acronym", "TN")]), "missing name"),
        (HashMap::new(), "missing name and acronym"),
    ];

    for (body, error_message) in test_cases {
        let response = client
            .post(&format!("{}/tournaments", &app.address))
            .header("Content-Type", "application/json")
            .json(&body)
            .send()
            .await
            .expect("Failed to execute request");

        assert_eq!(
            400,
            response.status().as_u16(),
            "The API did not fail with error 400 Bad Request when the payload was {}",
            error_message
        );
    }
}

#[tokio::test]
async fn create_tournament_returns_400_for_invalid_data() {
    let app = spawn_app().await;
    let client = reqwest::Client::new();
    let test_cases = vec![
        (
            HashMap::from([("name", "Tournament name"), ("acronym", " ")]),
            "invalid acronym",
        ),
        (
            HashMap::from([("name", " "), ("acronym", "TN")]),
            "invalid name",
        ),
    ];

    for (body, error_message) in test_cases {
        let response = client
            .post(&format!("{}/tournaments", &app.address))
            .header("Content-Type", "application/json")
            .json(&body)
            .send()
            .await
            .expect("Failed to execute request");

        assert_eq!(
            400,
            response.status().as_u16(),
            "The API did not fail with error 400 Bad Request when the payload was {}",
            error_message
        );
    }
}
