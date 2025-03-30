use crate::refchat::{
    error::{InvalidLoginError, RefchatError},
    WsSender,
};

#[derive(Clone, Debug)]
pub struct RefchatLoginDisplay {
    ws_sender: WsSender,
    tera_context: tera::Context,
}

impl RefchatLoginDisplay {
    pub fn new(ws_sender: WsSender, tera_context: tera::Context) -> Self {
        Self {
            ws_sender,
            tera_context,
        }
    }

    pub async fn show_login_wait(&self) -> Result<(), RefchatError> {
        let tera_context = self.tera_context.clone();
        self.ws_sender
            .send_html("refchat/login/login_wait.html", &tera_context)
            .await
    }

    pub async fn show_login_error(&self) -> RefchatError {
        let tera_context = self.tera_context.clone();
        if let Err(error) = self
            .ws_sender
            .send_html("refchat/login/login_error.html", &tera_context)
            .await
        {
            return error;
        }
        InvalidLoginError.into()
    }

    pub async fn reset(&self, username: &str) -> Result<(), RefchatError> {
        let mut tera_context = self.tera_context.clone();
        tera_context.insert("username", username);
        self.ws_sender
            .send_html("refchat/login/login.html", &tera_context)
            .await
    }
}
