use std::sync::{Arc, Mutex};
use tosurnament_telemetry::{get_subscriber, init_subscriber};

use crate::mock_writer::MockWriter;

#[test]
fn initialized_subscriber_contains_logged_data() {
    let buffer = Arc::new(Mutex::new(vec![]));
    let buffer_clone = buffer.clone();
    let subscriber = get_subscriber("test-telemetry".to_owned(), "info".to_owned(), move || {
        MockWriter::new(buffer_clone.clone())
    });
    init_subscriber(subscriber).unwrap();

    tracing::info!("some test data");

    let buffer_guard = buffer.lock().unwrap();
    let output = buffer_guard.to_vec();
    let log = String::from_utf8(output).unwrap();
    assert!(log.contains("some test data"));
}
