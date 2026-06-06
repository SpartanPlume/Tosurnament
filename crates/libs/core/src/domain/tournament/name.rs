use nutype::nutype;

#[nutype(
    sanitize(trim),
    validate(not_empty, len_char_max = 128, regex = r#"^[^"\\]+$"#),
    derive(Debug, Serialize, Deserialize, Clone, AsRef)
)]
pub struct TournamentName(String);

use ormlite::postgres::PgArgumentBuffer;
use ormlite::postgres::PgValueRef;
use sqlx::Postgres;

impl sqlx::Type<Postgres> for TournamentName {
    fn type_info() -> <Postgres as sqlx::Database>::TypeInfo {
        <String as sqlx::Type<Postgres>>::type_info()
    }

    fn compatible(ty: &<Postgres as sqlx::Database>::TypeInfo) -> bool {
        <String as sqlx::Type<Postgres>>::compatible(ty)
    }
}

impl sqlx::Encode<'_, Postgres> for TournamentName {
    fn encode_by_ref(
        &self,
        buf: &mut PgArgumentBuffer,
    ) -> Result<sqlx::encode::IsNull, Box<dyn std::error::Error + Send + Sync + 'static>> {
        let s = serde_json::to_value(self)?;
        let s = s.as_str().unwrap();
        <&'_ str as sqlx::Encode<Postgres>>::encode(s, buf)
    }
}

impl sqlx::Decode<'_, Postgres> for TournamentName {
    fn decode(value: PgValueRef<'_>) -> anyhow::Result<Self, sqlx::error::BoxDynError> {
        let value = value.as_str()?;
        let value = serde_json::Value::String(value.to_string());
        let value = serde_json::from_value(value)?;
        Ok(value)
    }
}

#[cfg(test)]
mod tests {
    use super::TournamentName;

    use claims::{assert_err, assert_ok};

    #[test]
    fn empty_name_is_invalid() {
        let name = "".to_string();
        assert_err!(TournamentName::try_new(name));
    }

    #[test]
    fn name_with_only_whitespaces_is_invalid() {
        let name = "  ".to_string();
        assert_err!(TournamentName::try_new(name));
    }

    #[test]
    fn name_longer_than_128_is_invalid() {
        let name = "a".repeat(129);
        assert_err!(TournamentName::try_new(name));
    }

    #[test]
    fn name_containing_invalid_characters_is_invalid() {
        for name in &['\\', '"'] {
            let name = name.to_string();
            assert_err!(TournamentName::try_new(name));
        }
    }

    #[test]
    fn name_containing_valid_characters_is_valid() {
        let name = "Tournament name".to_string();
        assert_ok!(TournamentName::try_new(name));
    }
}
