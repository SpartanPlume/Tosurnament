use std::collections::HashMap;

use crate::helpers::spawn_app;

#[tokio::test]
async fn create_tournament_returns_200_for_valid_data() {
    let app = spawn_app().await;
    let mut body = HashMap::new();
    body.insert("name", "Tournament name");
    body.insert("acronym", "TN");

    let response = app.post_tournaments(body).await;

    assert_eq!(200, response.status().as_u16());
    let saved = sqlx::query!("SELECT name, acronym FROM tournaments")
        .fetch_one(&app.db_pool)
        .await
        .expect("Failed to fetch saved tournament");
    assert_eq!(saved.name, "Tournament name");
    assert_eq!(saved.acronym, "TN");
}

#[tokio::test]
async fn create_tournament_returns_400_when_data_is_missing() {
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
        let response = app.post_tournaments(body).await;

        assert_eq!(
            400,
            response.status().as_u16(),
            "The API did not fail with error 400 Bad Request when the payload was {}",
            error_message
        );
    }
}

#[tokio::test]
async fn create_tournament_returns_400_for_invalid_data() {
    let app = spawn_app().await;
    let test_cases = vec![
        (
            HashMap::from([("name", "Tournament name"), ("acronym", " ")]),
            "invalid acronym",
        ),
        (
            HashMap::from([("name", " "), ("acronym", "TN")]),
            "invalid name",
        ),
    ];

    for (body, error_message) in test_cases {
        let response = app.post_tournaments(body).await;

        assert_eq!(
            400,
            response.status().as_u16(),
            "The API did not fail with error 400 Bad Request when the payload was {}",
            error_message
        );
    }
}
