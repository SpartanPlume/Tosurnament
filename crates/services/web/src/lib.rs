pub mod config;
pub mod context;
pub mod error;
pub mod extractor;
pub mod prelude;
pub mod routes;
pub mod server_error;
pub mod startup;

use once_cell::sync::Lazy;

use tera::Tera;

pub static TEMPLATES: Lazy<Tera> = Lazy::new(|| match Tera::new("templates/**/*") {
    Ok(t) => t,
    Err(e) => {
        println!("Parsing error(s): {}", e);
        ::std::process::exit(1);
    }
});
