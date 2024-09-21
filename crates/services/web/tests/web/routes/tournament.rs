use std::collections::HashMap;

use crate::helpers::{assert_ids, spawn_app};

#[tokio::test]
async fn show_tournament_contains_tournament_data() {
    let app = spawn_app().await;

    let response = app.show_tournament(1).await;

    assert_eq!(200, response.status().as_u16());
    let html = response
        .text()
        .await
        .expect("Invalid response returned by the web server");
    let expected_ids = HashMap::from([
        ("tournament_name", "First Tournament"),
        ("tournament_acronym", "FT"),
    ]);
    assert_ids(html, expected_ids);
}
