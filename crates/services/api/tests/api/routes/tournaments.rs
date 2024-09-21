use ormlite::model::*;
use std::collections::HashMap;

use tosurnament_core::domain::tournament::*;

use crate::helpers::*;

#[tokio::test]
async fn create_tournament_with_json_returns_201_for_valid_data() {
    let app = spawn_app().await;
    let body = HashMap::from([("name", "Tournament name"), ("acronym", "TN")]);

    let response = app.post_tournament(body).await;

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

    let response = app.post_tournament_with_form(body).await;

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
        let response = app.post_tournament(body).await;

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
        let response = app.post_tournament(body).await;

        assert_eq!(
            422,
            response.status().as_u16(),
            "The API did not fail with error 422 when the payload was {}",
            error_message
        );
    }
}
