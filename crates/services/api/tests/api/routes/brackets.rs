use ormlite::model::*;
use serde_json::json;

use tosurnament_core::domain::bracket::*;

use crate::helpers::*;

#[tokio::test]
async fn create_bracket_with_minimal_data() {
    let app = spawn_app().await;
    let body = json!({
        "tournament_id": 1,
        "main_stage_type": "DoubleElimination"
    });

    let response = app.http_post("/brackets", body).await;

    assert_eq!(201, response.status().as_u16());
    let created = response
        .json::<Bracket>()
        .await
        .expect("Invalid bracket object returned by the API");
    assert_eq!(created.tournament_id, 1);
    assert_eq!(created.name, Option::None);
    assert_eq!(created.current_round, BracketRound::NotStarted);
    assert_eq!(created.qualifiers_type, Option::None);
    assert_eq!(created.group_stage_type, Option::None);
    assert_eq!(created.main_stage_type, StageType::DoubleElimination);
    let saved = Bracket::select()
        .where_("id = ?")
        .bind(created.id)
        .fetch_one(&app.context.db.pool)
        .await
        .expect("Could not retrieve bracket from db");
    assert_eq!(created, saved);
}

#[tokio::test]
async fn create_bracket_with_all_data() {
    let app = spawn_app().await;
    let body = json!({
        "tournament_id": 1,
        "name": "10k-100k",
        "qualifiers_type": "Seeding",
        "group_stage_type": "RoundRobin",
        "main_stage_type": "DoubleElimination"
    });

    let response = app.http_post("/brackets", body).await;

    assert_eq!(201, response.status().as_u16());
    let created = response
        .json::<Bracket>()
        .await
        .expect("Invalid bracket object returned by the API");
    assert_eq!(created.tournament_id, 1);
    assert_eq!(created.name, Option::Some(String::from("10k-100k")));
    assert_eq!(created.current_round, BracketRound::NotStarted);
    assert_eq!(created.qualifiers_type, Option::Some(StageType::Seeding));
    assert_eq!(
        created.group_stage_type,
        Option::Some(StageType::RoundRobin)
    );
    assert_eq!(created.main_stage_type, StageType::DoubleElimination);
    let saved = Bracket::select()
        .where_("id = ?")
        .bind(created.id)
        .fetch_one(&app.context.db.pool)
        .await
        .expect("Could not retrieve bracket from db");
    assert_eq!(created, saved);
}

#[tokio::test]
async fn create_bracket_returns_422_for_invalid_data() {
    let app = spawn_app().await;
    let body = json!({
        "tournament_id": 1,
        "main_stage_type": ""
    });

    let response = app.http_post("/brackets", body).await;

    assert_eq!(422, response.status().as_u16());
}

#[tokio::test]
async fn get_brackets_returns_brackets() {
    let app = spawn_app().await;

    let response = app.http_get("/brackets").await;

    assert_eq!(200, response.status().as_u16());
    let brackets = response
        .json::<Vec<Bracket>>()
        .await
        .expect("Invalid bracket objects returned by the API");
    assert_eq!(16, brackets.len());
}
