"""Players spreadsheet table"""

from mysqldb_wrapper import Base, Id
from common.api.spreadsheet import find_corresponding_cells_best_effort


class PlayersSpreadsheet(Base):
    """Players spreadsheet class"""

    __tablename__ = "players_spreadsheet"

    id = Id()
    spreadsheet_id = str()
    sheet_name = str("")
    range_team_name = str("")
    range_team = str("B2:B")


class TeamNotFound(Exception):
    """Thrown when a match id is not found."""

    def __init__(self, team):
        self.team = team


class DuplicateTeam(Exception):
    """Thrown when a match id is found multiple times."""

    def __init__(self, team):
        self.team = team


class TeamInfo:
    """Contains all info about a team."""

    def __init__(self, team_name_cell):
        self.team_name = team_name_cell
        self.players = [team_name_cell]

    def set_players(self, players_cells):
        if players_cells:
            self.players = players_cells
        else:
            self.players = [self.team_name]

    @staticmethod
    def from_team_name(players_spreadsheet, worksheet, team_name):
        if not players_spreadsheet.range_team_name:
            return TeamInfo.from_player_name(players_spreadsheet, worksheet, team_name)
        team_name_cells = worksheet.find_cells(players_spreadsheet.range_team_name, team_name)
        if not team_name_cells:
            raise TeamNotFound(team_name)
        if len(team_name_cells) > 1:
            raise DuplicateTeam(team_name)
        team_name_cell = team_name_cells[0]
        return TeamInfo.from_player_cell(players_spreadsheet, worksheet, team_name_cell)

    @staticmethod
    def from_team_name_cell(players_spreadsheet, worksheet, team_name_cell):
        team_name_best_effort_ys = team_name_cell.y_merge_range
        team_info = TeamInfo(team_name_cell)
        team_info.set_players(
            find_corresponding_cells_best_effort(
                worksheet.get_range(players_spreadsheet.range_team), team_name_best_effort_ys,
            )
        )
        return team_info
