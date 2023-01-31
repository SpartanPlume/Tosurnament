# discord endpoints
# # discord api endpoints
DISCORD_API = "https://discord.com/api/v9"
DISCORD_ME = DISCORD_API + "/users/@me"
DISCORD_ME_GUILDS = DISCORD_ME + "/guilds"
DISCORD_GUILDS = DISCORD_API + "/guilds"
DISCORD_GUILD = DISCORD_GUILDS + "/{0}"
DISCORD_GUILD_CHANNELS = DISCORD_GUILD + "/channels"
DISCORD_GUILD_ROLES = DISCORD_GUILD + "/roles"
DISCORD_GUILD_ROLE = DISCORD_GUILD_ROLES + "/{1}"
DISCORD_GUILD_MEMBERS = DISCORD_GUILD + "/members"
DISCORD_GUILD_MEMBER = DISCORD_GUILD_MEMBERS + "/{1}"

# # discord oauth2 endpoints
DISCORD_OAUTH2 = DISCORD_API + "/oauth2"
DISCORD_TOKEN = DISCORD_OAUTH2 + "/token"
DISCORD_TOKEN_REVOKE = DISCORD_TOKEN + "/revoke"

# osu! endpoints
# # osu! oauth2 endpoints
OSU_OAUTH2 = "https://osu.ppy.sh/oauth"
OSU_TOKEN = OSU_OAUTH2 + "/token"
OSU_TOKEN_REVOKE = OSU_TOKEN + "/revoke"

# # osu! api endpoints
OSU_API = "https://osu.ppy.sh/api/v2"
OSU_ME = OSU_API + "/me/osu"
