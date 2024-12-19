mod round;
mod stage;

pub use round::Round;
pub use stage::Stage;

use ormlite::model::*;
use serde::{Deserialize, Serialize};

#[derive(Model, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct StageRound {
    pub id: i32,
    pub bracket_id: i32,
    pub stage: Stage,
    pub round: Round,
    #[ormlite(default)]
    pub created_at: chrono::DateTime<chrono::Utc>,
    #[ormlite(default)]
    pub updated_at: chrono::DateTime<chrono::Utc>,
}

#[derive(Insert, Debug, Deserialize, Clone)]
#[ormlite(returns = "StageRound")]
pub struct InsertStageRound {
    pub bracket_id: i32,
    pub stage: Stage,
    pub round: Round,
}
