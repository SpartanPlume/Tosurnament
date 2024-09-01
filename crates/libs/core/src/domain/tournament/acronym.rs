use nutype::nutype;

#[nutype(
    sanitize(trim),
    validate(not_empty, len_char_max = 16, regex = r#"^[\w!#?@]+$"#),
    derive(Debug, Serialize, Deserialize, Clone, AsRef)
)]
pub struct TournamentAcronym(String);

use ormlite::postgres::PgArgumentBuffer;
use ormlite::postgres::PgValueRef;
use sqlx::Postgres;

impl sqlx::Type<Postgres> for TournamentAcronym {
    fn type_info() -> <Postgres as sqlx::Database>::TypeInfo {
        <String as sqlx::Type<Postgres>>::type_info()
    }

    fn compatible(ty: &<Postgres as sqlx::Database>::TypeInfo) -> bool {
        <String as sqlx::Type<Postgres>>::compatible(ty)
    }
}

impl sqlx::Encode<'_, Postgres> for TournamentAcronym {
    fn encode_by_ref(
        &self,
        buf: &mut PgArgumentBuffer,
    ) -> Result<sqlx::encode::IsNull, Box<(dyn std::error::Error + Send + Sync + 'static)>> {
        let s = serde_json::to_value(self)?;
        let s = s.as_str().unwrap();
        <&'_ str as sqlx::Encode<Postgres>>::encode(s, buf)
    }
}

impl sqlx::Decode<'_, Postgres> for TournamentAcronym {
    fn decode(value: PgValueRef<'_>) -> anyhow::Result<Self, sqlx::error::BoxDynError> {
        let value = value.as_str()?;
        let value = serde_json::Value::String(value.to_string());
        let value = serde_json::from_value(value)?;
        Ok(value)
    }
}

#[cfg(test)]
mod tests {
    use super::TournamentAcronym;

    use claims::{assert_err, assert_ok};
    use proptest::prelude::*;

    #[test]
    fn empty_acronym_is_invalid() {
        let acronym = "".to_string();
        assert_err!(TournamentAcronym::try_new(acronym));
    }

    #[test]
    fn acronym_with_only_whitespaces_is_invalid() {
        let acronym = "  ".to_string();
        assert_err!(TournamentAcronym::try_new(acronym));
    }

    #[test]
    fn acronym_longer_than_16_is_invalid() {
        let acronym = "a".repeat(17);
        assert_err!(TournamentAcronym::try_new(acronym));
    }

    #[test]
    fn acronym_containing_invalid_character_is_invalid() {
        let acronym = "/".to_string();
        assert_err!(TournamentAcronym::try_new(acronym));
    }

    proptest! {
        #[test]
        fn acronym_containing_valid_characters_is_valid(acronym in "[a-z][A-Z][0-9]!#?@_") {
            assert_ok!(TournamentAcronym::try_new(acronym));
        }
    }
}
