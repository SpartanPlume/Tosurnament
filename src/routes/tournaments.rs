use actix_web::{post, web, HttpResponse, Responder};
use chrono::Utc;
use serde::Deserialize;
use sqlx::PgPool;
use uuid::Uuid;

#[derive(Deserialize)]
struct Tournament {
    name: String,
    acronym: String,
}

#[allow(clippy::async_yields_async)]
#[post("/tournament")]
#[tracing::instrument(skip_all, fields(%tournament.name))]
async fn create_tournament(
    tournament: web::Json<Tournament>,
    db_pool: web::Data<PgPool>,
) -> impl Responder {
    match insert_tournament_in_db(&tournament, &db_pool).await {
        Ok(_) => HttpResponse::Ok(),
        Err(_) => HttpResponse::InternalServerError(),
    }
}

#[tracing::instrument(skip_all)]
async fn insert_tournament_in_db(
    tournament: &Tournament,
    db_pool: &PgPool,
) -> Result<(), sqlx::Error> {
    sqlx::query!(
        r#"
        INSERT INTO tournaments (id, name, acronym, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5)
        "#,
        Uuid::new_v4(),
        tournament.name,
        tournament.acronym,
        Utc::now(),
        Utc::now()
    )
    .execute(db_pool)
    .await
    .map_err(|e| {
        tracing::error!("Failed to execute query: {:?}", e);
        e
    })?;
    Ok(())
}
