use core::time::Duration;

use sqlx::{
    postgres::{PgConnectOptions, PgPoolOptions},
    ConnectOptions, PgPool,
};

pub type DbPool = PgPool;

#[derive(Clone)]
#[non_exhaustive]
pub struct DatabaseContext {
    pub pool: DbPool,
}

impl DatabaseContext {
    pub async fn from_connection_string(connection_string: &str) -> DatabaseContext {
        let url =
            url::Url::parse(connection_string).expect("Could not parse connection string into url");
        let connect_options = PgConnectOptions::from_url(&url).expect("Could not parse url");
        let db_options = PgPoolOptions::new();
        let db_options = db_options.max_connections(32);
        let db_options = db_options.acquire_timeout(Duration::from_secs(4));
        let db_options = db_options.acquire_slow_threshold(Duration::from_secs(2));
        let pool = db_options
            .connect_with(connect_options)
            .await
            .expect("Could not connect to database. Is it up and running?");

        DatabaseContext { pool }
    }
}

#[cfg(test)]
mod tests {
    use super::DatabaseContext;

    use sqlx::postgres::{PgConnectOptions, PgPoolOptions};
    use sqlx::ConnectOptions;

    #[sqlx::test]
    #[ignore]
    async fn init_database_context_with_valid_connection_string_is_ok(
        _pool_options: PgPoolOptions,
        connect_options: PgConnectOptions,
    ) -> sqlx::Result<()> {
        DatabaseContext::from_connection_string(connect_options.to_url_lossy().as_str()).await;
        Ok(())
    }

    #[tokio::test]
    #[should_panic]
    async fn init_database_context_with_empty_connection_string_panics() {
        DatabaseContext::from_connection_string("").await;
    }

    #[tokio::test]
    #[should_panic]
    async fn init_database_context_with_invalid_connection_string_panics() {
        DatabaseContext::from_connection_string(
            "postgres://postgres:nopassword@localhost:5432/tosurnament",
        )
        .await;
    }
}
