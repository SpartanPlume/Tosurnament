mod name;
mod round;
mod stage_type;

use name::BracketName;
pub use round::BracketRound;
pub use stage_type::StageType;

use ormlite::model::*;
use serde::{Deserialize, Serialize};

#[derive(Model, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Bracket {
    pub id: i32,
    pub tournament_id: i32,
    #[ormlite(default)]
    pub name: Option<String>,
    #[ormlite(default)]
    pub current_round: BracketRound,
    #[ormlite(default)]
    pub qualifiers_type: Option<StageType>,
    #[ormlite(default)]
    pub group_stage_type: Option<StageType>,
    pub main_stage_type: StageType,
    #[ormlite(default)]
    pub created_at: chrono::DateTime<chrono::Utc>,
    #[ormlite(default)]
    pub updated_at: chrono::DateTime<chrono::Utc>,
}

#[derive(Insert, Debug, Deserialize, Clone)]
#[ormlite(returns = "Bracket")]
pub struct InsertBracket {
    pub tournament_id: i32,
    pub name: Option<BracketName>,
    pub qualifiers_type: Option<StageType>,
    pub group_stage_type: Option<StageType>,
    pub main_stage_type: StageType,
}
