use crate::{
    refchat::{
        context::{Channel, ChannelTab, ChatMessage},
        error::RefchatError,
        WsSender,
    },
    TEMPLATES,
};

#[derive(Clone, Debug)]
pub struct RefchatDisplay {
    ws_sender: WsSender,
    tera_context: tera::Context,
}

impl RefchatDisplay {
    pub fn new(ws_sender: WsSender, tera_context: tera::Context) -> Self {
        Self {
            ws_sender,
            tera_context,
        }
    }

    pub async fn reset(&self) -> Result<(), RefchatError> {
        self.ws_sender
            .send_html("refchat/start_refchat.html", &self.tera_context)
            .await
    }

    pub async fn show_channels(
        &self,
        channels: &Vec<Channel>,
        current_channel_name: &str,
    ) -> Result<(), RefchatError> {
        let mut tera_context = self.tera_context.clone();
        tera_context.insert("channels", channels);
        tera_context.insert("current_channel_name", current_channel_name);
        self.ws_sender
            .send_html("refchat/channel/show_channels.html", &tera_context)
            .await
    }

    pub async fn select_channel(
        &self,
        channel: &Channel,
        previous_channel: &Option<&Channel>,
    ) -> Result<(), RefchatError> {
        let tera_context = self.prepare_channel_change(channel, previous_channel);
        self.ws_sender
            .send_html("refchat/channel/select_channel.html", &tera_context)
            .await
    }

    pub async fn add_channel(
        &self,
        channel: &Channel,
        previous_channel: &Option<&Channel>,
    ) -> Result<(), RefchatError> {
        let tera_context = self.prepare_channel_change(channel, previous_channel);
        self.ws_sender
            .send_html("refchat/channel/add_channel.html", &tera_context)
            .await
    }

    fn prepare_channel_change(
        &self,
        channel: &Channel,
        previous_channel: &Option<&Channel>,
    ) -> tera::Context {
        let mut tera_context = self.tera_context.clone();
        tera_context.insert("channel", channel);
        if let Some(previous_channel) = previous_channel {
            tera_context.insert("previous_channel", previous_channel);
        } else {
            tera_context.insert("hide_new_channel_selection", &true);
        }
        tera_context
    }

    pub async fn show_new_channel_selection(
        &self,
        previous_channel: &Channel,
    ) -> Result<(), RefchatError> {
        let mut tera_context = self.tera_context.clone();
        tera_context.insert("previous_channel", &previous_channel);
        self.ws_sender
            .send_html(
                "refchat/channel/show_new_channel_selection.html",
                &tera_context,
            )
            .await
    }

    pub async fn add_message(&self, message: &ChatMessage) -> Result<(), RefchatError> {
        let mut tera_context = self.tera_context.clone();
        tera_context.insert("message", message);

        let template_page = "refchat/channel/chat/add_message.html";
        let page = TEMPLATES.render(template_page, &tera_context)?;

        // TODO: replace map acronyms by html to hover on them
        // let page = page.replace("NM1", r#"<div class="refchat_message_map_highlight">NM1<div class="refchat_message_map">Welcome</div></div>"#);
        self.ws_sender.send_text(page).await
    }

    pub async fn change_chat_input(&self, text: &str) -> Result<(), RefchatError> {
        let mut tera_context = self.tera_context.clone();
        tera_context.insert("input_text", text);
        self.ws_sender
            .send_html("refchat/channel/chat/input.html", &tera_context)
            .await
    }

    pub async fn update_helper_tab(&self, tab: &ChannelTab) -> Result<(), RefchatError> {
        let mut tera_context = self.tera_context.clone();
        tera_context.insert("tab", tab);
        self.ws_sender
            .send_html("refchat/channel/tab/show_tab_content.html", &tera_context)
            .await?;
        Ok(())
    }

    pub async fn select_channel_helper_tab(
        &self,
        tab: &ChannelTab,
        previous_tab: &ChannelTab,
    ) -> Result<(), RefchatError> {
        let mut tera_context = self.tera_context.clone();
        tera_context.insert("tab", tab);
        tera_context.insert("previous_tab", previous_tab);
        self.ws_sender
            .send_html("refchat/channel/tab/select_tab.html", &tera_context)
            .await
    }
}
