// Code heavily inspired from config-rs (https://github.com/mehcode/config-rs) env code and modified to support secret files (for Docker for example)

use std::env;

use config::{ConfigError, Map, Source, Value, ValueKind};

#[derive(Clone, Debug, Default)]
pub struct SecretFileEnvironment {
    prefix: Option<String>,
    prefix_separator: Option<String>,
    separator: Option<String>,
}

impl SecretFileEnvironment {
    pub fn with_prefix(s: &str) -> Self {
        Self {
            prefix: Some(s.into()),
            ..Self::default()
        }
    }

    pub fn prefix(mut self, s: &str) -> Self {
        self.prefix = Some(s.into());
        self
    }

    pub fn prefix_separator(mut self, s: &str) -> Self {
        self.prefix_separator = Some(s.into());
        self
    }

    pub fn separator(mut self, s: &str) -> Self {
        self.separator = Some(s.into());
        self
    }
}

impl Source for SecretFileEnvironment {
    fn clone_into_box(&self) -> Box<dyn Source + Send + Sync> {
        Box::new((*self).clone())
    }

    fn collect(&self) -> Result<Map<String, Value>, ConfigError> {
        let mut m = Map::new();
        let uri: String = "the environment".into();

        let separator = self.separator.as_deref().unwrap_or("");
        let prefix_separator = match (self.prefix_separator.as_deref(), self.separator.as_deref()) {
            (Some(pre), _) => pre,
            (None, Some(sep)) => sep,
            (None, None) => "_",
        };

        // Define a prefix pattern to test and exclude from keys
        let prefix_pattern = self
            .prefix
            .as_ref()
            .map(|prefix| format!("{}{}", prefix, prefix_separator).to_lowercase());

        let collector = |(key, value): (String, String)| {
            // Treat empty environment variables as unset
            if value.is_empty() {
                return;
            }

            let mut key = key.to_lowercase();
            let mut value = value;

            // Check for prefix
            if let Some(ref prefix_pattern) = prefix_pattern {
                if key.starts_with(prefix_pattern) {
                    // Remove this prefix from the key
                    key = key[prefix_pattern.len()..].to_string();
                } else {
                    // Skip this key
                    return;
                }
            }

            if key.ends_with("_file") {
                let content = std::fs::read_to_string(value).unwrap_or("".to_string());
                if content.is_empty() {
                    return;
                }
                key = key[..key.len() - 5].to_string();
                value = content;
            }

            // If separator is given replace with `.`
            if !separator.is_empty() {
                key = key.replace(separator, ".");
            }

            m.insert(key, Value::new(Some(&uri), ValueKind::String(value)));
        };

        env::vars().for_each(collector);

        Ok(m)
    }
}
