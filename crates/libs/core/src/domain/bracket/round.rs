use super::super::stage_round::Round;

#[derive(Debug, PartialEq, Eq, serde::Deserialize, serde::Serialize)]
pub enum BracketRound {
    NotStarted,
    Qualifiers(Round),
    GroupStage(Round),
    MainStage(Round),
    Finished,
}

use ormlite::postgres::PgArgumentBuffer;
use ormlite::postgres::PgValueRef;
use sqlx::Postgres;

impl sqlx::Type<Postgres> for BracketRound {
    fn type_info() -> <Postgres as sqlx::Database>::TypeInfo {
        <String as sqlx::Type<Postgres>>::type_info()
    }

    fn compatible(ty: &<Postgres as sqlx::Database>::TypeInfo) -> bool {
        <String as sqlx::Type<Postgres>>::compatible(ty)
    }
}

impl sqlx::Encode<'_, Postgres> for BracketRound {
    fn encode_by_ref(
        &self,
        buf: &mut PgArgumentBuffer,
    ) -> Result<sqlx::encode::IsNull, Box<dyn std::error::Error + Send + Sync + 'static>> {
        let s = serde_json::to_value(self)?;
        let s = s.as_str().unwrap();
        <&'_ str as sqlx::Encode<Postgres>>::encode(s, buf)
    }
}

impl sqlx::Decode<'_, Postgres> for BracketRound {
    fn decode(value: PgValueRef<'_>) -> anyhow::Result<Self, sqlx::error::BoxDynError> {
        let value = value.as_str()?;
        let value = serde_json::Value::String(value.to_string());
        let value = serde_json::from_value(value)?;
        Ok(value)
    }
}
