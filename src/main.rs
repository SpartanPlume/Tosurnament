use std::net::TcpListener;

use tosurnament::run;

#[tokio::main]
async fn main() -> Result<(), std::io::Error> {
    let listener = TcpListener::bind("127.0.0.1:8080").expect("Failed to bind port");
    run(listener)?.await
}
