"""Contains all tournament settings commands related to Tosurnament."""

import re
import discord
from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.databases.bracket import Bracket


class TosurnamentTournamentCog(tosurnament.TosurnamentBaseModule, name="tournament"):
    """Tosurnament tournament settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):  # pragma: no cover
        """Check function called before any command of the cog."""
        return self.admin_cog_check(ctx)

    @commands.command(aliases=["stn"])  # pragma: no cover
    async def set_tournament_name(self, ctx, *, name: str):
        """Sets the tournament name."""
        await self.set_tournament_values(ctx, {"name": name})

    @commands.command(aliases=["cb"])
    async def create_bracket(self, ctx, *, name: str):
        """Creates a bracket and sets it as current bracket (for bracket settings purpose)."""
        tournament = self.get_tournament(ctx.guild.id)
        bracket = Bracket(tournament_id=tournament.id, name=name)
        self.bot.session.add(bracket)
        tournament.current_bracket_id = bracket.id
        self.bot.session.update(tournament)
        await self.send_reply(ctx, ctx.command.name, "success", name)

    @commands.command(aliases=["get_brackets", "gb"])
    async def get_bracket(self, ctx, *, number: int = None):
        """Sets a bracket as current bracket or shows them all."""
        tournament = self.get_tournament(ctx.guild.id)
        brackets = tournament.brackets
        if number or number == 0:
            number -= 1
            if not (number >= 0 and number < len(brackets)):
                raise commands.UserInputError()
            tournament.current_bracket_id = brackets[number].id
            self.bot.session.update(tournament)
            await self.send_reply(ctx, ctx.command.name, "success", brackets[number].name)
        else:
            brackets_string = ""
            for i, bracket in enumerate(brackets):
                brackets_string += str(i + 1) + ": `" + bracket.name + "`"
                if bracket.id == tournament.current_bracket_id:
                    brackets_string += " (current bracket)"
                brackets_string += "\n"
            await self.send_reply(ctx, ctx.command.name, "default", brackets_string)

    @commands.command(aliases=["ssc"])  # pragma: no cover
    async def set_staff_channel(self, ctx, *, channel: discord.TextChannel):
        """Sets the staff channel."""
        await self.set_tournament_values(ctx, {"staff_channel_id": channel.id})

    @commands.command(aliases=["smnc"])  # pragma: no cover
    async def set_match_notification_channel(self, ctx, *, channel: discord.TextChannel):
        """Sets the match notification channel."""
        await self.set_tournament_values(ctx, {"match_notification_channel_id": channel.id})

    @commands.command(aliases=["srr"])  # pragma: no cover
    async def set_referee_role(self, ctx, *, role: discord.Role):
        """Sets the referee role."""
        await self.set_tournament_values(ctx, {"referee_role_id": role.id})

    @commands.command(aliases=["ssr"])  # pragma: no cover
    async def set_streamer_role(self, ctx, *, role: discord.Role):
        """Sets the streamer role."""
        await self.set_tournament_values(ctx, {"streamer_role_id": role.id})

    @commands.command(aliases=["scr"])  # pragma: no cover
    async def set_commentator_role(self, ctx, *, role: discord.Role):
        """Sets the commentator role."""
        await self.set_tournament_values(ctx, {"commentator_role_id": role.id})

    @commands.command(aliases=["spr"])  # pragma: no cover
    async def set_player_role(self, ctx, *, role: discord.Role):
        """Sets the player role."""
        await self.set_tournament_values(ctx, {"player_role_id": role.id})

    @commands.command(aliases=["stcr", "set_team_leader_role", "stlr"])
    async def set_team_captain_role(self, ctx, *, role: discord.Role = None):
        """Sets the team captain role."""
        if not role:
            await self.set_tournament_values(ctx, {"team_captain_role_id": 0})
        else:
            await self.set_tournament_values(ctx, {"team_captain_role_id": role.id})

    @commands.command(aliases=["spt"])  # pragma: no cover
    async def set_ping_team(self, ctx, ping_team: bool):
        """Sets if team should be pinged or team captain should be pinged."""
        await self.set_tournament_values(ctx, {"reschedule_ping_team": ping_team})

    @commands.command(aliases=["sprm"])  # pragma: no cover
    async def set_post_result_message(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message": message})

    @commands.command(aliases=["sprmt1ws"])  # pragma: no cover
    async def set_post_result_message_team1_with_score(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message_team1_with_score": message})

    @commands.command(aliases=["sprmt2ws"])  # pragma: no cover
    async def set_post_result_message_team2_with_score(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message_team2_with_score": message})

    @commands.command(aliases=["sprmml"])  # pragma: no cover
    async def set_post_result_message_mp_link(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message_mp_link": message})

    @commands.command(aliases=["sprmr"])  # pragma: no cover
    async def set_post_result_message_rolls(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message_rolls": message})

    @commands.command(aliases=["sprmb"])  # pragma: no cover
    async def set_post_result_message_bans(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message_bans": message})

    @commands.command(aliases=["sprmtb"])  # pragma: no cover
    async def set_post_result_message_tb_bans(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message_tb_bans": message})

    @commands.command(aliases=["srdhbct"])  # pragma: no cover
    async def set_reschedule_deadline_hours_before_current_time(self, ctx, hours: int):
        """Allows to change the deadline (in hours) before the current match time to reschedule a match."""
        await self.set_tournament_values(ctx, {"reschedule_deadline_hours_before_current_time": hours})

    @commands.command(aliases=["srdhbnt"])  # pragma: no cover
    async def set_reschedule_deadline_hours_before_new_time(self, ctx, hours: int):
        """Allows to change the deadline (in hours) before the new match time to reschedule a match."""
        await self.set_tournament_values(ctx, {"reschedule_deadline_hours_before_new_time": hours})

    @commands.command(aliases=["srde"])
    async def set_reschedule_deadline_end(self, ctx, *, date: str = ""):
        if date:
            date = date.lower()
            if not re.match(
                r"^(monday|tuesday|wednesday|thursday|friday|saturday|sunday) ([0-2][0-3]|[0-1][0-9]):[0-5][0-9]$", date
            ):
                raise commands.UserInputError()
        await self.set_tournament_values(ctx, {"reschedule_deadline_end": date})

    @commands.command(aliases=["snnsr"])  # pragma: no cover
    async def set_notify_no_staff_reschedule(self, ctx, notify: bool):
        await self.set_tournament_values(ctx, {"notify_no_staff_reschedule": notify})

    async def set_tournament_values(self, ctx, values):
        """Puts the input values into the corresponding tournament."""
        tournament = self.get_tournament(ctx.guild.id)
        for key, value in values.items():
            setattr(tournament, key, value)
        self.bot.session.update(tournament)
        await self.send_reply(ctx, ctx.command.name, "success", value)

    @commands.command(aliases=["amti", "add_matches_to_ignore"])
    async def add_match_to_ignore(self, ctx, *match_ids):
        """Adds matches in the list of matches to ignore in other commands."""
        await self.add_or_remove_match_to_ignore(ctx, match_ids, True)

    @commands.command(aliases=["rmti", "remove_matches_to_ignore"])
    async def remove_match_to_ignore(self, ctx, *match_ids):
        """Removes matches in the list of matches to ignore in other commands."""
        await self.add_or_remove_match_to_ignore(ctx, match_ids, False)

    async def add_or_remove_match_to_ignore(self, ctx, match_ids, add):
        """Removes matches in the list of matches to ignore in other commands."""
        tournament = self.get_tournament(ctx.guild.id)
        matches_to_ignore = [match_id.upper() for match_id in tournament.matches_to_ignore.split("\n")]
        for match_id in match_ids:
            match_id_upper = match_id.upper()
            if add and match_id_upper not in matches_to_ignore:
                matches_to_ignore.append(match_id_upper)
            elif not add and match_id_upper in matches_to_ignore:
                matches_to_ignore.remove(match_id_upper)
        matches_to_ignore.sort()
        tournament.matches_to_ignore = "\n".join(matches_to_ignore)
        self.bot.session.update(tournament)
        await self.send_reply(ctx, ctx.command.name, "success", " ".join(matches_to_ignore))


def get_class(bot):
    """Returns the main class of the module."""
    return TosurnamentTournamentCog(bot)


def setup(bot):  # pragma: no cover
    """Setups the cog."""
    bot.add_cog(TosurnamentTournamentCog(bot))
