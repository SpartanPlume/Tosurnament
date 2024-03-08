use nutype::nutype;

#[nutype(
    sanitize(trim),
    validate(not_empty, len_char_max = 128, regex = r#"^[^"\\]+$"#),
    derive(Debug, Deserialize, Clone, AsRef)
)]
pub struct TournamentName(String);

#[cfg(test)]
mod tests {
    use super::TournamentName;

    use claims::{assert_err, assert_ok};

    #[test]
    fn empty_name_is_invalid() {
        let name = "".to_string();
        assert_err!(TournamentName::new(name));
    }

    #[test]
    fn name_with_only_whitespaces_is_invalid() {
        let name = "  ".to_string();
        assert_err!(TournamentName::new(name));
    }

    #[test]
    fn name_longer_than_128_is_invalid() {
        let name = "a".repeat(129);
        assert_err!(TournamentName::new(name));
    }

    #[test]
    fn name_containing_invalid_characters_is_invalid() {
        for name in &['\\', '"'] {
            let name = name.to_string();
            assert_err!(TournamentName::new(name));
        }
    }

    #[test]
    fn name_containing_valid_characters_is_valid() {
        let name = "Tournament name".to_string();
        assert_ok!(TournamentName::new(name));
    }
}
