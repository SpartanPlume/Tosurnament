use sqlx::PgPool;

pub type DbPool = PgPool;

#[derive(Clone)]
#[non_exhaustive]
pub struct DatabaseContext {
    pub pool: DbPool,
}

impl DatabaseContext {
    pub async fn from_connection_string(connection_string: &str) -> DatabaseContext {
        let pool = PgPool::connect(connection_string)
            .await
            .expect("Could not connect to database");

        DatabaseContext { pool }
    }
}
