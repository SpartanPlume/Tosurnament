"""Contains all tournament settings commands related to Tosurnament."""

import re
import os
import uuid
import dateparser
import discord
from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.databases.tosurnament.bracket import Bracket
from common.api import tosurnament as tosurnament_api

DAY_REGEX = r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
TIME_REGEX = r"([0-2][0-3]|[0-1][0-9]):[0-5][0-9]"


class TosurnamentTournamentCog(tosurnament.TosurnamentBaseModule, name="tournament"):
    """Tosurnament tournament settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        """Check function called before any command of the cog."""
        return self.admin_cog_check(ctx)

    @commands.command(aliases=["stn"])
    async def set_tournament_name(self, ctx, *, name: str):
        """Sets the tournament's name."""
        await self.set_tournament_values(ctx, {"name": name})

    @commands.command(aliases=["sta"])
    async def set_tournament_acronym(self, ctx, *, acronym: str):
        """Sets the tournament's acronym."""
        await self.set_tournament_values(ctx, {"acronym": acronym})

    @commands.command(aliases=["cb"])
    async def create_bracket(self, ctx, *, name: str):
        """Creates a bracket and sets it as current bracket (for bracket settings purpose)."""
        tournament = self.get_tournament(ctx.guild.id)
        bracket = Bracket(tournament_id=tournament.id, name=name)
        bracket = tosurnament_api.create_bracket(tournament.id, bracket)
        tournament.current_bracket_id = bracket.id
        tournament = tosurnament_api.update_tournament(tournament)
        await self.send_reply(ctx, "success", name)

    @commands.command(aliases=["get_brackets", "gb"])
    async def get_bracket(self, ctx, *, number: int = None):
        """Sets a bracket as current bracket or shows them all."""
        tournament = self.get_tournament(ctx.guild.id)
        bracket = self.get_bracket_from_index(tournament.brackets, number)
        if bracket:
            tournament.current_bracket_id = bracket.id
            tosurnament_api.update_tournament(tournament)
            await self.send_reply(ctx, "success", bracket.name)
        else:
            brackets_string = ""
            for i, bracket in enumerate(tournament.brackets):
                brackets_string += str(i + 1) + ": `" + bracket.name + "`"
                if bracket.id == tournament.current_bracket_id:
                    brackets_string += " " + self.get_string(ctx, "current_bracket_indicator")
                brackets_string += "\n"
            await self.send_reply(ctx, "default", brackets_string)

    @commands.command(aliases=["ssc"])
    async def set_staff_channel(self, ctx, *, channel: discord.TextChannel):
        """Sets the staff channel."""
        await self.set_tournament_values(ctx, {"staff_channel_id": str(channel.id)})

    @commands.command(aliases=["smnc"])
    async def set_match_notification_channel(self, ctx, *, channel: discord.TextChannel):
        """Sets the match notification channel."""
        await self.set_tournament_values(ctx, {"match_notification_channel_id": str(channel.id)})

    @commands.command(aliases=["srr"])
    async def set_referee_role(self, ctx, *, role: discord.Role):
        """Sets the referee role."""
        await self.set_tournament_values(ctx, {"referee_role_id": str(role.id)})

    @commands.command(aliases=["ssr"])
    async def set_streamer_role(self, ctx, *, role: discord.Role):
        """Sets the streamer role."""
        await self.set_tournament_values(ctx, {"streamer_role_id": str(role.id)})

    @commands.command(aliases=["scr"])
    async def set_commentator_role(self, ctx, *, role: discord.Role):
        """Sets the commentator role."""
        await self.set_tournament_values(ctx, {"commentator_role_id": str(role.id)})

    @commands.command(aliases=["spr"])
    async def set_player_role(self, ctx, *, role: discord.Role):
        """Sets the player role."""
        await self.set_tournament_values(ctx, {"player_role_id": str(role.id)})

    @commands.command(aliases=["stcr", "set_team_leader_role", "stlr"])
    async def set_team_captain_role(self, ctx, *, role: discord.Role = None):
        """Sets the team captain role."""
        if not role:
            await self.set_tournament_values(ctx, {"team_captain_role_id": 0})
        else:
            await self.set_tournament_values(ctx, {"team_captain_role_id": str(role.id)})

    @commands.command(aliases=["spt"])
    async def set_ping_team(self, ctx, ping_team: bool):
        """Sets if team should be pinged or team captain should be pinged."""
        await self.set_tournament_values(ctx, {"reschedule_ping_team": ping_team})

    @commands.command(aliases=["sprm"])
    async def set_post_result_message(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message": message})

    @commands.command(aliases=["sprmt1ws"])
    async def set_post_result_message_team1_with_score(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message_team1_with_score": message})

    @commands.command(aliases=["sprmt2ws"])
    async def set_post_result_message_team2_with_score(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message_team2_with_score": message})

    @commands.command(aliases=["sprmml"])
    async def set_post_result_message_mp_link(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message_mp_link": message})

    @commands.command(aliases=["sprmr"])
    async def set_post_result_message_rolls(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message_rolls": message})

    @commands.command(aliases=["sprmb"])
    async def set_post_result_message_bans(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message_bans": message})

    @commands.command(aliases=["sprmtb"])
    async def set_post_result_message_tb_bans(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message_tb_bans": message})

    @commands.command(aliases=["srbu"])
    async def set_registration_background_update(self, ctx, *, boolean: bool):
        """Sets whether the registration update background task should be run."""
        await self.set_tournament_values(ctx, {"registration_background_update": boolean})

    @commands.command(aliases=["srdhbct"])
    async def set_reschedule_deadline_hours_before_current_time(self, ctx, hours: int):
        """Allows to change the deadline (in hours) before the current match time to reschedule a match."""
        await self.set_tournament_values(ctx, {"reschedule_deadline_hours_before_current_time": hours})

    @commands.command(aliases=["srdhbnt"])
    async def set_reschedule_deadline_hours_before_new_time(self, ctx, hours: int):
        """Allows to change the deadline (in hours) before the new match time to reschedule a match."""
        await self.set_tournament_values(ctx, {"reschedule_deadline_hours_before_new_time": hours})

    @commands.command(aliases=["srde"])
    async def set_reschedule_deadline_end(self, ctx, *, date: str = ""):
        if date:
            date = date.lower()
            if not re.match(
                r"^" + DAY_REGEX + r" " + TIME_REGEX + r"$",
                date,
            ):
                raise commands.UserInputError()
        await self.set_tournament_values(ctx, {"reschedule_deadline_end": date})

    @commands.command(aliases=["srbd"])
    async def set_reschedule_before_date(self, ctx, *, date: str = ""):
        if date:
            date = date.lower()
            if not re.match(
                r"^" + DAY_REGEX + r" " + TIME_REGEX + r"$",
                date,
            ):
                raise commands.UserInputError()
        await self.set_tournament_values(ctx, {"reschedule_before_date": date})

    @commands.command(aliases=["sdf"])
    async def set_date_format(self, ctx, *, date_format: str = ""):
        """Sets the date format used in the date range of the schedules/qualifiers spreadsheet."""
        await self.set_tournament_values(ctx, {"date_format": date_format})

    @commands.command(aliases=["snnsr"])
    async def set_notify_no_staff_reschedule(self, ctx, notify: bool):
        await self.set_tournament_values(ctx, {"notify_no_staff_reschedule": notify})

    @commands.command(aliases=["su"])
    async def set_utc(self, ctx, utc: str):
        if utc:
            if not re.match(r"^[-\+]" + TIME_REGEX + r"$", utc):
                raise commands.UserInputError()
            try:
                dateparser.parse("now", settings={"TIMEZONE": utc})
            except Exception:
                raise commands.UserInputError()  # TODO better exception
        await self.set_tournament_values(ctx, {"utc": utc})

    @commands.command(aliases=["srp"])
    async def set_registration_phase(self, ctx, boolean: bool):
        await self.set_tournament_values(ctx, {"registration_phase": boolean})

    @commands.command(aliases=["sgm"])
    async def set_game_mode(self, ctx, *, game_mode: str = None):
        if game_mode.lower() in ["0", "std", "standard"]:
            m = 0
        elif game_mode.lower() in ["1", "taiko"]:
            m = 1
        elif game_mode.lower() in ["2", "ctb", "catch the beat", "catchthebeat"]:
            m = 2
        elif game_mode.lower() in ["3", "mania"]:
            m = 3
        else:
            await self.send_reply(ctx, "default")
            return
        await self.set_tournament_values(ctx, {"game_mode": m})

    async def set_tournament_values(self, ctx, values):
        """Puts the input values into the corresponding tournament."""
        tournament = self.get_tournament(ctx.guild.id)
        for key, value in values.items():
            setattr(tournament, key, value)
        tosurnament_api.update_tournament(tournament)
        await self.send_reply(ctx, "success", value)
        await self.send_reply(ctx, "use_dashboard", ctx.guild.id)

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
        match_ids = {match_id.casefold(): match_id for match_id in match_ids}
        tournament = self.get_tournament(ctx.guild.id)
        matches_to_ignore = tournament.matches_to_ignore.split("\n")
        all_match_infos = []
        for bracket in tournament.brackets:
            all_match_infos.extend(await self.get_match_infos_from_id(bracket, match_ids.keys()))
        matches_found = []
        for match_info in all_match_infos:
            match_id = match_info.match_id.get()
            if add and match_id not in matches_to_ignore:
                matches_to_ignore.append(match_id)
            elif not add and match_id in matches_to_ignore:
                matches_to_ignore.remove(match_id)
            else:
                continue  # pragma: no cover
            matches_found.append(match_info)
            match_ids.pop(match_id.casefold())
        matches_to_ignore.sort()
        tournament.matches_to_ignore = "\n".join(matches_to_ignore)
        tosurnament_api.update_tournament(tournament)
        await self.send_reply(ctx, "success", " ".join(matches_to_ignore))
        matches_not_found = [match_id for match_id in match_ids.values()]
        if matches_not_found:
            await self.send_reply(ctx, "not_found", " ".join(matches_not_found))
        reply_type = "to_ignore"
        if not add:
            reply_type = "to_not_ignore"
        staff_channel = ctx
        if tournament.staff_channel_id:
            staff_channel = self.bot.get_channel(int(tournament.staff_channel_id))
        for match_info in matches_found:
            referees_to_ping, referees_not_found = self.find_staff_to_ping(ctx.guild, match_info.referees)
            streamers_to_ping, streamers_not_found = self.find_staff_to_ping(ctx.guild, match_info.streamers)
            commentators_to_ping, commentators_not_found = self.find_staff_to_ping(ctx.guild, match_info.commentators)
            staffs_to_ping = [
                *referees_to_ping,
                *streamers_to_ping,
                *commentators_to_ping,
            ]
            staffs_not_found = set([*referees_not_found, *streamers_not_found, *commentators_not_found])
            to_ping = "/".join([*set([staff.mention for staff in staffs_to_ping]), *staffs_not_found])
            await self.send_reply(ctx, reply_type, to_ping, match_info.match_id.get(), channel=staff_channel)

    @commands.command(aliases=["ss", "sync_spreadsheets"])
    async def sync_spreadsheet(self, ctx):
        tournament = self.get_tournament(ctx.guild.id)
        spreadsheet_ids = []
        for bracket in tournament.brackets:
            for spreadsheet_type in Bracket.get_spreadsheet_types().keys():
                spreadsheet = bracket.get_spreadsheet_from_type(spreadsheet_type)
                if not spreadsheet:
                    continue
                spreadsheet_id = spreadsheet.spreadsheet_id
                if spreadsheet_id not in spreadsheet_ids:
                    await spreadsheet.get_spreadsheet(retry=True, force_sync=True)
                    spreadsheet_ids.append(spreadsheet_id)
        await self.send_reply(ctx, "success")

    @commands.command(aliases=["svts"])
    async def save_tournament_settings(self, ctx):
        """Saves the tournament settings and gives a code corresponding to it."""
        tournament = self.get_tournament(ctx.guild.id)
        if os.path.exists("tournament_templates"):
            if tournament.template_code and os.path.exists("tournament_templates/" + tournament.template_code):
                os.remove("tournament_templates/" + tournament.template_code)
        else:
            os.mkdir("tournament_templates")
        if not tournament.template_code:
            tournament.template_code = str(uuid.uuid4())
        settings_to_write = ""
        for key, value in vars(tournament).items():
            if key not in ["id", "template_code"] and not isinstance(value, bytes):
                settings_to_write += key + "=" + value + "\n"
        with open("tournament_templates/" + tournament.template_code) as f:
            f.write(settings_to_write)
        await self.send_reply(ctx, "success", tournament.template_code)

    @save_tournament_settings.error
    async def save_tournament_settings_handler(self, ctx, error):
        """Error handler of save_tournament_settings function."""
        if isinstance(error, OSError):
            self.log.error("The tournament template file could not be created or deleted.")
            await self.send_reply(ctx, "OSError")

    @commands.command(aliases=["sts"])
    async def show_tournament_settings(self, ctx):
        """Shows the tournament settings."""
        tournament = self.get_tournament(ctx.guild.id)
        await self.show_object_settings(ctx, tournament, stack_depth=2)


def get_class(bot):
    """Returns the main class of the module."""
    return TosurnamentTournamentCog(bot)


def setup(bot):
    """Setups the cog."""
    bot.add_cog(TosurnamentTournamentCog(bot))
