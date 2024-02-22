use unicode_segmentation::UnicodeSegmentation;

#[derive(Debug)]
pub struct TournamentName(String);

impl TournamentName {
    pub fn parse(s: String) -> Result<TournamentName, String> {
        let s = s.trim().to_string();
        if s.is_empty() {
            return Err("Tournament name is empty".to_string());
        }

        if s.graphemes(true).count() > 128 {
            return Err("Tournament name is too long".to_string());
        }

        let forbidden_characters = ['\\', '"'];
        if s.chars().any(|c| forbidden_characters.contains(&c)) {
            return Err("Tournament name contains invalid characters".to_string());
        }

        Ok(Self(s))
    }
}

impl AsRef<str> for TournamentName {
    fn as_ref(&self) -> &str {
        &self.0
    }
}

#[cfg(test)]
mod tests {
    use crate::domain::tournament_name::TournamentName;

    use claims::{assert_err, assert_ok};

    #[test]
    fn empty_name_is_invalid() {
        let name = "".to_string();
        assert_err!(TournamentName::parse(name));
    }

    #[test]
    fn name_with_only_whitespaces_is_invalid() {
        let name = "  ".to_string();
        assert_err!(TournamentName::parse(name));
    }

    #[test]
    fn name_with_128_graphemes_is_valid() {
        let name = "ɑ".repeat(128);
        assert_ok!(TournamentName::parse(name));
    }

    #[test]
    fn name_longer_than_128_is_invalid() {
        let name = "a".repeat(129);
        assert_err!(TournamentName::parse(name));
    }

    #[test]
    fn name_containing_invalid_characters_is_invalid() {
        for name in &['\\', '"'] {
            let name = name.to_string();
            assert_err!(TournamentName::parse(name));
        }
    }

    #[test]
    fn name_containing_valid_characters_is_valid() {
        let name = "Tournament name".to_string();
        assert_ok!(TournamentName::parse(name));
    }
}
