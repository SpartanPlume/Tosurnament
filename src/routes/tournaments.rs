use actix_web::{post, web, HttpResponse, Responder};
use chrono::Utc;
use serde::Deserialize;
use sqlx::PgPool;
use uuid::Uuid;

use crate::domain::Tournament;
use crate::domain::TournamentAcronym;
use crate::domain::TournamentName;

#[derive(Deserialize)]
struct BodyData {
    name: String,
    acronym: String,
}

impl TryFrom<BodyData> for Tournament {
    type Error = String;

    fn try_from(value: BodyData) -> Result<Self, Self::Error> {
        let name = TournamentName::parse(value.name)?;
        let acronym = TournamentAcronym::parse(value.acronym)?;
        Ok(Self { name, acronym })
    }
}

#[allow(clippy::async_yields_async)]
#[post("/tournaments")]
#[tracing::instrument(skip_all, fields(%body_data.name))]
async fn create_tournament(
    body_data: web::Json<BodyData>,
    db_pool: web::Data<PgPool>,
) -> impl Responder {
    let tournament = match body_data.0.try_into() {
        Ok(tournament) => tournament,
        Err(_) => return HttpResponse::BadRequest(),
    };
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
        tournament.name.as_ref(),
        tournament.acronym.as_ref(),
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
