"""Post results commands"""

import math
import re
from discord.ext import commands
from discord.utils import escape_markdown
from bot.modules.tosurnament import module as tosurnament
from common.databases.tosurnament.spreadsheets.players_spreadsheet import TeamInfo
from common.databases.tosurnament.spreadsheets.schedules_spreadsheet import MatchInfo, MatchIdNotFound
from common.databases.tosurnament_message.post_result_message import PostResultMessage
from common.databases.tosurnament_message.base_message import with_corresponding_message, on_raw_reaction_with_context
from common.api import osu
from common.api import challonge
from common.api import tosurnament as tosurnament_api

ROUNDS = ["GF", "Finals", "SF", "QF"]


class PostResultBuilder:
    def __init__(self):
        self.tournament_acronym = ""
        self.tournament_name = ""
        self.bracket_name = ""
        self.bracket_round = ""
        self.score_team1 = 0
        self.score_team2 = 0
        self.roll_team1 = 0
        self.roll_team2 = 0
        self.team_name1 = ""
        self.team_name2 = ""
        self.match_id = ""
        self.mp_links = ""
        self.bans_team1 = ""
        self.bans_team2 = ""
        self.tb_bans_team1 = ""
        self.tb_bans_team2 = ""

    def get_score_team1(self):
        if self.score_team1 < 0 or self.score_team1 == -1 + 2 ** 32:
            return "FF"
        else:
            return str(self.score_team1)

    def get_score_team2(self):
        if self.score_team2 < 0 or self.score_team2 == -1 + 2 ** 32:
            return "FF"
        else:
            return str(self.score_team2)

    def get_mp_links(self):
        links = osu.build_mp_links(self.mp_links.split("\n"))
        return "\n".join(["<" + link + ">" for link in links])

    def build(self, ctx, blueprint, bot, tournament):
        result = blueprint

        team1_with_score = bot.get_string(ctx, "default_team1_with_score")
        if tournament.post_result_message_team1_with_score:
            team1_with_score = tournament.post_result_message_team1_with_score
        if self.score_team1 > self.score_team2:
            team1_with_score = "**" + team1_with_score + "**"
        result = result.replace("%_team1_with_score_", team1_with_score)

        team2_with_score = bot.get_string(ctx, "default_team2_with_score")
        if tournament.post_result_message_team2_with_score:
            team2_with_score = tournament.post_result_message_team2_with_score
        if self.score_team2 > self.score_team1:
            team2_with_score = "**" + team2_with_score + "**"
        result = result.replace("%_team2_with_score_", team2_with_score)

        if self.mp_links:
            if tournament.post_result_message_mp_link:
                result = result.replace("%_mp_link_", tournament.post_result_message_mp_link)
            else:
                result = result.replace("%_mp_link_", bot.get_string(ctx, "default_mp_link"))
        else:
            result = result.replace("%_mp_link_", "")

        if self.roll_team1 > 0 or self.roll_team2 > 0:
            if tournament.post_result_message_rolls:
                result = result.replace("%_rolls_", tournament.post_result_message_rolls)
            else:
                result = result.replace("%_rolls_", bot.get_string(ctx, "default_rolls"))
        else:
            result = result.replace("%_rolls_", "")

        if self.bans_team1 or self.bans_team2:
            if tournament.post_result_message_bans:
                result = result.replace("%_bans_", tournament.post_result_message_bans)
            else:
                result = result.replace("%_bans_", bot.get_string(ctx, "default_bans"))
        else:
            result = result.replace("%_bans_", "")

        if self.tb_bans_team1 or self.tb_bans_team2:
            if tournament.post_result_message_tb_bans:
                result = result.replace("%_tb_bans_", tournament.post_result_message_tb_bans)
            else:
                result = result.replace("%_tb_bans_", bot.get_string(ctx, "default_tb_bans"))
        else:
            result = result.replace("%_tb_bans_", "")

        escaped_team_name1 = escape_markdown(self.team_name1)
        escaped_team_name2 = escape_markdown(self.team_name2)

        result = result.replace("%tournament_acronym", self.tournament_acronym)
        result = result.replace("%tournament_name", self.tournament_name)
        result = result.replace("%bracket_name", self.bracket_name)
        result = result.replace("%bracket_round", self.bracket_round)
        result = result.replace("%match_id", self.match_id)
        result = result.replace("%mp_link", self.get_mp_links())
        result = result.replace("%team1", escaped_team_name1)
        result = result.replace("%team2", escaped_team_name2)
        result = result.replace("%score_team1", self.get_score_team1())
        result = result.replace("%score_team2", self.get_score_team2())
        result = result.replace("%bans_team1", self.bans_team1)
        result = result.replace("%bans_team2", self.bans_team2)
        result = result.replace("%tb_bans_team1", self.tb_bans_team1)
        result = result.replace("%tb_bans_team2", self.tb_bans_team2)
        result = result.replace("%roll_team1", str(self.roll_team1))
        result = result.replace("%roll_team2", str(self.roll_team2))
        if self.roll_team2 > self.roll_team1:
            result = result.replace("%roll_winner", str(self.roll_team2))
            result = result.replace("%roll_loser", str(self.roll_team1))
            result = result.replace("%team_roll_winner", escaped_team_name2)
            result = result.replace("%team_roll_loser", escaped_team_name1)
            result = result.replace("%bans_roll_winner", self.bans_team2)
            result = result.replace("%bans_roll_loser", self.bans_team1)
            result = result.replace("%tb_bans_roll_winner", self.tb_bans_team2)
            result = result.replace("%tb_bans_roll_loser", self.tb_bans_team1)
        else:
            result = result.replace("%roll_winner", str(self.roll_team1))
            result = result.replace("%roll_loser", str(self.roll_team2))
            result = result.replace("%team_roll_winner", escaped_team_name1)
            result = result.replace("%team_roll_loser", escaped_team_name2)
            result = result.replace("%bans_roll_winner", self.bans_team1)
            result = result.replace("%bans_roll_loser", self.bans_team2)
            result = result.replace("%tb_bans_roll_winner", self.tb_bans_team1)
            result = result.replace("%tb_bans_roll_loser", self.tb_bans_team2)
        return result


def get_players_id(team_info):
    players = []
    for player in team_info.players:
        players.append(player.name.get())
    return osu.usernames_to_ids(players)


def calc_match_score(post_result_message, players_team1, players_team2):
    n_warmup = post_result_message.n_warmup
    score_team1 = 0
    score_team2 = 0
    games = []
    for mp_id in post_result_message.mp_links.split("\n"):
        match = osu.get_match(mp_id)
        if not match:
            raise tosurnament.InvalidMpLink()
        games += match.games
    for i, game in enumerate(games):
        if n_warmup > 0:
            n_warmup -= 1
        else:
            if i + 1 < len(games):
                if games[i + 1].beatmap_id == game.beatmap_id:
                    i += 1
                    continue
            total_team1 = 0
            total_team2 = 0
            for score in game.scores:
                if score.passed == "1":
                    if score.user_id in players_team1:
                        total_team1 += int(score.score)
                    elif score.user_id in players_team2:
                        total_team2 += int(score.score)
            if total_team1 > total_team2:
                if score_team1 < int(post_result_message.best_of / 2) + 1:
                    score_team1 += 1
            elif total_team1 < total_team2:
                if score_team2 < int(post_result_message.best_of / 2) + 1:
                    score_team2 += 1
    return score_team1, score_team2


class TosurnamentPostResultCog(tosurnament.TosurnamentBaseModule, name="post_result"):
    """Tosurnament post results commands"""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        role_name = "Referee"
        tournament = self.get_tournament(ctx.guild.id)
        role_id = tournament.get_role_id(role_name)
        role = tosurnament.get_role(ctx.guild.roles, role_id, role_name)
        if not role:
            raise tosurnament.RoleDoesNotExist(role_name)
        if role in ctx.author.roles:
            return True
        raise tosurnament.NotRequiredRole(role.name)

    @commands.command(aliases=["pr"])
    async def post_result(self, ctx, match_id: str):
        """Allows referees to post the result of a match"""
        tournament, bracket = await self.init_post_result(ctx, match_id)
        await self.step0(ctx, match_id, -1 + 2 ** 32, -1 + 2 ** 32, tournament, bracket)

    @commands.command(aliases=["prws"])
    async def post_result_with_scores(self, ctx, match_id: str, score_team1: int, score_team2: int):
        """Allows referees to post the result of a match"""
        tournament, bracket = await self.init_post_result(ctx, match_id)
        await self.step0(ctx, match_id, score_team1, score_team2, tournament, bracket)

    @commands.command(aliases=["prol"])
    async def post_result_one_liner(
        self, ctx, match_id: str, score_team1: int, score_team2: int, best_of: int, n_warmup: int, *, others
    ):
        await self.post_result_one_liner_(ctx, match_id, score_team1, score_team2, best_of, 0, 0, n_warmup, others)

    @commands.command(aliases=["prolwr"])
    async def post_result_one_liner_with_rolls(
        self,
        ctx,
        match_id: str,
        score_team1: int,
        score_team2: int,
        best_of: int,
        roll_team1: int,
        roll_team2: int,
        n_warmup: int,
        *,
        others
    ):
        await self.post_result_one_liner_(
            ctx,
            match_id,
            score_team1,
            score_team2,
            best_of,
            roll_team1,
            roll_team2,
            n_warmup,
            others,
        )

    async def post_result_one_liner_(
        self,
        ctx,
        match_id,
        score_team1,
        score_team2,
        best_of,
        roll_team1,
        roll_team2,
        n_warmup,
        others,
    ):
        """Allows referees to post the result of a match"""
        tournament, bracket = await self.init_post_result(ctx, match_id)
        mp_links = []
        bans = []
        tb_bans = []
        i = 0
        others_kind = others.split("|'|")
        while i < len(others_kind):
            for other in others_kind[i].strip().split('"\'"'):
                other = other.strip()
                if i == 0:
                    mp_links.append(other)
                elif i == 1:
                    bans.append(other)
                else:
                    tb_bans.append(other)
            i += 1
        mp_links = [osu.get_from_string(mp_link) for mp_link in mp_links]
        bans_team1 = []
        bans_team2 = []
        if len(bans) % 2 == 0:
            bans_team1 = bans[: int(len(bans) / 2)]
            bans_team2 = bans[int(len(bans) / 2) :]
        tb_bans_team1 = []
        tb_bans_team2 = []
        if len(tb_bans) % 2 == 0:
            tb_bans_team1 = tb_bans[: int(len(tb_bans) / 2)]
            tb_bans_team2 = tb_bans[int(len(tb_bans) / 2) :]
        post_result_message = PostResultMessage(
            tournament_id=tournament.id,
            bracket_id=bracket.id,
            author_id=ctx.author.id,
            step=8,
            match_id=match_id,
            score_team1=score_team1,
            score_team2=score_team2,
            best_of=best_of,
            roll_team1=roll_team1,
            roll_team2=roll_team2,
            n_warmup=n_warmup,
            mp_links="\n".join(mp_links),
            bans_team1="\n".join(bans_team1),
            bans_team2="\n".join(bans_team2),
            tb_bans_team1="\n".join(tb_bans_team1),
            tb_bans_team2="\n".join(tb_bans_team2),
        )
        message = await self.step7_send_message(ctx, tournament, post_result_message)
        if post_result_message.score_team1 < 0:
            post_result_message.score_team1 = 2 ** 32 - 1
        if post_result_message.score_team2 < 0:
            post_result_message.score_team2 = 2 ** 32 - 1
        self.bot.session.add(post_result_message)
        await self.add_reaction_to_setup_message(message)

    async def init_post_result(self, ctx, match_id):
        """Allows referees to post the result of a match"""
        tournament = self.get_tournament(ctx.guild.id)
        for bracket in tournament.brackets:
            schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
            if not schedules_spreadsheet:
                continue
            try:
                MatchInfo.from_id(schedules_spreadsheet, match_id)
            except MatchIdNotFound:
                continue
            return tournament, bracket
        raise tosurnament.InvalidMatchId()

    async def step0(self, ctx, match_id, score_team1, score_team2, tournament, bracket):
        """Step 0 (initialization) of the post_result_command"""
        message = await self.send_reply(ctx, "step1", match_id)
        post_result_message = PostResultMessage(
            tournament_id=tournament.id,
            bracket_id=bracket.id,
            author_id=ctx.author.id,
            setup_message_id=message.id,
            match_id=match_id,
            score_team1=score_team1,
            score_team2=score_team2,
        )
        if post_result_message.score_team1 < 0:
            post_result_message.score_team1 = 2 ** 32 - 1
        if post_result_message.score_team2 < 0:
            post_result_message.score_team2 = 2 ** 32 - 1
        self.bot.session.add(post_result_message)
        await self.add_reaction_to_setup_message(message)

    async def step1(self, ctx, tournament, post_result_message, parameter):
        """Step 1 (best of) of the post_result command"""
        try:
            parameter = int(parameter)
        except ValueError:
            raise commands.UserInputError
        if parameter < 0 or parameter % 2 != 1:
            raise commands.UserInputError
        post_result_message.best_of = parameter
        await self.update_post_result_setup_message_with_ctx(ctx, post_result_message, 2)

    async def step2(self, ctx, tournament, post_result_message, parameter):
        """Step 2 (roll team1) of the post_result command"""
        try:
            parameter = int(parameter)
        except ValueError:
            raise commands.UserInputError
        if parameter < 1 or parameter > 100:
            raise commands.UserInputError
        post_result_message.roll_team1 = parameter
        await self.update_post_result_setup_message_with_ctx(ctx, post_result_message, 3)

    async def step3(self, ctx, tournament, post_result_message, parameter):
        """Step 3 (roll team2) of the post_result command"""
        try:
            parameter = int(parameter)
        except ValueError:
            raise commands.UserInputError
        if parameter < 1 or parameter > 100:
            raise commands.UserInputError
        post_result_message.roll_team2 = parameter
        await self.update_post_result_setup_message_with_ctx(ctx, post_result_message, 4)

    async def step4(self, ctx, tournament, post_result_message, parameter):
        """Step 4 (nb of warmups) of the post_result command"""
        try:
            parameter = int(parameter)
        except ValueError:
            raise commands.UserInputError
        if parameter < 0:
            raise commands.UserInputError
        post_result_message.n_warmup = parameter
        await self.update_post_result_setup_message_with_ctx(ctx, post_result_message, 5)

    async def step5(self, ctx, tournament, post_result_message, parameter):
        """Step 5 (mp links) of the post_result command"""
        mp_links = []
        links = re.split(" |\n", parameter)
        for link in links:
            link = osu.get_from_string(link)
            mp_links.append(link)
        post_result_message.mp_links = "\n".join(mp_links)
        await self.update_post_result_setup_message_with_ctx(ctx, post_result_message, 6)

    async def step6(self, ctx, tournament, post_result_message, parameter):
        """Step 6 (bans team1) of the post_result command"""
        post_result_message.bans_team1 = parameter
        await self.update_post_result_setup_message_with_ctx(ctx, post_result_message, 7)

    async def step7_send_message(self, ctx, tournament, post_result_message):
        bracket = tosurnament_api.get_bracket(tournament.id, post_result_message.bracket_id)
        if not bracket:
            self.bot.session.delete(post_result_message)
            raise tosurnament.NoBracket()
        schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
        if not schedules_spreadsheet:
            raise tosurnament.NoSpreadsheet("schedules")
        match_info = MatchInfo.from_id(schedules_spreadsheet, post_result_message.match_id, False)
        prbuilder = await self.create_prbuilder(None, post_result_message, tournament, bracket, match_info, ctx)
        if tournament.post_result_message:
            result_string = tournament.post_result_message
        else:
            result_string = self.get_string(ctx, "default")
        result_string = prbuilder.build(ctx, result_string, self, tournament)

        await self.update_post_result_setup_message(ctx, post_result_message, 8)

        preview_message = await self.send_reply(ctx, "preview", result_string)
        post_result_message.preview_message_id = preview_message.id

    async def step7(self, ctx, tournament, post_result_message, parameter):
        """Step 7 (bans team2) of the post_result command"""
        post_result_message.bans_team2 = parameter
        await self.step7_send_message(ctx, tournament, post_result_message)

    async def step8_write_in_spreadsheet(self, bracket, match_info, prbuilder):
        match_info.score_team1.set(prbuilder.get_score_team1())
        match_info.score_team2.set(prbuilder.get_score_team2())
        mp_links = osu.build_mp_links(prbuilder.mp_links.split("\n"))
        i = 0
        while i < len(match_info.mp_links) and i < len(mp_links):
            if i + 1 == len(match_info.mp_links):
                match_info.mp_links[i].set("/".join(mp_links[i:]))
            else:
                match_info.mp_links[i].set(mp_links[i])
            i += 1
        self.add_update_spreadsheet_background_task(await bracket.get_schedules_spreadsheet())

    async def step8_remove_player_role(self, ctx, error_channel, tournament, challonge_tournament, loser_participant):
        if challonge_tournament.state == "group_stages_underway":
            for match in challonge_tournament.matches:
                if not match.state == "complete":
                    return
            await self.send_reply(ctx, "group_stage_complete", channel=error_channel)
        elif challonge_tournament.state == "underway":
            matches = challonge.get_matches_of_participant(challonge_tournament.id, loser_participant.id)
            for match in matches:
                if not match.state == "complete":
                    return
            bracket = tournament.current_bracket
            players_spreadsheet = await bracket.get_players_spreadsheet()
            if not players_spreadsheet:
                return
            try:
                team_info = TeamInfo.from_team_name(players_spreadsheet, loser_participant.name)
                player_role = tosurnament.get_role(ctx.guild.roles, tournament.player_role_id, "Player")
                roles_to_remove = [player_role]
                bracket_role = tosurnament.get_role(ctx.guild.roles, bracket.role_id, bracket.name)
                if bracket_role:
                    roles_to_remove.append(bracket_role)
                team_role = tosurnament.get_role(ctx.guild.roles, None, team_info.team_name)
                if team_role:
                    roles_to_remove.append(team_role)
                for player in team_info.players:
                    user = tosurnament.UserAbstraction.get_from_player_info(self.bot, player, ctx.guild)
                    member = user.get_member(ctx.guild)
                    if member:
                        await member.remove_roles(*roles_to_remove)
            except Exception:
                return

    async def find_corresponding_challonge_match(
        self, ctx, tournament, challonge_tournament, error_channel, prbuilder, update_score=False
    ):
        participant1 = None
        participant2 = None
        for participant in challonge_tournament.participants:
            if participant.name == prbuilder.team_name1:
                participant1 = participant
                participant1.set_match_score(prbuilder.score_team1)
            elif participant.name == prbuilder.team_name2:
                participant2 = participant
                participant2.set_match_score(prbuilder.score_team2)
        if not participant1 or not participant2:
            await self.send_reply(ctx, "participant_not_found", prbuilder.match_id, channel=error_channel)
            return None
        participant_matches = [match for match in participant1.matches if match.state == "open"]
        for match in participant_matches:
            if update_score:
                if match.update_score_with_participants(participant1, participant2):
                    await self.step8_remove_player_role(
                        ctx, error_channel, tournament, challonge_tournament, match.get_loser_participant()
                    )
                    return match
            else:
                if match.has_participant(participant1) and match.has_participant(participant2):
                    return match
        await self.send_reply(
            ctx,
            "match_not_found",
            prbuilder.match_id,
            prbuilder.team_name1,
            prbuilder.team_name2,
            channel=error_channel,
        )
        return None

    async def step8_challonge(self, ctx, tournament, error_channel, prbuilder):
        try:
            challonge_tournament = tournament.current_bracket.challonge_tournament
            if challonge_tournament.state == "pending":
                challonge_tournament.start()
            await self.find_corresponding_challonge_match(
                ctx, tournament, challonge_tournament, error_channel, prbuilder, True
            )
        except challonge.ChallongeException as e:
            await self.on_cog_command_error(ctx, e, channel=error_channel)
            return

    async def get_teams_infos(self, bracket, team_name1, team_name2):
        players_spreadsheet = await bracket.get_players_spreadsheet()
        if not players_spreadsheet:
            return None, None
        team1_info = TeamInfo.from_team_name(players_spreadsheet, team_name1)
        team2_info = TeamInfo.from_team_name(players_spreadsheet, team_name2)
        return team1_info, team2_info

    async def create_prbuilder(self, ctx, post_result_message, tournament, bracket, match_info, error_channel):
        prbuilder = PostResultBuilder()
        prbuilder.tournament_acronym = tournament.acronym
        prbuilder.tournament_name = tournament.name
        prbuilder.bracket_name = bracket.name
        prbuilder.match_id = post_result_message.match_id
        prbuilder.team_name1 = match_info.team1.get()
        prbuilder.team_name2 = match_info.team2.get()
        prbuilder.roll_team1 = post_result_message.roll_team1
        prbuilder.roll_team2 = post_result_message.roll_team2
        prbuilder.bans_team1 = post_result_message.bans_team1
        prbuilder.bans_team2 = post_result_message.bans_team2
        prbuilder.tb_bans_team1 = post_result_message.tb_bans_team1
        prbuilder.tb_bans_team2 = post_result_message.tb_bans_team2

        current_round = ""
        if bracket.current_round:
            current_round = bracket.current_round
        elif bracket.challonge:
            try:
                challonge_tournament = bracket.challonge_tournament
                rounds, n_loser_rounds = self.get_rounds(challonge_tournament)
                match = await self.find_corresponding_challonge_match(
                    ctx, tournament, challonge_tournament, error_channel, prbuilder
                )
                if match:
                    match_round = match.round
                    if match_round > n_loser_rounds + 1:
                        match_round = n_loser_rounds + 1
                    if match_round > 0:
                        if n_loser_rounds + 1 < len(rounds):
                            current_round = rounds[-match_round - (len(rounds) - n_loser_rounds - 1)]
                        else:
                            current_round = rounds[-match_round]
                    else:
                        if n_loser_rounds + 1 < len(rounds):
                            current_round = rounds[
                                -1 * math.floor(-match_round / 2) - 2 - (len(rounds) - n_loser_rounds - 1)
                            ]
                        else:
                            current_round = rounds[-1 * math.floor(-match_round / 2) - 2]
                        if current_round == ROUNDS[0]:
                            current_round = "LF"
            except challonge.ChallongeException as e:
                await self.on_cog_command_error(ctx, e, channel=error_channel)
        prbuilder.bracket_round = current_round

        score_team1 = post_result_message.score_team1
        score_team2 = post_result_message.score_team2
        if score_team1 == 0 and score_team2 == 0:
            team1_info, team2_info = await self.get_teams_infos(bracket, match_info.team1.get(), match_info.team2.get())
            if team1_info and team2_info:
                players_id_team1 = get_players_id(team1_info)
                players_id_team2 = get_players_id(team2_info)
            else:
                players_id_team1 = osu.usernames_to_ids([prbuilder.team_name1])
                players_id_team2 = osu.usernames_to_ids([prbuilder.team_name2])
            score_team1, score_team2 = calc_match_score(post_result_message, players_id_team1, players_id_team2)

        prbuilder.score_team1 = score_team1
        prbuilder.score_team2 = score_team2
        prbuilder.mp_links = post_result_message.mp_links
        return prbuilder

    async def step8_per_bracket(self, ctx, post_result_message, tournament):
        bracket = tournament.current_bracket
        schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
        if not schedules_spreadsheet:
            raise tosurnament.NoSpreadsheet("schedules")
        match_info = MatchInfo.from_id(schedules_spreadsheet, post_result_message.match_id, False)
        if tournament.staff_channel_id:
            error_channel = self.bot.get_channel(tournament.staff_channel_id)
        else:
            error_channel = ctx
        prbuilder = await self.create_prbuilder(
            ctx, post_result_message, tournament, bracket, match_info, error_channel
        )
        if tournament.post_result_message:
            result_string = tournament.post_result_message
        else:
            result_string = self.get_string(ctx, "default")
        result_string = prbuilder.build(result_string, self, tournament)
        if bracket.challonge:
            await self.step8_challonge(ctx, tournament, error_channel, prbuilder)
        await self.step8_write_in_spreadsheet(bracket, match_info, prbuilder)
        post_result_channel = ctx
        if bracket.post_result_channel_id:
            post_result_channel = self.bot.get_channel(bracket.post_result_channel_id)
        await post_result_channel.send(result_string)

    async def step8(self, ctx, tournament, post_result_message, parameter):
        """Step 8 of the post_result command"""
        if parameter == "post":
            tournament.current_bracket_id = post_result_message.bracket_id
            if not tournament.current_bracket:
                raise tosurnament.NoBracket()
            await self.step8_per_bracket(ctx, post_result_message, tournament)
            self.bot.session.delete(post_result_message)
            await self.delete_setup_message(ctx.channel, post_result_message)
            try:
                await ctx.message.delete()
            except Exception as e:
                self.bot.info(str(type(e)) + ": " + str(e))

    async def delete_setup_message(self, channel, post_result_message):
        if post_result_message.setup_message_id:
            message = await channel.fetch_message(post_result_message.setup_message_id)
            await message.delete()
        if post_result_message.preview_message_id:
            message = await channel.fetch_message(post_result_message.preview_message_id)
            await message.delete()
            post_result_message.preview_message_id = 0

    @commands.command(aliases=["a"])
    async def answer(self, ctx, *, parameter: str):
        """Allows referees to setup the result message"""
        tournament = self.get_tournament(ctx.guild.id)
        post_result_message = (
            self.bot.session.query(PostResultMessage)
            .where(PostResultMessage.tournament_id == tournament.id)
            .where(PostResultMessage.author_id == ctx.author.id)
            .first()
        )
        if not post_result_message:
            self.bot.info("No post result message found")
            return
        steps = [
            self.step1,
            self.step2,
            self.step3,
            self.step4,
            self.step5,
            self.step6,
            self.step7,
            self.step8,
        ]
        self.bot.info("answer of step " + str(post_result_message.step))
        await steps[post_result_message.step - 1](ctx, tournament, post_result_message, parameter)

    @on_raw_reaction_with_context("add", valid_emojis=["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "❌"])
    @with_corresponding_message(PostResultMessage)
    async def reaction_on_setup_message(self, ctx, emoji, post_result_message):
        """Change the setup message step"""
        ctx.command.name = "post_result"
        try:
            tournament = self.get_tournament(ctx.guild.id)
        except tosurnament.NoTournament:
            return
        if emoji.name == "❌":
            self.bot.session.delete(post_result_message)
            await self.delete_setup_message(ctx.channel, post_result_message)
            await self.send_reply(ctx, "cancel")
            return
        emoji_steps = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣"]
        step = emoji_steps.index(emoji.name) + 1
        try:
            if step == 8:
                await self.step7_send_message(ctx.channel, tournament, post_result_message)
            else:
                await self.update_post_result_setup_message(ctx, post_result_message, step)
        except Exception as e:
            await self.on_cog_command_error(ctx, e)

    async def add_reaction_to_setup_message(self, message):
        try:
            await message.add_reaction("1⃣")
            await message.add_reaction("2⃣")
            await message.add_reaction("3⃣")
            await message.add_reaction("4⃣")
            await message.add_reaction("5⃣")
            await message.add_reaction("6⃣")
            await message.add_reaction("7⃣")
            await message.add_reaction("8⃣")
            await message.add_reaction("❌")
        except Exception:
            return

    async def update_post_result_setup_message_with_ctx(self, ctx, post_result_message, new_step):
        try:
            await ctx.message.delete()
        except Exception as e:
            self.bot.info(str(type(e)) + ": " + str(e))
        await self.update_post_result_setup_message(ctx, post_result_message, new_step)

    async def update_post_result_setup_message(self, ctx, post_result_message, new_step):
        ctx.command.name = "post_result"
        await self.delete_setup_message(ctx.channel, post_result_message)
        message = await self.send_reply(
            ctx,
            "step" + str(new_step),
            post_result_message.match_id,
            post_result_message.best_of,
            post_result_message.roll_team1,
            post_result_message.roll_team2,
            post_result_message.n_warmup,
            osu.build_mp_links(post_result_message.mp_links.split("\n")),
            post_result_message.bans_team1,
            post_result_message.bans_team2,
            post_result_message.tb_bans_team1,
            post_result_message.tb_bans_team2,
        )
        post_result_message.setup_message_id = message.id
        post_result_message.step = new_step
        if post_result_message.score_team1 < 0:
            post_result_message.score_team1 = 2 ** 32 - 1
        if post_result_message.score_team2 < 0:
            post_result_message.score_team2 = 2 ** 32 - 1
        self.bot.session.update(post_result_message)
        await self.add_reaction_to_setup_message(message)

    async def post_result_common_handler(self, ctx, error):
        if isinstance(error, tosurnament.InvalidMpLink):
            await self.send_reply(ctx, "invalid_mp_link")

    @answer.error
    async def answer_handler(self, ctx, error):
        """Error handler of answer function"""
        await self.post_result_common_handler(ctx, error)

    @post_result.error
    async def post_result_handler(self, ctx, error):
        """Error handler of post_result function"""
        await self.post_result_common_handler(ctx, error)

    @post_result_with_scores.error
    async def post_result_with_scores_handler(self, ctx, error):
        """Error handler of post_result_with_scores function"""
        await self.post_result_common_handler(ctx, error)

    @commands.command(aliases=["tprm"])
    async def test_post_result_message(self, ctx, nb_bans=1, nb_tb_bans=1):
        """Shows the post result message with default values."""
        tournament = self.get_tournament(ctx.guild.id)
        bracket = tournament.current_bracket
        pr_builder = PostResultBuilder()
        pr_builder.tournament_acronym = tournament.acronym
        pr_builder.tournament_name = tournament.name
        pr_builder.bracket_name = bracket.name
        current_round = bracket.current_round
        if not current_round and bracket.challonge:
            challonge_tournament = challonge.get_tournament(bracket.challonge)
            rounds, n_loser_rounds = self.get_rounds(challonge_tournament)
            current_round = rounds[n_loser_rounds]
        pr_builder.bracket_round = current_round
        pr_builder.score_team1 = 5
        pr_builder.score_team2 = 2
        pr_builder.roll_team1 = 100
        pr_builder.roll_team2 = 1
        pr_builder.team_name1 = "Team 1"
        pr_builder.team_name2 = "Team 2"
        pr_builder.match_id = "W1"
        pr_builder.mp_links = "123456"
        pr_builder.bans_team1 = "\n".join(["NM" + str(i + 1) for i in range(nb_bans)])
        pr_builder.bans_team2 = "\n".join(["HD" + str(i + 1) for i in range(nb_bans)])
        pr_builder.tb_bans_team1 = "\n".join(["TB" + str(i + 1) for i in range(nb_tb_bans)])
        pr_builder.tb_bans_team2 = "\n".join(["TB" + str(i + 1) for i in range(nb_tb_bans)])
        if tournament.post_result_message:
            bp_result_string = tournament.post_result_message
        else:
            bp_result_string = self.get_string(ctx, "default")
        result_string = "__Normal preview:__\n" + pr_builder.build(bp_result_string, self, tournament)
        pr_builder.score_team1 = -1
        pr_builder.score_team2 = 0
        pr_builder.mp_links = ""
        pr_builder.bans_team1 = ""
        pr_builder.bans_team2 = ""
        pr_builder.tb_bans_team1 = ""
        pr_builder.tb_bans_team2 = ""
        result_string += "\n\n\n__FF preview:__\n" + pr_builder.build(bp_result_string, self, tournament)
        await ctx.send(result_string)

    def get_rounds(self, challonge_tournament):
        participants = [participant for participant in challonge_tournament.participants if participant.active]
        n_loser_round = math.floor(math.log2(len(participants)))
        rounds = list(ROUNDS)
        while n_loser_round + 1 > len(rounds):
            rounds.append("RO" + str(pow(2, len(rounds))))
        return rounds, n_loser_round


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentPostResultCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentPostResultCog(bot))
