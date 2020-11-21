"""Contains all tournament settings commands related to Tosurnament."""

import re
import dateparser
import discord
from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.databases.bracket import Bracket

TIME_REGEX = r"([0-2][0-3]|[0-1][0-9]):[0-5][0-9]"


class TosurnamentTournamentCog(tosurnament.TosurnamentBaseModule, name="tournament"):
    """Tosurnament tournament settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        """Check function called before any command of the cog."""
        return self.admin_cog_check(ctx)

    @commands.command(aliases=["stn"])  # pragma: no cover
    async def set_tournament_name(self, ctx, *, name: str):
        """Sets the tournament name."""
        await self.set_tournament_values(ctx, {"name": name})

    @commands.command(aliases=["sta"])  # pragma: no cover
    async def set_tournament_acronym(self, ctx, *, acronym: str):
        """Sets the tournament acronym."""
        await self.set_tournament_values(ctx, {"acronym": acronym})

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
            await self.send_reply(
                ctx, ctx.command.name, "success", brackets[number].name
            )
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
    async def set_match_notification_channel(
        self, ctx, *, channel: discord.TextChannel
    ):
        """Sets the match notification channel."""
        await self.set_tournament_values(
            ctx, {"match_notification_channel_id": channel.id}
        )

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
        await self.set_tournament_values(
            ctx, {"post_result_message_team1_with_score": message}
        )

    @commands.command(aliases=["sprmt2ws"])  # pragma: no cover
    async def set_post_result_message_team2_with_score(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(
            ctx, {"post_result_message_team2_with_score": message}
        )

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
        await self.set_tournament_values(
            ctx, {"reschedule_deadline_hours_before_current_time": hours}
        )

    @commands.command(aliases=["srdhbnt"])  # pragma: no cover
    async def set_reschedule_deadline_hours_before_new_time(self, ctx, hours: int):
        """Allows to change the deadline (in hours) before the new match time to reschedule a match."""
        await self.set_tournament_values(
            ctx, {"reschedule_deadline_hours_before_new_time": hours}
        )

    @commands.command(aliases=["srde"])
    async def set_reschedule_deadline_end(self, ctx, *, date: str = ""):
        if date:
            date = date.lower()
            if not re.match(
                r"^(monday|tuesday|wednesday|thursday|friday|saturday|sunday) "
                + TIME_REGEX
                + r"$",
                date,
            ):
                raise commands.UserInputError()
        await self.set_tournament_values(ctx, {"reschedule_deadline_end": date})

    @commands.command(aliases=["snnsr"])  # pragma: no cover
    async def set_notify_no_staff_reschedule(self, ctx, notify: bool):
        await self.set_tournament_values(ctx, {"notify_no_staff_reschedule": notify})

    @commands.command(aliases=["su"])  # pragma: no cover
    async def set_utc(self, ctx, utc: str):
        if utc:
            if not re.match(r"^[-\+]" + TIME_REGEX + r"$", utc):
                raise commands.UserInputError()
            try:
                dateparser.parse("now", settings={"TIMEZONE": utc})
            except Exception:
                raise commands.UserInputError()  # TODO better exception
        await self.set_tournament_values(ctx, {"utc": utc})

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
        match_ids = set([match_id.lower() for match_id in match_ids])
        tournament = self.get_tournament(ctx.guild.id)
        matches_to_ignore = tournament.matches_to_ignore.split("\n")
        all_match_infos = []
        for bracket in tournament.brackets:
            all_match_infos.extend(
                await self.get_match_infos_from_id(bracket, match_ids)
            )
        user_role_referee = tosurnament.UserDetails.Role()
        for match_info in all_match_infos:
            if add and match_info.match_id.value not in matches_to_ignore:
                matches_to_ignore.append(match_info.match_id.value)
                user_role_referee.taken_matches.append((match_info))
            elif not add and match_info.match_id.value in matches_to_ignore:
                matches_to_ignore.remove(match_info.match_id.value)
                user_role_referee.taken_matches.append((match_info))
        matches_to_ignore.sort()
        tournament.matches_to_ignore = "\n".join(matches_to_ignore)
        self.bot.session.update(tournament)
        await self.send_reply(
            ctx, ctx.command.name, "success", " ".join(matches_to_ignore)
        )
        if match_ids:
            await self.send_reply(
                ctx, ctx.command.name, "not_found", " ".join(match_ids)
            )
        reply_type = "to_ignore"
        if not add:
            reply_type = "to_not_ignore"
        staff_channel = ctx
        if tournament.staff_channel_id:
            staff_channel = self.bot.get_channel(tournament.staff_channel_id)
        for match_info in user_role_referee.taken_matches:
            referees_to_ping, referees_not_found = self.find_staff_to_ping(
                ctx.guild, match_info.referees
            )
            streamers_to_ping, streamers_not_found = self.find_staff_to_ping(
                ctx.guild, match_info.streamers
            )
            commentators_to_ping, commentators_not_found = self.find_staff_to_ping(
                ctx.guild, match_info.commentators
            )
            staffs_to_ping = [
                *referees_to_ping,
                *streamers_to_ping,
                *commentators_to_ping,
            ]
            staffs_not_found = set(
                [*referees_not_found, *streamers_not_found, *commentators_not_found]
            )
            to_ping = "/".join(
                [*set([staff.mention for staff in staffs_to_ping]), *staffs_not_found]
            )
            await self.send_reply(
                staff_channel,
                ctx.command.name,
                reply_type,
                to_ping,
                match_info.match_id.value,
            )

    async def sync_a_spreadsheet(self, spreadsheet, spreadsheet_ids):
        spreadsheet_id = spreadsheet.spreadsheet_id
        if spreadsheet_id not in spreadsheet_ids:
            await spreadsheet.get_spreadsheet(retry=True, force_sync=True)
            spreadsheet_ids.append(spreadsheet_id)

    @commands.command(aliases=["ss", "sync_spreadsheets"])
    async def sync_spreadsheet(self, ctx):
        tournament = self.get_tournament(ctx.guild.id)
        spreadsheet_ids = []
        for bracket in tournament.brackets:
            if bracket.schedules_spreadsheet:
                await self.sync_a_spreadsheet(
                    bracket.schedules_spreadsheet, spreadsheet_ids
                )
            if bracket.players_spreadsheet:
                await self.sync_a_spreadsheet(
                    bracket.schedules_spreadsheet, spreadsheet_ids
                )
        await self.send_reply(ctx, ctx.command.name, "success")


def get_class(bot):
    """Returns the main class of the module."""
    return TosurnamentTournamentCog(bot)


def setup(bot):
    """Setups the cog."""
    bot.add_cog(TosurnamentTournamentCog(bot))
