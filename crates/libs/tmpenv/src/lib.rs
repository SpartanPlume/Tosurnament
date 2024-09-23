// Copied from bnjjj/tmp_env to add remove_var function

//! tmp_env is a crate which lets you create temporary environment and be automatically restored/cleaned when not needed.

//! For example sometimes you need to change the current directory or set environment variables to launch a process but you don't need this temporary environment for the rest of your program.
//! Then you will use `tmp_env` to create environment variable using `tmp_env::set_var` instead of `std::env::set_var` to get from `tmp_env::set_var` a datastructure which will automatically restore the
//! corresponding environmet variable when dropped.
use std::{
    ffi::{OsStr, OsString},
    fmt::Debug,
    ops::{Deref, DerefMut},
    path::{Path, PathBuf},
};

use rand::distributions::Alphanumeric;
use rand::{thread_rng, Rng};

/// A helper datastructure for ensuring that we switch back to the current folder before the
/// end of the current scope.
pub struct CurrentDir(std::path::PathBuf);

impl Debug for CurrentDir {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self.0)
    }
}

pub fn set_current_dir<P: AsRef<Path>>(path: P) -> Result<CurrentDir, std::io::Error> {
    let current_dir = std::env::current_dir()?;
    std::env::set_current_dir(&path)?;
    Ok(CurrentDir(current_dir))
}

impl Drop for CurrentDir {
    fn drop(&mut self) {
        std::env::set_current_dir(&self.0).expect("cannot go back to the previous directory");
    }
}
/// A helper datastructure for ensuring that we restore the current environment variable before the
/// end of the current scope.
pub struct CurrentEnv(OsString, Option<String>);

impl Debug for CurrentEnv {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self.0)
    }
}

pub fn set_var<K: AsRef<OsStr>, V: AsRef<OsStr>>(key: K, value: V) -> CurrentEnv {
    let key = key.as_ref();
    let previous_val = std::env::var(key).ok();
    std::env::set_var(key, value);
    CurrentEnv(key.to_owned(), previous_val)
}

pub fn remove_var<K: AsRef<OsStr>>(key: K) -> CurrentEnv {
    let key = key.as_ref();
    let previous_val = std::env::var(key).ok();
    std::env::remove_var(key);
    CurrentEnv(key.to_owned(), previous_val)
}

impl Drop for CurrentEnv {
    fn drop(&mut self) {
        match self.1.take() {
            Some(previous_val) => std::env::set_var(&self.0, previous_val),
            None => std::env::remove_var(&self.0),
        }
    }
}

/// A helper datastructure for ensuring that we delete the tmp dir created before
/// end of the current scope.
pub struct TmpDir(pub(crate) PathBuf);

impl Deref for TmpDir {
    type Target = PathBuf;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl DerefMut for TmpDir {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.0
    }
}

impl Debug for TmpDir {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self.0)
    }
}

pub fn create_temp_dir() -> Result<TmpDir, std::io::Error> {
    let tmp_dir = std::env::temp_dir();
    let tmp_path = tmp_dir.join(random_path());
    std::fs::create_dir(&tmp_path)?;

    Ok(TmpDir(tmp_path))
}

impl Drop for TmpDir {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).expect("cannot delete the tmp dir")
    }
}

fn random_path() -> PathBuf {
    let rand_string: String = thread_rng()
        .sample_iter(&Alphanumeric)
        .take(10)
        .map(char::from)
        .collect();

    PathBuf::from(rand_string)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_env() {
        {
            let _tmp_env = set_var("TEST_TMP_ENV", "myvalue");
            assert_eq!(std::env::var("TEST_TMP_ENV"), Ok(String::from("myvalue")));
        }
        assert!(std::env::var("TEST_TMP_ENV").is_err());
        // Because guard is dropped
        set_var("TEST_TMP_ENV_DROPPED", "myvaluedropped");
        assert!(std::env::var("TEST_TMP_ENV_DROPPED").is_err());
    }

    #[test]
    fn test_env_with_previous_value() {
        std::env::set_var("TEST_TMP_ENV_PREVIOUS", "previous_value");
        {
            let _tmp_env = set_var("TEST_TMP_ENV_PREVIOUS", "myvalue");
            assert_eq!(
                std::env::var("TEST_TMP_ENV_PREVIOUS"),
                Ok(String::from("myvalue"))
            );
        }
        assert_eq!(
            std::env::var("TEST_TMP_ENV_PREVIOUS"),
            Ok(String::from("previous_value"))
        );
    }

    #[test]
    fn test_remove_env() {
        let _tmp_env = remove_var("TEST_TMP_REMOVE_ENV");
        assert!(std::env::var("TEST_TMP_REMOVE_ENV").is_err());
    }

    #[test]
    fn test_remove_env_with_previous_value() {
        std::env::set_var("TEST_TMP_REMOVE_ENV_PREVIOUS", "previous_value");
        {
            let _tmp_env = remove_var("TEST_TMP_REMOVE_ENV_PREVIOUS");
            assert!(std::env::var("TEST_TMP_REMOVE_ENV_PREVIOUS").is_err());
        }
        assert_eq!(
            std::env::var("TEST_TMP_REMOVE_ENV_PREVIOUS"),
            Ok(String::from("previous_value"))
        );
    }

    #[test]
    fn test_tmp_dir() {
        #[allow(unused_assignments)]
        let mut tmp_dir_created: Option<PathBuf> = None;
        {
            let tmp_dir = create_temp_dir().expect("cannot create temp dir");
            tmp_dir_created = Some(tmp_dir.0.clone());
            assert!(std::fs::metadata(&*tmp_dir).is_ok());
        }
        assert!(std::fs::metadata(tmp_dir_created.unwrap()).is_err());
    }
}
