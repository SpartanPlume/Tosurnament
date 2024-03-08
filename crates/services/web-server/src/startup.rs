use tokio::net::TcpListener;

use axum::{routing::get, Router};

use crate::config::Config;
use crate::context::Context;
use crate::routes::*;

pub struct Application {
    port: u16,
    server: Router,
    listener: TcpListener,
}

impl Application {
    pub async fn build(config: Config) -> Result<Self, std::io::Error> {
        let context = Context::from_config(&config).await;
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
        axum::serve(self.listener, self.server).await
    }
}

pub fn create_server(context: Context) -> Router {
    Router::new()
        .route("/health_check", get(health_check))
        .route("/tournaments", get(get_tournaments).post(create_tournament))
        .with_state(context.clone())
        .layer(tower_http::trace::TraceLayer::new_for_http())
}
