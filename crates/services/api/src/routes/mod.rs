mod health_check;
mod tournaments;

pub use health_check::*;
pub use tournaments::*;

#[derive(serde::Deserialize)]
pub struct Pagination {
    page: Option<usize>,
    per_page: Option<usize>,
}
