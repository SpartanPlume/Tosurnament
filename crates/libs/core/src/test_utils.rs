use secrecy::ExposeSecret;
use sqlx::migrate::Migrator;
use sqlx::{Connection, Executor, PgConnection, PgPool};

use crate::config::DatabaseConfig;
use crate::MIGRATOR;

pub async fn configure_database(db_config: &DatabaseConfig) {
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
