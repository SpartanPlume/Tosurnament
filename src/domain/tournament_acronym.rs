#[derive(Debug)]
pub struct TournamentAcronym(String);

impl TournamentAcronym {
    pub fn parse(s: String) -> Result<TournamentAcronym, String> {
        let s = s.trim().to_string();
        if s.is_empty() {
            return Err("Tournament acronym is empty".to_string());
        }

        if s.len() > 16 {
            return Err("Tournament acronym is too long".to_string());
        }

        let allowed_special_characters = ['!', '#', '?', '@'];
        if s.chars()
            .any(|c| !c.is_alphanumeric() && !allowed_special_characters.contains(&c))
        {
            return Err("Tournament acronym contains invalid characters".to_string());
        }

        Ok(Self(s))
    }
}

impl AsRef<str> for TournamentAcronym {
    fn as_ref(&self) -> &str {
        &self.0
    }
}

#[cfg(test)]
mod tests {
    use crate::domain::tournament_acronym::TournamentAcronym;

    use claims::{assert_err, assert_ok};
    use proptest::prelude::*;

    #[test]
    fn empty_acronym_is_invalid() {
        let acronym = "".to_string();
        assert_err!(TournamentAcronym::parse(acronym));
    }

    #[test]
    fn acronym_with_only_whitespaces_is_invalid() {
        let acronym = "  ".to_string();
        assert_err!(TournamentAcronym::parse(acronym));
    }

    #[test]
    fn acronym_longer_than_16_is_invalid() {
        let acronym = "a".repeat(17);
        assert_err!(TournamentAcronym::parse(acronym));
    }

    #[test]
    fn acronym_containing_invalid_character_is_invalid() {
        let acronym = "/".to_string();
        assert_err!(TournamentAcronym::parse(acronym));
    }

    proptest! {
        #[test]
        fn acronym_containing_valid_characters_is_valid(acronym in "[a-z][A-Z][0-9]!#?@") {
            assert_ok!(TournamentAcronym::parse(acronym));
        }
    }
}
