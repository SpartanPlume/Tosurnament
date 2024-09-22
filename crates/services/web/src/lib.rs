pub mod config;
pub mod context;
pub mod error;
pub mod extractor;
pub mod prelude;
pub mod routes;
pub mod startup;

use once_cell::sync::Lazy;

use tera::Tera;

pub static TEMPLATES: Lazy<Tera> = Lazy::new(|| {
    let base_path = match std::env::var("CARGO_MANIFEST_DIR") {
        Ok(path) => std::path::PathBuf::from(path),
        Err(_) => std::env::current_dir().expect("Failed to determine the current directory"),
    };
    let templates_dir = base_path.join("templates");
    let templates_dir = templates_dir
        .to_str()
        .expect("Failed to find templates directory");
    match Tera::new(&format!("{}/**/*", templates_dir)) {
        Ok(t) => t,
        Err(e) => {
            println!("Parsing error(s): {}", e);
            ::std::process::exit(1);
        }
    }
});
