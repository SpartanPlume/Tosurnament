mod health_check;
mod index;
mod tournament;
mod tournaments;

pub use health_check::*;
pub use index::*;
pub use tournament::*;
pub use tournaments::*;

#[derive(serde::Deserialize, serde::Serialize)]
pub struct Pagination {
    page: Option<usize>,
    per_page: Option<usize>,
}
