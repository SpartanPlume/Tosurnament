pub mod context;
pub mod domain;

use sqlx::migrate::Migrator;
pub static MIGRATOR: Migrator = sqlx::migrate!();

pub use context::DbPool;
