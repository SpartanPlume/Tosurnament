mod acronym;
mod name;

use anyhow::Context;
use serde::{Deserialize, Serialize};

use crate::DbPool;
use acronym::TournamentAcronym;
use name::TournamentName;

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Tournament {
    pub id: i32,
    pub name: String,
    pub acronym: String,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub updated_at: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct NewTournament {
    pub name: TournamentName,
    pub acronym: TournamentAcronym,
}

impl Tournament {
    pub async fn get_all(db_pool: &DbPool) -> Result<Vec<Tournament>, anyhow::Error> {
        sqlx::query_as!(Tournament, "SELECT * FROM tournaments")
            .fetch_all(db_pool)
            .await
            .context("Could not retrieve tournaments from database")
    }

    pub async fn get_by_id(db_pool: &DbPool, entry_id: i32) -> Result<Tournament, anyhow::Error> {
        sqlx::query_as!(
            Tournament,
            "SELECT * FROM tournaments WHERE id = $1",
            entry_id
        )
        .fetch_one(db_pool)
        .await
        .context("Could not retrieve tournament by id from database")
    }
}

impl NewTournament {
    pub async fn insert(&self, db_pool: &DbPool) -> Result<Tournament, anyhow::Error> {
        let tournament = sqlx::query_as!(
            Tournament,
            "INSERT INTO tournaments (name, acronym) VALUES ($1, $2) RETURNING *",
            self.name.as_ref(),
            self.acronym.as_ref()
        )
        .fetch_one(db_pool)
        .await
        .context("Could not retrieve tournament by id from database")?;
        Ok(tournament)
    }
}
