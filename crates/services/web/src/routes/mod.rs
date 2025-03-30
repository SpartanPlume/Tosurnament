mod health_check;
mod index;
mod refchat;
mod refchat_ws;
mod tournament;
mod tournaments;

pub use health_check::*;
pub use index::*;
pub use refchat::*;
pub use refchat_ws::handle_refchat_ws;
pub use tournament::*;
pub use tournaments::*;

#[derive(serde::Deserialize, serde::Serialize)]
pub struct Pagination {
    page: Option<usize>,
    per_page: Option<usize>,
}
