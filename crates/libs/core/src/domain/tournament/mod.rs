mod acronym;
mod name;

use serde::{Deserialize, Serialize};

use acronym::TournamentAcronym;
use name::TournamentName;

use ormlite::model::*;

#[derive(Model, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Tournament {
    pub id: i32,
    pub name: String,
    pub acronym: String,
    #[ormlite(default)]
    pub created_at: chrono::DateTime<chrono::Utc>,
    #[ormlite(default)]
    pub updated_at: chrono::DateTime<chrono::Utc>,
}

#[derive(Insert, Debug, Deserialize, Clone)]
#[ormlite(returns = "Tournament")]
pub struct InsertTournament {
    pub name: TournamentName,
    pub acronym: TournamentAcronym,
}
