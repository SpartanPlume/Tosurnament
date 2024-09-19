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
