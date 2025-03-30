use tosurnament_web::refchat::ChatEvent;

use crate::refchat::helpers::{spawn_app, HtmlTag};

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_new_message_event_sends_message() {
    let mut app = spawn_app().await;
    app.join_chat_channel("#test").await;

    app.send_websocket_event(r#"{"event_type": "NewMessage", "text": "something"}"#)
        .await;

    let expected_message = "something";
    let _input_update = app.next_websocket_text().await;
    let response = app.next_websocket_text().await;
    assert!(response.contains(expected_message));
    let event = app.get_next_chat_event().await;
    assert_eq!(
        ChatEvent::Message {
            channel_name: Some("#test".to_string()),
            username: Some(app.get_client_username().to_string()),
            text: expected_message.to_string()
        },
        event
    );
    app.teardown().await;
}

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_select_valid_channel_event_modifies_displayed_channel() {
    let mut app = spawn_app().await;
    app.join_chat_channel("#test").await;

    // "" is default channel
    app.send_websocket_event(r#"{"event_type": "SelectChannel", "channel_name": ""}"#)
        .await;

    let response = app.next_websocket_text().await;
    let channel_div = HtmlTag::get_element_from_id(&response, "refchat_channel_Server")
        .expect("Could not find expected html tag");
    assert!(channel_div.has_class("active_tab"));
    let previous_channel_div = HtmlTag::get_element_from_id(&response, "refchat_channel_test")
        .expect("Could not find expected html tag");
    assert!(!previous_channel_div.has_class("active_tab"));
    app.teardown().await;
}

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_new_channel_selection_event_displays_channel_selection() {
    let mut app = spawn_app().await;
    app.join_chat_channel("#test").await;

    app.send_websocket_event(r#"{"event_type": "NewChannelSelection"}"#)
        .await;

    let response = app.next_websocket_text().await;
    let div = HtmlTag::get_element_from_id(&response, "refchat_new_channel_selection")
        .expect("Could not find expected html tag");
    assert!(!div.has_class("invisible"));
    app.teardown().await;
}

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_join_channel_event_sends_join_command() {
    let mut app = spawn_app().await;
    app.send_command("/join #test").await;
    let _join_event = app.get_next_chat_event().await;

    app.send_websocket_event(r##"{"event_type": "JoinChannel", "channel_name": "#test"}"##)
        .await;

    let event = app.get_next_chat_event().await;
    assert_eq!(
        ChatEvent::Join {
            username: app.get_client_username().to_string(),
            channel_name: "#test".to_string(),
        },
        event
    );
    app.teardown().await;
}

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_query_user_event_displays_new_channel() {
    let mut app = spawn_app().await;

    app.send_websocket_event(&format!(
        r#"{{"event_type": "QueryUser", "user": "{}"}}"#,
        app.get_server_username()
    ))
    .await;

    let response = app.next_websocket_text().await;
    let div = HtmlTag::get_element_from_id(
        &response,
        &format!("refchat_channel_{}", app.get_server_username()),
    )
    .expect("Could not find expected html tag");
    assert!(div.has_class("active_tab"));
    app.teardown().await;
}

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_part_channel_event_on_current_channel_removes_channel_and_displays_default_channel(
) {
    let mut app = spawn_app().await;
    app.join_chat_channel("#test").await;

    app.send_websocket_event(r##"{"event_type": "PartChannel", "channel_name": "#test"}"##)
        .await;

    let response = app.next_websocket_text().await;
    let div = HtmlTag::get_element_from_id(&response, "refchat_channel_Server")
        .expect("Could not find expected html tag");
    assert!(div.has_class("active_tab"));
    assert!(HtmlTag::get_element_from_id(&response, "refchat_channel_test").is_none());
    let event = app.get_next_chat_event().await;
    assert_eq!(
        ChatEvent::Part {
            username: app.get_client_username().to_string(),
            channel_name: "#test".to_string(),
        },
        event
    );
    app.teardown().await;
}

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_part_channel_event_on_other_channel_removes_channel_only() {
    let mut app = spawn_app().await;
    app.join_chat_channel("#test").await;
    app.join_chat_channel("#test2").await;

    app.send_websocket_event(r##"{"event_type": "PartChannel", "channel_name": "#test"}"##)
        .await;

    let response = app.next_websocket_text().await;
    let div = HtmlTag::get_element_from_id(&response, "refchat_channel_test2")
        .expect("Could not find expected html tag");
    assert!(div.has_class("active_tab"));
    assert!(HtmlTag::get_element_from_id(&response, "refchat_channel_test").is_none());
    let event = app.get_next_chat_event().await;
    assert_eq!(
        ChatEvent::Part {
            username: app.get_client_username().to_string(),
            channel_name: "#test".to_string(),
        },
        event
    );
    app.teardown().await;
}

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_part_channel_event_on_user_removes_channel_without_command() {
    let mut app = spawn_app().await;
    app.join_chat_channel("#test").await;

    app.send_websocket_event(r##"{"event_type": "PartChannel", "channel_name": "#test"}"##)
        .await;

    let response = app.next_websocket_text().await;
    let div = HtmlTag::get_element_from_id(&response, "refchat_channel_Server")
        .expect("Could not find expected html tag");
    assert!(div.has_class("active_tab"));
    assert!(HtmlTag::get_element_from_id(&response, "refchat_channel_test").is_none());
    app.teardown().await;
}

// TODO: test on ChangeChatInput

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_show_previous_history_message_event_shows_previous_message() {
    let mut app = spawn_app().await;
    app.join_chat_channel("#test").await;
    app.send_websocket_event(r#"{"event_type": "ChangeChatInput", "text": "Some test message"}"#)
        .await;

    app.send_websocket_event(r#"{"event_type": "ShowPreviousHistoryMessage"}"#)
        .await;

    let response = app.next_websocket_text().await;
    let input = HtmlTag::get_element_from_id(&response, "refchat_input")
        .expect("Could not find expected html tag");
    assert_eq!("", input.get_attribute("value"));
    app.teardown().await;
}

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_show_next_history_message_event_shows_next_message() {
    let mut app = spawn_app().await;
    app.join_chat_channel("#test").await;
    app.send_websocket_event(r#"{"event_type": "NewMessage", "text": "Some test message"}"#)
        .await;
    let _input_reset = app.next_websocket_text().await;
    let _message_display = app.next_websocket_text().await;

    app.send_websocket_event(r#"{"event_type": "ShowNextHistoryMessage"}"#)
        .await;

    let response = app.next_websocket_text().await;
    let input = HtmlTag::get_element_from_id(&response, "refchat_input")
        .expect("Could not find expected html tag");
    assert_eq!("Some test message", input.get_attribute("value"));
    app.teardown().await;
}

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_select_helper_tab_event_modifies_displayed_helper_tab() {
    let mut app = spawn_app().await;
    app.join_chat_channel("#mp_123").await;

    app.send_websocket_event(r#"{"event_type": "SelectHelperTab", "tab_name": "Rules"}"#)
        .await;

    let response = app.next_websocket_text().await;
    let div = HtmlTag::get_element_from_id(&response, "refchat_helper_tab_Rules")
        .expect("Could not find expected html tag");
    assert!(div.has_class("active_tab"));
    app.teardown().await;
}

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_sync_room_event_sends_mp_settings_command() {
    let mut app = spawn_app().await;
    app.join_chat_channel("#test").await;

    app.send_websocket_event(r#"{"event_type": "SyncRoom"}"#)
        .await;

    let expected_message = "!mp settings";
    let response = app.next_websocket_text().await;
    assert!(response.contains(expected_message));
    let event = app.get_next_chat_event().await;
    assert_eq!(
        ChatEvent::Message {
            channel_name: Some("#test".to_string()),
            username: Some(app.get_client_username().to_string()),
            text: expected_message.to_string()
        },
        event
    );
    app.teardown().await;
}

// TODO: test on InvitePlayers

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_pick_ban_timer_event_sends_mp_timer_command() {
    let mut app = spawn_app().await;
    app.join_chat_channel("#test").await;

    app.send_websocket_event(r#"{"event_type": "PickBanTimer"}"#)
        .await;

    let expected_message = "!mp timer 90";
    let response = app.next_websocket_text().await;
    assert!(response.contains(expected_message));
    let event = app.get_next_chat_event().await;
    assert_eq!(
        ChatEvent::Message {
            channel_name: Some("#test".to_string()),
            username: Some(app.get_client_username().to_string()),
            text: expected_message.to_string()
        },
        event
    );
    app.teardown().await;
}

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_ready_up_timer_event_sends_mp_timer_command() {
    let mut app = spawn_app().await;
    app.join_chat_channel("#test").await;

    app.send_websocket_event(r#"{"event_type": "ReadyUpTimer"}"#)
        .await;

    let expected_message = "!mp timer 60";
    let response = app.next_websocket_text().await;
    assert!(response.contains(expected_message));
    let event = app.get_next_chat_event().await;
    assert_eq!(
        ChatEvent::Message {
            channel_name: Some("#test".to_string()),
            username: Some(app.get_client_username().to_string()),
            text: expected_message.to_string()
        },
        event
    );
    app.teardown().await;
}

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_start_match_event_sends_mp_start_command() {
    let mut app = spawn_app().await;
    app.join_chat_channel("#test").await;

    app.send_websocket_event(r#"{"event_type": "StartMatch"}"#)
        .await;

    let expected_message = "!mp start 5";
    let response = app.next_websocket_text().await;
    assert!(response.contains(expected_message));
    let event = app.get_next_chat_event().await;
    assert_eq!(
        ChatEvent::Message {
            channel_name: Some("#test".to_string()),
            username: Some(app.get_client_username().to_string()),
            text: expected_message.to_string()
        },
        event
    );
    app.teardown().await;
}

#[tokio::test]
#[serial_test::serial]
#[ignore]
async fn refchat_abort_event_sends_mp_abort_command() {
    let mut app = spawn_app().await;
    app.join_chat_channel("#test").await;

    app.send_websocket_event(r#"{"event_type": "Abort"}"#).await;

    let expected_message = "!mp abort";
    let response = app.next_websocket_text().await;
    assert!(response.contains(expected_message));
    let event = app.get_next_chat_event().await;
    assert_eq!(
        ChatEvent::Message {
            channel_name: Some("#test".to_string()),
            username: Some(app.get_client_username().to_string()),
            text: expected_message.to_string()
        },
        event
    );
    app.teardown().await;
}
