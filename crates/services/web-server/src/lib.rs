pub mod config;
pub mod context;
pub mod error;
pub mod extractor;
pub mod prelude;
pub mod routes;
pub mod server_error;
pub mod startup;
pub mod telemetry;

use tera::Tera;

lazy_static::lazy_static! {
    pub static ref TEMPLATES: Tera = {
        match Tera::new("templates/**/*") {
            Ok(t) => t,
            Err(e) => {
                println!("Parsing error(s): {}", e);
                ::std::process::exit(1);
            }
        }
    };
}
