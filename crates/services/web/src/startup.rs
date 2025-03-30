use std::net::SocketAddr;

use axum::routing::any;
use axum::{routing::get, Router};
use tokio::net::TcpListener;
use tower_http::services::ServeDir;

use crate::config::Config;
use crate::context::WebContext;
use crate::routes::*;

pub struct Application {
    port: u16,
    server: Router,
    listener: TcpListener,
}

impl Application {
    pub async fn build(config: Config) -> Result<Self, std::io::Error> {
        let context = WebContext::from_config(&config).await;
        let address = format!("{}:{}", config.application.host, config.application.port);
        let listener = TcpListener::bind(address).await?;
        let port = listener.local_addr().expect("Failed to bind port").port();
        let server = create_server(context);
        Ok(Self {
            port,
            server,
            listener,
        })
    }

    pub fn port(&self) -> u16 {
        self.port
    }

    pub async fn run_until_stopped(self) -> Result<(), std::io::Error> {
        axum::serve(
            self.listener,
            self.server
                .into_make_service_with_connect_info::<SocketAddr>(),
        )
        .await
    }
}

pub fn create_server(context: WebContext) -> Router {
    let base_path = match std::env::var("CARGO_MANIFEST_DIR") {
        Ok(path) => std::path::PathBuf::from(path),
        Err(_) => std::env::current_dir().expect("Failed to determine the current directory"),
    };
    let static_dir = base_path.join("static");

    Router::new()
        .layer(tower_http::trace::TraceLayer::new_for_http())
        .nest_service("/static", ServeDir::new(static_dir))
        .route("/health_check", get(health_check))
        // Html routes
        //.route("/", get(|| async { Redirect::temporary("/tournaments") }))
        .route("/", get(index))
        .route("/tournaments", get(show_more_tournaments))
        .route("/tournaments/{id}", get(show_tournament))
        .route("/refchat", get(show_refchat))
        .route("/refchat-ws", any(handle_refchat_ws))
        .with_state(context.clone())
}
