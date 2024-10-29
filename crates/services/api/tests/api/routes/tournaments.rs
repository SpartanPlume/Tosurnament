use ormlite::model::*;
use std::collections::HashMap;

use tosurnament_core::domain::tournament::*;

use crate::helpers::*;

#[tokio::test]
async fn create_tournament_with_json_returns_201_for_valid_data() {
    let app = spawn_app().await;
    let body = HashMap::from([("name", "Tournament name"), ("acronym", "TN")]);

    let response = app.http_post("/tournaments", body).await;

    assert_eq!(201, response.status().as_u16());
    let created = response
        .json::<Tournament>()
        .await
        .expect("Invalid tournament object returned by the API");
    assert_eq!(created.name, "Tournament name");
    assert_eq!(created.acronym, "TN");
    let saved = Tournament::select()
        .where_("id = ?")
        .bind(created.id)
        .fetch_one(&app.context.db.pool)
        .await
        .expect("Could not retrieve tournament from db");
    assert_eq!(created, saved);
}

#[tokio::test]
async fn create_tournament_with_form_returns_201_for_valid_data() {
    let app = spawn_app().await;
    let body = HashMap::from([("name", "Tournament name"), ("acronym", "TN")]);

    let response = app.http_post_form("/tournaments", body).await;

    assert_eq!(201, response.status().as_u16());
    let created = response
        .json::<Tournament>()
        .await
        .expect("Invalid tournament object returned by the API");
    assert_eq!(created.name, "Tournament name");
    assert_eq!(created.acronym, "TN");
    let saved = Tournament::select()
        .where_("id = ?")
        .bind(created.id)
        .fetch_one(&app.context.db.pool)
        .await
        .expect("Could not retrieve tournament from db");
    assert_eq!(created, saved);
}

#[tokio::test]
async fn create_tournament_returns_422_when_data_is_missing() {
    let app = spawn_app().await;
    let test_cases = vec![
        (
            HashMap::from([("name", "Tournament name")]),
            "missing acronym",
        ),
        (HashMap::from([("acronym", "TN")]), "missing name"),
        (HashMap::new(), "missing name and acronym"),
    ];

    for (body, error_message) in test_cases {
        let response = app.http_post("/tournaments", body).await;

        assert_eq!(
            422,
            response.status().as_u16(),
            "The API did not fail with error 422 when the payload was {}",
            error_message
        );
    }
}

#[tokio::test]
async fn create_tournament_returns_422_for_invalid_data() {
    let app = spawn_app().await;
    let test_cases = vec![
        (
            HashMap::from([("name", "Tournament name"), ("acronym", " ")]),
            "invalid acronym",
        ),
        (
            HashMap::from([("name", ""), ("acronym", "TN")]),
            "invalid name",
        ),
    ];

    for (body, error_message) in test_cases {
        let response = app.http_post("/tournaments", body).await;

        assert_eq!(
            422,
            response.status().as_u16(),
            "The API did not fail with error 422 when the payload was {}",
            error_message
        );
    }
}

#[tokio::test]
async fn get_tournaments_returns_tournaments() {
    let app = spawn_app().await;

    let response = app.http_get("/tournaments").await;

    assert_eq!(200, response.status().as_u16());
    let tournaments = response
        .json::<Vec<Tournament>>()
        .await
        .expect("Invalid tournament objects returned by the API");
    assert_eq!(11, tournaments.len());
}

#[tokio::test]
async fn get_tournaments_with_per_page_pagination_returns_fixed_number_of_tournaments() {
    let app = spawn_app().await;

    let response = app.http_get("/tournaments?per_page=5").await;

    assert_eq!(200, response.status().as_u16());
    let tournaments = response
        .json::<Vec<Tournament>>()
        .await
        .expect("Invalid tournament objects returned by the API");
    assert_eq!(5, tournaments.len());
    assert_eq!(1, tournaments.first().unwrap().id)
}

#[tokio::test]
async fn get_tournaments_with_page_pagination_returns_fixed_number_of_tournaments_with_offset() {
    let app = spawn_app().await;

    let response = app.http_get("/tournaments?per_page=5&page=2").await;

    assert_eq!(200, response.status().as_u16());
    let tournaments = response
        .json::<Vec<Tournament>>()
        .await
        .expect("Invalid tournament objects returned by the API");
    assert_eq!(5, tournaments.len());
    assert_eq!(6, tournaments.first().unwrap().id)
}

#[tokio::test]
async fn get_tournaments_with_exceeding_page_pagination_returns_no_tournament() {
    let app = spawn_app().await;

    let response = app.http_get("/tournaments?per_page=5&page=100").await;

    assert_eq!(200, response.status().as_u16());
    let tournaments = response
        .json::<Vec<Tournament>>()
        .await
        .expect("Invalid tournament objects returned by the API");
    assert_eq!(0, tournaments.len());
}

#[tokio::test]
async fn get_tournaments_with_exceeding_number_per_page_pagination_returns_as_most_tournaments_as_possible(
) {
    let app = spawn_app().await;

    let response = app.http_get("/tournaments?per_page=100").await;

    assert_eq!(200, response.status().as_u16());
    let tournaments = response
        .json::<Vec<Tournament>>()
        .await
        .expect("Invalid tournament objects returned by the API");
    assert_eq!(11, tournaments.len());
}

#[tokio::test]
async fn get_tournaments_with_invalid_pagination_returns_400() {
    let app = spawn_app().await;

    let response = app.http_get("/tournaments?per_page=-2").await;

    assert_eq!(400, response.status().as_u16());
}

#[tokio::test]
async fn get_tournament_returns_200_for_existing_tournament() {
    let app = spawn_app().await;

    let response = app.http_get("/tournaments/1").await;

    assert_eq!(200, response.status().as_u16());
    let tournament = response
        .json::<Tournament>()
        .await
        .expect("Invalid tournament objects returned by the API");
    assert_eq!(tournament.name, "Basic Tournament RO64");
    assert_eq!(tournament.acronym, "BT64");
}

#[tokio::test]
async fn get_tournament_returns_404_for_non_existing_tournament() {
    let app = spawn_app().await;

    let response = app.http_get("/tournaments/0").await;

    assert_eq!(404, response.status().as_u16());
}
