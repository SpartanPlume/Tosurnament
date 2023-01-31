"""Contains all commands executable by the owner of the bot."""

from discord.ext import commands
from bot.modules import module as base
from common.api import tosurnament as tosurnament_api
from common.databases.tosurnament.user import User


class OwnerCog(base.BaseModule, name="owner"):
    """Owner commands."""

    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if ctx.author.id != self.bot.owner_id:
            raise commands.NotOwner()
        return True

    @commands.command(hidden=True)
    async def stop(self, ctx):
        """Stops the bot."""
        await self.bot.stop(0, ctx)

    @commands.command(hidden=True)
    async def update(self, ctx):
        """Updates the bot."""
        await self.bot.stop(42, ctx)

    @commands.command(hidden=True)
    async def restart(self, ctx):
        """Restarts the bot."""
        await self.bot.stop(43, ctx)

    @commands.command(hidden=True)
    async def ping(self, ctx):
        """Pings the bot."""
        await ctx.send("pong")

    @commands.command(hidden=True)
    async def say(self, ctx, *args):
        """Bot says the input."""
        await ctx.send(" ".join(args))

    @commands.command(hidden=True)
    async def add_verified_user(self, ctx, discord_id: str, osu_id: str, *, osu_name: str):
        """Add a verified user to the database (to use when someone can't use the website, because of parental controls for example)."""
        user = self.get_user(discord_id)
        if user and user.verified:
            await ctx.send("User is already verified")
            return
        if user:
            user.verified = True
            user.discord_id = discord_id
            user.discord_id_snowflake = discord_id
            user.osu_id = osu_id
            user.osu_name = osu_name
            user.osu_name_hash = osu_name
            tosurnament_api.update_user(user)
        else:
            user = User(
                verified=True,
                discord_id=discord_id,
                discord_id_snowflake=discord_id,
                osu_id=osu_id,
                osu_name=osu_name,
                osu_name_hash=osu_name,
            )
            tosurnament_api.create_user(user)
        await ctx.send(osu_name + " has been added as a verified user")

    @commands.command(hidden=True)
    async def check_user_info(self, ctx, discord_id: str):
        """Checks the information of a User."""
        user = self.get_user(discord_id)
        if user:
            output = ""
            for key, value in user.get_api_dict().items():
                value = str(value)
                if not value:
                    value = self.get_string(ctx, "undefined")
                tmp_output = "__" + key + "__: `" + value + "`\n"
                if len(output + tmp_output) >= 2000:
                    await ctx.send(output)
                    output = tmp_output
                else:
                    output += tmp_output
            await ctx.send(output)
        else:
            await ctx.send("User not found")

    @commands.command(hidden=True)
    async def announce(self, ctx, *, message: str):
        """Sends an annoucement to all servers that have a tournament running."""
        users_already_sent_to = []
        for guild in self.bot.guilds:
            tournament = tosurnament_api.get_tournament_by_discord_guild_id(guild.id)
            if tournament:
                staff_channel = self.bot.get_channel(int(tournament.staff_channel_id))
                tosurnament_guild = self.get_guild(guild.id)
                admin_role = base.get_role(guild.roles, tosurnament_guild.admin_role_id, "Admin")
                if admin_role:
                    admin_role_mention = admin_role.mention
                else:
                    admin_role_mention = guild.owner.mention
                try:
                    if staff_channel:
                        await staff_channel.send(admin_role_mention + "\n\n" + message)
                        continue
                except Exception:
                    pass
            if guild.owner.id not in users_already_sent_to:
                try:
                    await guild.owner.send(message)
                    users_already_sent_to.append(guild.owner.id)
                except Exception:
                    continue


async def setup(bot):
    """Setups the cog."""
    await bot.add_cog(OwnerCog(bot))
