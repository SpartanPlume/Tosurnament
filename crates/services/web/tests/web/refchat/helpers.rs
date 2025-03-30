use std::future::IntoFuture;
use std::net::{Ipv4Addr, SocketAddr};

use axum::{
    extract::{ws::WebSocket, State, WebSocketUpgrade},
    routing::get,
    Router,
};
use futures::{SinkExt, StreamExt};
use once_cell::sync::Lazy;
use tokio::net::TcpStream;
use tokio::time::Duration;
use tokio_tungstenite::{tungstenite, MaybeTlsStream, WebSocketStream};

use tosurnament_config::get_config;
use tosurnament_web::config::Config;
use tosurnament_web::refchat::{
    handle_chat, ChatClient, ChatEvent, ChatReceiver, ChatSender, RefchatError, RefchatInterface,
};

use super::super::helpers::TRACING;

pub struct TestWebSocket(WebSocketStream<MaybeTlsStream<TcpStream>>);

impl TestWebSocket {
    pub async fn new(connection_string: &str) -> Self {
        let (stream, _) = tokio_tungstenite::connect_async(connection_string)
            .await
            .expect("Could not connect websocket");
        Self(stream)
    }

    pub async fn send(&mut self, message: &str) -> Result<(), tungstenite::Error> {
        self.0.send(tungstenite::Message::text(message)).await
    }

    pub async fn next(&mut self) -> Result<String, Box<dyn std::error::Error>> {
        match self.0.next().await {
            Some(next) => match next? {
                tungstenite::Message::Text(msg) => Ok(msg.as_str().to_owned()),
                _ => panic!("Invalid message received"),
            },
            None => Err(Box::from("Connection closed")),
        }
    }
}

struct OnDrop<F: FnOnce()>(std::mem::ManuallyDrop<F>);
impl<F: FnOnce()> Drop for OnDrop<F> {
    #[inline(always)]
    fn drop(&mut self) {
        (unsafe { std::ptr::read(&*self.0) })();
    }
}

pub struct TestApp {
    chat_sender: ChatSender,
    chat_receiver: ChatReceiver,
    websocket: TestWebSocket,
    server_username: String,
    client_username: String,
}

impl TestApp {
    pub async fn new(
        socket_addr: SocketAddr,
        mut chat_client: ChatClient,
        client_username: String,
    ) -> Self {
        chat_client
            .wait_until_ready()
            .await
            .expect("An error occurred while waiting for full connection to chat server");
        let (chat_sender, chat_receiver) =
            chat_client.split().expect("Could not split chat client");
        let websocket = TestWebSocket::new(&format!("ws://{}/ws", socket_addr)).await;
        let server_username = chat_sender.get_username().to_owned();
        Self {
            chat_sender,
            chat_receiver,
            websocket,
            server_username,
            client_username,
        }
    }

    pub fn get_server_username(&self) -> &str {
        &self.server_username
    }

    pub fn get_client_username(&self) -> &str {
        &self.client_username
    }

    pub async fn send_command(&mut self, message: &str) {
        let command = self.chat_sender.parse_command_from_text(message);
        if let Err(err) = self.chat_sender.send_command("".to_string(), command).await {
            self.panic_teardown(Box::new(err), "Could not send command in chat")
                .await;
        }
    }

    pub async fn _send_chat_message(&mut self, channel_name: &str, message: &str) {
        let command = self.chat_sender.parse_command_from_text(message);
        if let Err(err) = self
            .chat_sender
            .send_command(channel_name.to_string(), command)
            .await
        {
            self.panic_teardown(Box::new(err), "Could not send message in chat")
                .await;
        }
    }

    pub async fn get_next_chat_event(&mut self) -> ChatEvent {
        match self.chat_receiver.next_event().await {
            Ok(event) => event,
            Err(err) => {
                self.panic_teardown(Box::new(err), "Could not process chat event")
                    .await
            }
        }
    }

    pub async fn send_websocket_event(&mut self, event: &str) {
        if let Err(err) = self.websocket.send(event).await {
            self.panic_teardown(Box::new(err), "Could not send event in websocket")
                .await
        }
    }

    pub async fn next_websocket_text(&mut self) -> String {
        match self.websocket.next().await {
            Ok(text) => text,
            Err(err) => {
                self.panic_teardown(err, "Could not process event in websocket")
                    .await
            }
        }
    }

    pub async fn join_chat_channel(&mut self, channel_name: &str) {
        self.send_command(&format!("/join {channel_name}")).await;
        let _join_event = self.get_next_chat_event().await;
        self.send_websocket_event(&format!(
            r#"{{"event_type": "JoinChannel", "channel_name": "{channel_name}"}}"#
        ))
        .await;
        let _add_channel = self.next_websocket_text().await;
        let _join_event = self.get_next_chat_event().await;
    }

    pub async fn teardown(self) {
        let command = self.chat_sender.parse_command_from_text("/quit");
        let _ = self.chat_sender.send_command("".to_string(), command).await;
        drop(self);
        tokio::time::sleep(Duration::from_secs(1)).await;
    }

    async fn panic_teardown(&mut self, err: Box<dyn std::error::Error>, msg: &str) -> ! {
        unsafe {
            let app = std::ptr::read(self);
            let _x = OnDrop(std::mem::ManuallyDrop::new(|| std::process::abort()));
            app.teardown().await;
            panic!("{msg}: {err}")
        }
    }
}

pub async fn spawn_app() -> TestApp {
    Lazy::force(&TRACING);

    let client_username = format!("c{}", uuid::Uuid::new_v4());
    let listener = tokio::net::TcpListener::bind(SocketAddr::from((Ipv4Addr::UNSPECIFIED, 0)))
        .await
        .expect("Could not listen to a port");
    let socket_addr = listener.local_addr().expect("Could not get local address");
    tokio::spawn(axum::serve(listener, create_router(client_username.clone())).into_future());

    let config: Config = get_config().expect("Failed to read config");
    let server_username = format!("s{}", uuid::Uuid::new_v4());
    let chat_client = ChatClient::try_new(&config.refchat, server_username, "".into())
        .await
        .expect("Could not connect to chat server");

    let mut app = TestApp::new(socket_addr, chat_client, client_username).await;
    let _show_channels = app.next_websocket_text().await;

    app
}

pub struct HtmlTag<'a> {
    _html: &'a str,
    inner: tl::HTMLTag<'a>,
}

impl<'a> HtmlTag<'a> {
    pub fn get_element_from_id(html: &'a str, id: &str) -> Option<Self> {
        let dom = tl::parse(&html, tl::ParserOptions::default())
            .expect("Could not parse response into HTML");
        let parser = dom.parser();
        let element = dom
            .get_element_by_id(id)?
            .get(parser)
            .expect("Invalid parser")
            .as_tag()
            .expect("Not a HTMLTag");
        Some(Self {
            _html: html,
            inner: element.clone(),
        })
    }

    pub fn has_class(&self, class: &str) -> bool {
        self.inner
            .attributes()
            .class()
            .expect("No class found")
            .as_utf8_str()
            .split(' ')
            .any(|c| c == class)
    }

    pub fn _get_content(&self) -> String {
        let dom = tl::parse(self._html, tl::ParserOptions::default())
            .expect("Could not parse response into HTML");
        self.inner.inner_text(dom.parser()).to_string()
    }

    pub fn get_attribute(&self, attribute: &str) -> String {
        self.inner
            .attributes()
            .get(attribute)
            .expect("Attribute not found")
            .map_or_else(|| String::new(), |a| a.as_utf8_str().to_string())
    }
}

fn create_router(client_username: String) -> Router {
    Router::new().route("/ws", get(prepare_interface_ws).with_state(client_username))
}

async fn prepare_interface_ws(
    ws: WebSocketUpgrade,
    State(client_username): State<String>,
) -> axum::response::Response {
    ws.on_upgrade(|socket| handle_interface_ws(socket, client_username))
}

async fn handle_interface_ws(socket: WebSocket, client_username: String) {
    let config: Config = get_config().expect("Failed to read config");
    let mut chat_client = ChatClient::try_new(&config.refchat, client_username, "".into())
        .await
        .expect("Could not connect to chat server");
    chat_client
        .wait_until_ready()
        .await
        .expect("An error occurred while waiting for full connection to chat server");
    let (chat_sender, chat_receiver) = chat_client
        .split()
        .expect("Could not split chat connection");
    let (sender, receiver) = socket.split();
    let refchat_interface = RefchatInterface::new(
        sender.into(),
        chat_sender.get_username().to_string(),
        tera::Context::new(),
    );
    let _chat_thread = tokio::spawn(handle_chat(refchat_interface.clone(), chat_receiver));
    if let Err(err) = refchat_interface
        .listen(&mut receiver.into(), &chat_sender)
        .await
    {
        match err {
            RefchatError::Disconnected(_) => {}
            err => panic!("Could not listen to interface events: {}", err),
        }
    }
}
