pub mod config;
pub mod context;
pub mod domain;
#[cfg(feature = "test-utils")]
pub mod test_utils;

use sqlx::migrate::Migrator;
pub static MIGRATOR: Migrator = sqlx::migrate!();

pub use context::DbPool;
