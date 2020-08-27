"""Contains all bracket settings commands related to Tosurnament."""

import discord
from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.api import spreadsheet
from common.api import challonge
from common.databases.players_spreadsheet import TeamInfo
from common.databases.bracket import Bracket


class TosurnamentBracketCog(tosurnament.TosurnamentBaseModule, name="bracket"):
    """Tosurnament bracket settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        """Check function called before any command of the cog."""
        return self.admin_cog_check(ctx)

    @commands.command(aliases=["sbn"])  # pragma: no cover
    async def set_bracket_name(self, ctx, *, name: str):
        """Modifies the current bracket's name."""
        await self.set_bracket_values(ctx, {"name": name})

    @commands.command(aliases=["sbr"])  # pragma: no cover
    async def set_bracket_role(self, ctx, *, role: discord.Role):
        """Modifies the current bracket's role."""
        await self.set_bracket_values(ctx, {"role_id": role.id})

    @commands.command(aliases=["scbr"])  # pragma: no cover
    async def set_current_bracket_round(self, ctx, *, current_round: str = ""):
        """Sets the round of the current bracket."""
        await self.set_bracket_values(ctx, {"current_round": current_round})

    @commands.command(aliases=["sprc"])  # pragma: no cover
    async def set_post_result_channel(self, ctx, *, channel: discord.TextChannel):
        """Sets the post result's channel."""
        await self.set_bracket_values(ctx, {"post_result_channel_id": channel.id})

    @commands.command(aliases=["sc"])
    async def set_challonge(self, ctx, challonge_tournament: str):
        """Sets the challonge."""
        challonge_tournament = challonge.extract_tournament_id(challonge_tournament)
        await self.set_bracket_values(ctx, {"challonge": challonge_tournament})

    def is_player_in_challonge(self, member, teams_info, participants):
        user = tosurnament.UserAbstraction.get_from_user(self.bot, member)
        if teams_info:
            for team_info in teams_info:
                if (user.verified and user.name.lower() in [cell.value for cell in team_info.players]) or (
                    str(member) in [cell.value for cell in team_info.discord]
                ):
                    if team_info.team_name.value.lower() in participants:
                        return team_info.team_name.value
                    else:
                        return None
        elif user.verified and user.name.lower() in participants:
            return user.name
        return None

    @commands.command(aliases=["cpr"])
    async def clear_player_role(self, ctx, bracket_index: int = None, remove_player_role: bool = True):
        """Removes the player role of users not present in the challonge."""
        tournament = self.get_tournament(ctx.guild.id)
        brackets = tournament.brackets
        if len(brackets) != 1:
            if bracket_index is None:
                brackets_string = ""
                for i, bracket in enumerate(brackets):
                    brackets_string += str(i + 1) + ": `" + bracket.name + "`\n"
                await self.send_reply(ctx, "clear_player_role", "default", brackets_string)
                return
            elif bracket_index <= 0 or bracket_index > len(brackets):
                raise commands.UserInputError()
            bracket_index -= 1
        else:
            bracket_index = 0
        bracket = brackets[bracket_index]
        if not bracket.challonge:
            raise tosurnament.NoChallonge(bracket.name)
        player_role = tosurnament.get_role(ctx.guild.roles, tournament.player_role_id, "Player")
        bracket_role = tosurnament.get_role(ctx.guild.roles, bracket.role_id, bracket.name)
        team_captain_role = tosurnament.get_role(ctx.guild.roles, tournament.team_captain_role_id, "Team Captain")
        if remove_player_role:
            roles_to_removes = list(filter(None, [player_role, bracket_role, team_captain_role]))
        else:
            roles_to_removes = list(filter(None, [bracket_role, team_captain_role]))

        challonge_tournament = challonge.get_tournament(bracket.challonge)
        participants = [participant.name for participant in challonge_tournament.participants]
        participants_lower = [participant.lower() for participant in participants]

        players_spreadsheet = bracket.players_spreadsheet
        teams_info = []
        if players_spreadsheet:
            await players_spreadsheet.get_spreadsheet()
            if players_spreadsheet.range_team_name:
                team_cells = players_spreadsheet.spreadsheet.get_cells_with_value_in_range(
                    players_spreadsheet.range_team_name
                )
            else:
                team_cells = players_spreadsheet.spreadsheet.get_cells_with_value_in_range(
                    players_spreadsheet.range_team
                )
            teams_info = []
            for cell in team_cells:
                try:
                    team_info = TeamInfo.from_team_name(players_spreadsheet, cell.value)
                except Exception:
                    continue
                if players_spreadsheet.range_team_name:
                    if team_role := tosurnament.get_role(ctx.guild.roles, None, team_info.team_name.value):
                        roles_to_removes.append(team_role)
                teams_info.append(team_info)

        players_found = []
        n_user_roles_removed = 0
        users_role_not_removed = []
        for member in ctx.guild.members:
            if bracket_role:
                if not tosurnament.get_role(member.roles, bracket_role.id):
                    continue
            elif player_role and not tosurnament.get_role(member.roles, player_role.id):
                continue
            if player_name := self.is_player_in_challonge(member, teams_info, participants_lower):
                players_found.append(player_name.lower())
            else:
                if member:
                    try:
                        await member.remove_roles(*roles_to_removes)
                        n_user_roles_removed += 1
                    except Exception:
                        users_role_not_removed.append(str(member))

        success_extra = ""
        players_not_found = ""
        for participant in participants:
            if participant.lower() not in players_found:
                players_not_found += participant + "\n"
        players_not_found.strip("\n")
        if players_not_found:
            success_extra += self.get_string("clear_player_role", "players_not_found", players_not_found)
        if users_role_not_removed:
            success_extra += self.get_string(
                "clear_player_role", "users_role_not_removed", "\n".join(users_role_not_removed)
            )
        await self.send_reply(
            ctx, "clear_player_role", "success", bracket.name, n_user_roles_removed, len(players_found), success_extra,
        )

    @commands.command(aliases=["sps"])  # pragma: no cover
    async def set_players_spreadsheet(self, ctx, spreadsheet_id: str, *, sheet_name: str = ""):
        """Sets the players spreadsheet."""
        await self.set_bracket_spreadsheet(ctx, "players", spreadsheet_id, sheet_name)

    @commands.command(aliases=["sss"])  # pragma: no cover
    async def set_schedules_spreadsheet(self, ctx, spreadsheet_id: str, *, sheet_name: str = ""):
        """Sets the schedules spreadsheet."""
        await self.set_bracket_spreadsheet(ctx, "schedules", spreadsheet_id, sheet_name)

    async def set_bracket_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        for key, value in values.items():
            setattr(tournament.current_bracket, key, value)
        self.bot.session.update(tournament.current_bracket)
        await self.send_reply(ctx, ctx.command.name, "success", value)

    async def set_bracket_spreadsheet(self, ctx, spreadsheet_type, spreadsheet_id, sheet_name):
        """Puts the input spreadsheet into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        bracket = tournament.current_bracket
        spreadsheet_id = spreadsheet.extract_spreadsheet_id(spreadsheet_id)
        any_spreadsheet = bracket.get_spreadsheet_from_type(spreadsheet_type)
        if not any_spreadsheet:
            any_spreadsheet = bracket.create_spreadsheet_from_type(self.bot, spreadsheet_type)
        any_spreadsheet.spreadsheet_id = spreadsheet_id
        if sheet_name:
            any_spreadsheet.sheet_name = sheet_name
        self.bot.session.update(any_spreadsheet)
        await self.send_reply(ctx, ctx.command.name, "success", spreadsheet_id)

    @commands.command(aliases=["ssssn"])  # pragma: no cover
    async def set_schedules_spreadsheet_sheet_name(self, ctx, *, sheet_name: str = ""):
        """Sets the sheet name of the schedules spreadsheet."""
        await self.set_schedules_spreadsheet_values(ctx, {"sheet_name": sheet_name})

    @commands.command(aliases=["sssdf"])  # pragma: no cover
    async def set_schedules_spreadsheet_date_format(self, ctx, *, date_format: str = ""):
        """Sets the date format used in the date range of the schedules spreadsheet."""
        await self.set_schedules_spreadsheet_values(ctx, {"date_format": date_format})

    @commands.command(aliases=["ssssir"])  # pragma: no cover
    async def set_schedules_spreadsheet_staff_is_range(self, ctx, use_range: bool):
        """Sets the staff_is_range of the schedules spreadsheet."""
        await self.set_schedules_spreadsheet_values(ctx, {"use_range": use_range})

    @commands.command(aliases=["sssrmi"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_match_id(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range match id."""
        if not spreadsheet.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_match_id": cell_range})

    @commands.command(aliases=["sssrt1"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_team1(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range team1."""
        if not spreadsheet.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_team1": cell_range})

    @commands.command(aliases=["sssrt2"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_team2(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range team2."""
        if not spreadsheet.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_team2": cell_range})

    @commands.command(aliases=["sssrst1"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_score_team1(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range score team1."""
        if not spreadsheet.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_score_team1": cell_range})

    @commands.command(aliases=["sssrst2"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_score_team2(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range score team2."""
        if not spreadsheet.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_score_team2": cell_range})

    @commands.command(aliases=["sssrd"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_date(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range date."""
        if not spreadsheet.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_date": cell_range})

    @commands.command(aliases=["sssrt"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_time(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range time."""
        if not spreadsheet.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_time": cell_range})

    @commands.command(aliases=["sssrr"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_referee(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range referee."""
        if not spreadsheet.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_referee": cell_range})

    @commands.command(aliases=["sssrs"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_streamer(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range streamer."""
        if not spreadsheet.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_streamer": cell_range})

    @commands.command(aliases=["sssrc"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_commentator(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range commentator."""
        if not spreadsheet.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_commentator": cell_range})

    @commands.command(aliases=["sssrml"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_mp_links(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range mp links."""
        if not spreadsheet.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_mp_links": cell_range})

    @commands.command(aliases=["spssn"])  # pragma: no cover
    async def set_players_spreadsheet_sheet_name(self, ctx, *, sheet_name: str = ""):
        """Sets the sheet name of the players spreadsheet."""
        await self.set_players_spreadsheet_values(ctx, {"sheet_name": sheet_name})

    @commands.command(aliases=["spsrtn"])  # pragma: no cover
    async def set_players_spreadsheet_range_team_name(self, ctx, *, cell_range: str = ""):
        """Sets the players spreadsheet range team name."""
        if not spreadsheet.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_players_spreadsheet_values(ctx, {"range_team_name": cell_range})

    @commands.command(aliases=["spsrt"])  # pragma: no cover
    async def set_players_spreadsheet_range_team(self, ctx, *, cell_range: str):
        """Sets the players spreadsheet range team."""
        if not spreadsheet.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_players_spreadsheet_values(ctx, {"range_team": cell_range})

    @commands.command(aliases=["spsrd"])  # pragma: no cover
    async def set_players_spreadsheet_range_discord(self, ctx, *, cell_range: str):
        """Sets the players spreadsheet range team."""
        if not spreadsheet.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_players_spreadsheet_values(ctx, {"range_discord": cell_range})

    async def set_schedules_spreadsheet_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        await self.set_spreadsheet_values(ctx, "schedules", values)

    async def set_players_spreadsheet_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        await self.set_spreadsheet_values(ctx, "players", values)

    async def set_spreadsheet_values(self, ctx, spreadsheet_type, values):
        tournament = self.get_tournament(ctx.guild.id)
        any_spreadsheet = tournament.current_bracket.get_spreadsheet_from_type(spreadsheet_type)
        if not any_spreadsheet:
            raise tosurnament.NoSpreadsheet(spreadsheet_type)
        await self.update_table(ctx, any_spreadsheet, values)

    @commands.command(aliases=["cp"])
    async def copy_bracket(self, ctx, index_from: int, index_to: int):
        """Copies the settings of a bracket to another one."""
        tournament = self.get_tournament(ctx.guild.id)
        brackets = tournament.brackets
        if index_from > 0 and index_from <= len(brackets) and index_to > 0 and index_to <= len(brackets):
            bracket_from = brackets[index_from - 1]
            bracket_to = brackets[index_to - 1]
            bracket_to.post_result_channel_id = bracket_from.post_result_channel_id
            bracket_to.current_round = bracket_from.current_round

            for spreadsheet_type in Bracket.get_spreadsheet_types().keys():
                spreadsheet_from = bracket_from.get_spreadsheet_from_type(spreadsheet_type)
                if spreadsheet_from:
                    spreadsheet_to = bracket_to.get_spreadsheet_from_type(spreadsheet_type)
                    if not spreadsheet_to:
                        spreadsheet_to = bracket_to.create_spreadsheet_from_type(self.bot, spreadsheet_type)
                    spreadsheet_from.copy_to(spreadsheet_to)
                    self.bot.session.update(spreadsheet_to)

            await self.send_reply(ctx, ctx.command.name, "success", bracket_from.name, bracket_to.name)
            return
        raise commands.UserInputError()


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentBracketCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentBracketCog(bot))
