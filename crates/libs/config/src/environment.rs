#[derive(PartialEq, Eq, Debug)]
pub enum Environment {
    Local,
    Development,
    Testing,
    Production,
}

impl Environment {
    pub fn as_str(&self) -> &'static str {
        match self {
            Environment::Local => "local",
            Environment::Development => "development",
            Environment::Testing => "testing",
            Environment::Production => "production",
        }
    }
}

impl TryFrom<String> for Environment {
    type Error = String;

    fn try_from(s: String) -> Result<Self, Self::Error> {
        match s.to_lowercase().as_str() {
            "local" => Ok(Self::Local),
            "development" => Ok(Self::Development),
            "testing" => Ok(Self::Testing),
            "production" => Ok(Self::Production),
            other => Err(format!("{} is not a supported environment", other)),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::Environment;

    #[test]
    fn environment_local_to_str() {
        assert_eq!("local", Environment::Local.as_str());
    }

    #[test]
    fn environment_development_to_str() {
        assert_eq!("development", Environment::Development.as_str());
    }

    #[test]
    fn environment_testing_to_str() {
        assert_eq!("testing", Environment::Testing.as_str());
    }

    #[test]
    fn environment_production_to_str() {
        assert_eq!("production", Environment::Production.as_str());
    }

    #[test]
    fn environment_from_local() {
        assert_eq!(
            Ok(Environment::Local),
            Environment::try_from("local".to_owned())
        );
    }

    #[test]
    fn environment_from_development() {
        assert_eq!(
            Ok(Environment::Development),
            Environment::try_from("development".to_owned())
        );
    }

    #[test]
    fn environment_from_testing() {
        assert_eq!(
            Ok(Environment::Testing),
            Environment::try_from("testing".to_owned())
        );
    }

    #[test]
    fn environment_from_production() {
        assert_eq!(
            Ok(Environment::Production),
            Environment::try_from("production".to_owned())
        );
    }

    #[test]
    fn environment_from_other_returns_error() {
        assert!(Environment::try_from("other".to_owned()).is_err());
    }
}
