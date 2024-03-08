use nutype::nutype;

#[nutype(
    sanitize(trim),
    validate(not_empty, len_char_max = 16, regex = r#"^[\w!#?@]+$"#),
    derive(Debug, Deserialize, Clone, AsRef)
)]
pub struct TournamentAcronym(String);

#[cfg(test)]
mod tests {
    use super::TournamentAcronym;

    use claims::{assert_err, assert_ok};
    use proptest::prelude::*;

    #[test]
    fn empty_acronym_is_invalid() {
        let acronym = "".to_string();
        assert_err!(TournamentAcronym::new(acronym));
    }

    #[test]
    fn acronym_with_only_whitespaces_is_invalid() {
        let acronym = "  ".to_string();
        assert_err!(TournamentAcronym::new(acronym));
    }

    #[test]
    fn acronym_longer_than_16_is_invalid() {
        let acronym = "a".repeat(17);
        assert_err!(TournamentAcronym::new(acronym));
    }

    #[test]
    fn acronym_containing_invalid_character_is_invalid() {
        let acronym = "/".to_string();
        assert_err!(TournamentAcronym::new(acronym));
    }

    proptest! {
        #[test]
        fn acronym_containing_valid_characters_is_valid(acronym in "[a-z][A-Z][0-9]!#?@_") {
            assert_ok!(TournamentAcronym::new(acronym));
        }
    }
}
