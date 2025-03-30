mod chat;
mod context;
mod error;
mod interface;
mod ws_receiver;
mod ws_sender;

use axum::extract::ws::{self as axum_ws};
use futures::stream::StreamExt;

use crate::config::RefchatConfig;
use ws_receiver::WsReceiver;
use ws_sender::WsSender;

pub use chat::handle_chat;
pub use chat::{ChatClient, ChatEvent, ChatReceiver, ChatSender};
pub use error::RefchatError;
pub use interface::{login::RefchatLoginInterface, RefchatInterface};

pub async fn handle_socket(
    socket: axum_ws::WebSocket,
    tera_context: tera::Context,
    refchat_config: RefchatConfig,
) {
    let (sender, receiver) = socket.split();
    let sender = WsSender::new(sender);
    let mut receiver = WsReceiver::new(receiver);

    let mut login_interface = RefchatLoginInterface::new(
        sender.clone(),
        refchat_config,
        "User".to_owned(),
        tera_context.clone(),
    );
    if let Err(error) = login_interface.reset_display().await {
        tracing::error!("Could not reset login interface display: {}", error);
    }

    match login_interface.listen(&mut receiver).await {
        Ok(chat_client) => {
            let interface =
                RefchatInterface::new(sender, chat_client.get_username().to_owned(), tera_context);
            if let Err(error) = interface.reset_display().await {
                tracing::error!("Could not reset interface display: {}", error);
            }
            match chat_client.split() {
                Ok((chat_sender, chat_receiver)) => {
                    let chat_thread = tokio::spawn(handle_chat(interface.clone(), chat_receiver));
                    if let Err(error) = interface.listen(&mut receiver, &chat_sender).await {
                        error.trace();
                    }
                    chat_thread.abort();
                }
                Err(error) => {
                    tracing::error!("Could not split chat client: {}", error);
                }
            }
        }
        Err(error) => {
            error.trace();
        }
    }
}
