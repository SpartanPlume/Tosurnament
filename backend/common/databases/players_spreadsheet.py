"""Players spreadsheet table"""

import re
from discord.ext import commands
from common.databases.base_spreadsheet import BaseSpreadsheet
from common.api.spreadsheet import (
    find_corresponding_cell_best_effort_from_range,
    find_corresponding_cells_best_effort_from_range,
    Cell,
    from_letter_base,
)


class PlayersSpreadsheet(BaseSpreadsheet):
    """Players spreadsheet class"""

    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._type = "players"

    __tablename__ = "players_spreadsheet"

    range_team_name = str("")
    range_team = str("A2:A")
    range_discord = str("B2:B")
    range_discord_id = str()
    range_rank = str()
    range_bws_rank = str()
    range_osu_id = str()
    range_pp = str()
    range_timezone = str()
    max_range_for_teams = int(0)


class TeamNotFound(commands.CommandError):
    """Thrown when a match id is not found."""

    def __init__(self, team):
        self.team = team


class DuplicateTeam(commands.CommandError):
    """Thrown when a match id is found multiple times."""

    def __init__(self, team):
        self.team = team


class TeamInfo:
    """Contains all info about a team."""

    def __init__(self, team_name_cell):
        self.team_name = team_name_cell
        self.players = [team_name_cell]
        self.discord = [""]
        self.discord_ids = [""]
        self.ranks = [""]
        self.bws_ranks = [""]
        self.osu_ids = [""]
        self.pps = [""]
        self.timezones = [""]

    def set_players(self, players_cells):
        if players_cells:
            self.players = players_cells
        else:
            self.players = [self.team_name]

    def set_discord(self, discords):
        while len(discords) < len(self.players):
            discords.append(Cell(-1, -1, None))
        self.discord = discords

    def set_discord_ids(self, discord_ids):
        while len(discord_ids) < len(self.players):
            discord_ids.append(Cell(-1, -1, None))
        self.discord_ids = discord_ids

    def set_ranks(self, ranks):
        while len(ranks) < len(self.players):
            ranks.append(Cell(-1, -1, None))
        self.ranks = ranks

    def set_bws_ranks(self, bws_ranks):
        while len(bws_ranks) < len(self.players):
            bws_ranks.append(Cell(-1, -1, None))
        self.bws_ranks = bws_ranks

    def set_osu_ids(self, osu_ids):
        while len(osu_ids) < len(self.players):
            osu_ids.append(Cell(-1, -1, None))
        self.osu_ids = osu_ids

    def set_pps(self, pps):
        while len(pps) < len(self.players):
            pps.append(Cell(-1, -1, None))
        self.pps = pps

    def set_timezones(self, timezones):
        while len(timezones) < len(self.players):
            timezones.append(Cell(-1, -1, None))
        self.timezones = timezones

    @staticmethod
    def from_player_name(players_spreadsheet, player_name):
        player_name = str(player_name)
        player_cells = players_spreadsheet.spreadsheet.find_cells(players_spreadsheet.range_team, player_name)
        if not player_cells:
            raise TeamNotFound(player_name)
        # ? To keep ?
        # if len(player_cells) > 1:
        #    raise DuplicateTeam(player_name)
        player_cell = player_cells[0]
        return TeamInfo.from_player_cell(players_spreadsheet, player_cell)

    @staticmethod
    def from_player_cell(players_spreadsheet, player_cell):
        player_cell.change_value_to_string()
        team_info = TeamInfo(player_cell)
        team_info.set_discord(
            [
                find_corresponding_cell_best_effort_from_range(
                    players_spreadsheet.spreadsheet,
                    players_spreadsheet.range_discord,
                    player_cell,
                    max_difference_with_base=players_spreadsheet.max_range_for_teams
                )
            ]
        )
        team_info.set_discord_ids(
            [
                find_corresponding_cell_best_effort_from_range(
                    players_spreadsheet.spreadsheet,
                    players_spreadsheet.range_discord_id,
                    player_cell,
                    max_difference_with_base=players_spreadsheet.max_range_for_teams
                )
            ]
        )
        team_info.set_ranks(
            [
                find_corresponding_cell_best_effort_from_range(
                    players_spreadsheet.spreadsheet,
                    players_spreadsheet.range_rank,
                    player_cell,
                    max_difference_with_base=players_spreadsheet.max_range_for_teams
                )
            ]
        )
        team_info.set_bws_ranks(
            [
                find_corresponding_cell_best_effort_from_range(
                    players_spreadsheet.spreadsheet,
                    players_spreadsheet.range_bws_rank,
                    player_cell,
                    max_difference_with_base=players_spreadsheet.max_range_for_teams
                )
            ]
        )
        team_info.set_osu_ids(
            [
                find_corresponding_cell_best_effort_from_range(
                    players_spreadsheet.spreadsheet,
                    players_spreadsheet.range_osu_id,
                    player_cell,
                    max_difference_with_base=players_spreadsheet.max_range_for_teams
                )
            ]
        )
        team_info.set_pps(
            [
                find_corresponding_cell_best_effort_from_range(
                    players_spreadsheet.spreadsheet,
                    players_spreadsheet.range_pp,
                    player_cell,
                    max_difference_with_base=players_spreadsheet.max_range_for_teams
                )
            ]
        )
        team_info.set_timezones(
            [
                find_corresponding_cell_best_effort_from_range(
                    players_spreadsheet.spreadsheet,
                    players_spreadsheet.range_timezone,
                    player_cell,
                    max_difference_with_base=players_spreadsheet.max_range_for_teams
                )
            ]
        )
        return team_info

    @staticmethod
    def from_discord_id(players_spreadsheet, discord_id):
        discord_id = str(discord_id)
        discord_id_cells = players_spreadsheet.spreadsheet.find_cells(players_spreadsheet.range_discord_id, discord_id)
        if not discord_id_cells:
            raise TeamNotFound(discord_id)
        discord_id_cell = discord_id_cells[0]
        return TeamInfo.from_discord_id_cell(players_spreadsheet, discord_id_cell)

    @staticmethod
    def from_discord_id_cell(players_spreadsheet, discord_id_cell):
        if players_spreadsheet.range_team_name:
            team_name_cell = find_corresponding_cell_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_team_name,
                discord_id_cell,
            )
            if team_name_cell.x == -1:
                raise TeamNotFound(discord_id_cell.value)
            return TeamInfo.from_team_name_cell(players_spreadsheet, team_name_cell)
        else:
            player_cell = find_corresponding_cell_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_team,
                discord_id_cell,
            )
            if player_cell.x == -1:
                raise TeamNotFound(discord_id_cell.value)
            return TeamInfo.from_player_cell(players_spreadsheet, player_cell)

    @staticmethod
    def from_team_name(players_spreadsheet, team_name):
        team_name = str(team_name)
        if not players_spreadsheet.range_team_name:
            return TeamInfo.from_player_name(players_spreadsheet, team_name)
        team_name_cells = players_spreadsheet.spreadsheet.find_cells(players_spreadsheet.range_team_name, team_name)
        if not team_name_cells:
            raise TeamNotFound(team_name)
        # ? To keep ?
        # if len(team_name_cells) > 1:
        #    raise DuplicateTeam(team_name)
        team_name_cell = team_name_cells[0]
        return TeamInfo.from_team_name_cell(players_spreadsheet, team_name_cell)

    @staticmethod
    def from_team_name_cell(players_spreadsheet, team_name_cell):
        team_name_cell.change_value_to_string()
        team_info = TeamInfo(team_name_cell)
        team_info.set_players(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_team,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams
                to_string=True,
            )
        )
        team_info.set_discord(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_discord,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams
            )
        )
        team_info.set_discord_ids(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_discord_id,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams
            )
        )
        team_info.set_ranks(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_rank,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams
            )
        )
        team_info.set_bws_ranks(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_bws_rank,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams
            )
        )
        team_info.set_osu_ids(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_osu_id,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams
            )
        )
        team_info.set_pps(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_pp,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams
            )
        )
        team_info.set_timezones(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_timezone,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams
            )
        )
        return team_info

    @staticmethod
    def get_first_blank_fields(players_spreadsheet):
        range_to_use = None
        if players_spreadsheet.range_team_name:
            range_to_use = players_spreadsheet.range_team_name
        else:
            range_to_use = players_spreadsheet.range_team
        cells = players_spreadsheet.spreadsheet.get_range(range_to_use)
        if not cells:
            worksheet, range_to_use = players_spreadsheet.spreadsheet.get_worksheet_and_range(range_to_use)
            splitted_range = range_to_use.split(":")[0]
            column, row, _ = re.split(r"(\d+)", splitted_range)  # TODO: handle all kind of ranges
            cells = [[Cell(from_letter_base(column), int(row) - 1, "")]]
            worksheet.cells = cells
        used = False
        for row in cells:
            used = False
            for cell in row:
                if cell.value:
                    used = True
                    break
            if not used:
                break
        if used:
            worksheet, _ = players_spreadsheet.spreadsheet.get_worksheet_and_range(range_to_use)
            cells = worksheet.cells
            row = [Cell(row[0].x, row[0].y + 1, "")]
            cells.append(row)
        if players_spreadsheet.range_team_name:
            return TeamInfo.from_team_name_cell(players_spreadsheet, row[0])
        else:
            return TeamInfo.from_player_cell(players_spreadsheet, row[0])
