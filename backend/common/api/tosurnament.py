import requests
from discord.ext import commands
from common.databases.tosurnament.tournament import Tournament
from common.databases.tosurnament.bracket import Bracket
from common.databases.tosurnament.guild import Guild
from common.databases.tosurnament.spreadsheets.schedules_spreadsheet import SchedulesSpreadsheet
from common.databases.tosurnament.spreadsheets.players_spreadsheet import PlayersSpreadsheet
from common.databases.tosurnament.spreadsheets.qualifiers_spreadsheet import QualifiersSpreadsheet
from common.databases.tosurnament.spreadsheets.qualifiers_results_spreadsheet import QualifiersResultsSpreadsheet
from common.databases.tosurnament.allowed_reschedule import AllowedReschedule
from common.databases.tosurnament.user import User

TOSURNAMENT_URL = "http://localhost:5001/api/v1/tosurnament/"


class TosurnamentException(commands.CommandError):
    """Base exception of the tosurnament api wrapper"""

    def __init__(self, code, description):
        self.code = code
        self.description = description


class ServerError(TosurnamentException):
    """Special exception when the api can't be reached"""

    def __init__(self):
        super().__init__(500, "Couldn't reach Tosurnament API")


def remove_bytes_entries(data):
    if data is None:
        return None
    new_data = {}
    for key, value in data.items():
        if not isinstance(value, bytes):
            new_data[key] = value
    return new_data


def requests_wrapper(method, url, data=None, url_parameters=None):
    try:
        r = requests.request(method, url, json=remove_bytes_entries(data), params=url_parameters)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        if method == "get" and r.status_code == 404:
            return None
        raise TosurnamentException(r.status_code, r.text)
    except requests.exceptions.RequestException:
        raise ServerError()
    if r.status_code == 204:
        return None
    return r.json()


# Tournaments
def fill_tournament_object_from_data(tournament_data, include_brackets, include_spreadsheets):
    brackets = []
    if include_brackets:
        brackets_data = tournament_data.pop("brackets", [])
        for bracket_data in brackets_data:
            brackets.append(fill_bracket_object_from_data(bracket_data, include_spreadsheets))
    tournament = Tournament(**tournament_data)
    setattr(tournament, "_brackets", brackets)
    return tournament


def get_tournament(tournament_id, include_brackets=True, include_spreadsheets=True):
    url_parameters = {"include_brackets": str(include_brackets), "include_spreadsheets": str(include_spreadsheets)}
    tournament_data = requests_wrapper(
        "get", TOSURNAMENT_URL + "tournaments/" + str(tournament_id), url_parameters=url_parameters
    )
    if tournament_data is None:
        return None
    return fill_tournament_object_from_data(tournament_data, include_brackets, include_spreadsheets)


def get_tournaments(include_brackets=True, include_spreadsheets=True):
    url_parameters = {"include_brackets": str(include_brackets), "include_spreadsheets": str(include_spreadsheets)}
    tournaments_data = requests_wrapper("get", TOSURNAMENT_URL + "tournaments", url_parameters=url_parameters)
    tournaments = []
    if tournaments_data is None:
        return tournaments
    for tournament_data in tournaments_data["tournaments"]:
        tournaments.append(fill_tournament_object_from_data(tournament_data, include_brackets, include_spreadsheets))
    return tournaments


def get_tournament_by_discord_guild_id(guild_id, include_brackets=True, include_spreadsheets=True):
    url_parameters = {
        "guild_id": str(guild_id),
        "include_brackets": str(include_brackets),
        "include_spreadsheets": str(include_spreadsheets),
    }
    tournament_data = requests_wrapper("get", TOSURNAMENT_URL + "tournaments", url_parameters=url_parameters)
    if not tournament_data["tournaments"]:
        return None
    return fill_tournament_object_from_data(tournament_data["tournaments"][0], include_brackets, include_spreadsheets)


def update_tournament(tournament):
    requests_wrapper("put", TOSURNAMENT_URL + "tournaments/" + str(tournament.id), data=tournament.get_table_dict())
    return tournament


def create_tournament(tournament):
    tournament_data = requests_wrapper("post", TOSURNAMENT_URL + "tournaments", data=tournament.get_table_dict())
    return fill_tournament_object_from_data(tournament_data, True, False)


def delete_tournament(tournament):
    if isinstance(tournament, Tournament):
        tournament_id = str(tournament.id)
    else:
        tournament_id = str(tournament)
    requests_wrapper("delete", TOSURNAMENT_URL + "tournaments/" + tournament_id)


# Brackets
def fill_bracket_object_from_data(bracket_data, include_spreadsheets):
    spreadsheets = {}
    if include_spreadsheets:
        for spreadsheet_type, spreadsheet_class in Bracket.get_spreadsheet_types().items():
            spreadsheet_data = bracket_data.pop(spreadsheet_type + "_spreadsheet", None)
            if spreadsheet_data:
                spreadsheets[spreadsheet_type] = spreadsheet_class(**spreadsheet_data)
    bracket = Bracket(**bracket_data)
    for spreadsheet_type, spreadsheet in spreadsheets.items():
        setattr(bracket, "_" + spreadsheet_type + "_spreadsheet", spreadsheet)
    return bracket


def get_brackets(tournament_id, include_spreadsheets=True):
    url_parameters = {"include_spreadsheets": str(include_spreadsheets)}
    brackets_data = requests_wrapper(
        "get", TOSURNAMENT_URL + "tournaments/" + str(tournament_id) + "/brackets", url_parameters=url_parameters
    )
    brackets = []
    if brackets_data is None:
        return brackets
    for bracket_data in brackets_data["brackets"]:
        brackets.append(fill_bracket_object_from_data(bracket_data, include_spreadsheets))
    return brackets


def get_bracket(tournament_id, bracket_id, include_spreadsheets=True):
    url_parameters = {"include_spreadsheets": str(include_spreadsheets)}
    bracket_data = requests_wrapper(
        "get",
        TOSURNAMENT_URL + "tournaments/" + str(tournament_id) + "/brackets/" + str(bracket_id),
        url_parameters=url_parameters,
    )
    if bracket_data is None:
        return None
    return fill_bracket_object_from_data(bracket_data, include_spreadsheets)


def update_bracket(tournament_id, bracket):
    requests_wrapper(
        "put",
        TOSURNAMENT_URL + "tournaments/" + str(tournament_id) + "/brackets/" + str(bracket.id),
        data=bracket.get_table_dict(),
    )
    return bracket


def create_bracket(tournament_id, bracket):
    bracket_data = requests_wrapper(
        "post",
        TOSURNAMENT_URL + "tournaments/" + str(tournament_id) + "/brackets",
        data=bracket.get_table_dict(),
    )
    return Bracket(**bracket_data)


# Guilds
def get_guild(guild_id):
    guild_data = requests_wrapper("get", TOSURNAMENT_URL + "guilds/" + str(guild_id))
    if guild_data is None:
        return None
    return Guild(**guild_data)


def get_guild_by_discord_guild_id(guild_id):
    guild_data = requests_wrapper("get", TOSURNAMENT_URL + "guilds?guild_id=" + str(guild_id))
    if not guild_data["guilds"]:
        return None
    return Guild(**guild_data["guilds"][0])


def update_guild(guild):
    requests_wrapper("put", TOSURNAMENT_URL + "guilds/" + str(guild.id), data=guild.get_table_dict())
    return guild


def create_guild(guild):
    guild_data = requests_wrapper("post", TOSURNAMENT_URL + "guilds", data=guild.get_table_dict())
    return Guild(**guild_data)


# Schedules spreadsheets
def get_schedules_spreadsheet(tournament_id, bracket_id, schedules_spreadsheet_id):
    schedules_spreadsheet_data = requests_wrapper(
        "get",
        TOSURNAMENT_URL
        + "tournaments/"
        + str(tournament_id)
        + "/brackets/"
        + str(bracket_id)
        + "/schedules_spreadsheet/"
        + str(schedules_spreadsheet_id),
    )
    if schedules_spreadsheet_data is None:
        return None
    return SchedulesSpreadsheet(**schedules_spreadsheet_data)


def update_schedules_spreadsheet(tournament_id, bracket_id, schedules_spreadsheet):
    requests_wrapper(
        "put",
        TOSURNAMENT_URL
        + "tournaments/"
        + str(tournament_id)
        + "/brackets/"
        + str(bracket_id)
        + "/schedules_spreadsheet/"
        + str(schedules_spreadsheet.id),
        data=schedules_spreadsheet.get_table_dict(),
    )
    return schedules_spreadsheet


def create_schedules_spreadsheet(tournament_id, bracket_id, schedules_spreadsheet):
    schedules_spreadsheet_data = requests_wrapper(
        "post",
        TOSURNAMENT_URL
        + "tournaments/"
        + str(tournament_id)
        + "/brackets/"
        + str(bracket_id)
        + "/schedules_spreadsheet",
        data=schedules_spreadsheet.get_table_dict(),
    )
    return SchedulesSpreadsheet(**schedules_spreadsheet_data)


# Players spreadsheets
def get_players_spreadsheet(tournament_id, bracket_id, players_spreadsheet_id):
    players_spreadsheet_data = requests_wrapper(
        "get",
        TOSURNAMENT_URL
        + "tournaments/"
        + str(tournament_id)
        + "/brackets/"
        + str(bracket_id)
        + "/players_spreadsheet/"
        + str(players_spreadsheet_id),
    )
    if players_spreadsheet_data is None:
        return None
    return PlayersSpreadsheet(**players_spreadsheet_data)


def update_players_spreadsheet(tournament_id, bracket_id, players_spreadsheet):
    requests_wrapper(
        "put",
        TOSURNAMENT_URL
        + "tournaments/"
        + str(tournament_id)
        + "/brackets/"
        + str(bracket_id)
        + "/players_spreadsheet/"
        + str(players_spreadsheet.id),
        data=players_spreadsheet.get_table_dict(),
    )
    return players_spreadsheet


def create_players_spreadsheet(tournament_id, bracket_id, players_spreadsheet):
    players_spreadsheet_data = requests_wrapper(
        "post",
        TOSURNAMENT_URL + "tournaments/" + str(tournament_id) + "/brackets/" + str(bracket_id) + "/players_spreadsheet",
        data=players_spreadsheet.get_table_dict(),
    )
    return PlayersSpreadsheet(**players_spreadsheet_data)


# Qualifiers spreadsheets
def get_qualifiers_spreadsheet(tournament_id, bracket_id, qualifiers_spreadsheet_id):
    qualifiers_spreadsheet_data = requests_wrapper(
        "get",
        TOSURNAMENT_URL
        + "tournaments/"
        + str(tournament_id)
        + "/brackets/"
        + str(bracket_id)
        + "/qualifiers_spreadsheet/"
        + str(qualifiers_spreadsheet_id),
    )
    if qualifiers_spreadsheet_data is None:
        return None
    return QualifiersSpreadsheet(**qualifiers_spreadsheet_data)


def update_qualifiers_spreadsheet(tournament_id, bracket_id, qualifiers_spreadsheet):
    requests_wrapper(
        "put",
        TOSURNAMENT_URL
        + "tournaments/"
        + str(tournament_id)
        + "/brackets/"
        + str(bracket_id)
        + "/qualifiers_spreadsheet/"
        + str(qualifiers_spreadsheet.id),
        data=qualifiers_spreadsheet.get_table_dict(),
    )
    return qualifiers_spreadsheet


def create_qualifiers_spreadsheet(tournament_id, bracket_id, qualifiers_spreadsheet):
    qualifiers_spreadsheet_data = requests_wrapper(
        "post",
        TOSURNAMENT_URL
        + "tournaments/"
        + str(tournament_id)
        + "/brackets/"
        + str(bracket_id)
        + "/qualifiers_spreadsheet",
        data=qualifiers_spreadsheet.get_table_dict(),
    )
    return QualifiersSpreadsheet(**qualifiers_spreadsheet_data)


# Qualifiers results spreadsheets
def get_qualifiers_results_spreadsheet(tournament_id, bracket_id, qualifiers_results_spreadsheet_id):
    qualifiers_results_spreadsheet_data = requests_wrapper(
        "get",
        TOSURNAMENT_URL
        + "tournaments/"
        + str(tournament_id)
        + "/brackets/"
        + str(bracket_id)
        + "/qualifiers_results_spreadsheet/"
        + str(qualifiers_results_spreadsheet_id),
    )
    if qualifiers_results_spreadsheet_data is None:
        return None
    return QualifiersResultsSpreadsheet(**qualifiers_results_spreadsheet_data)


def update_qualifiers_results_spreadsheet(tournament_id, bracket_id, qualifiers_results_spreadsheet):
    requests_wrapper(
        "put",
        TOSURNAMENT_URL
        + "tournaments/"
        + str(tournament_id)
        + "/brackets/"
        + str(bracket_id)
        + "/qualifiers_results_spreadsheet/"
        + str(qualifiers_results_spreadsheet.id),
        data=qualifiers_results_spreadsheet.get_table_dict(),
    )
    return qualifiers_results_spreadsheet


def create_qualifiers_results_spreadsheet(tournament_id, bracket_id, qualifiers_results_spreadsheet):
    qualifiers_results_spreadsheet_data = requests_wrapper(
        "post",
        TOSURNAMENT_URL
        + "tournaments/"
        + str(tournament_id)
        + "/brackets/"
        + str(bracket_id)
        + "/qualifiers_results_spreadsheet",
        data=qualifiers_results_spreadsheet.get_table_dict(),
    )
    return QualifiersResultsSpreadsheet(**qualifiers_results_spreadsheet_data)


# Allowed reschedules
def get_allowed_reschedules(tournament_id):
    allowed_reschedules_data = requests_wrapper(
        "get", TOSURNAMENT_URL + "tournaments/" + str(tournament_id) + "/allowed_reschedules"
    )
    allowed_reschedules = []
    if allowed_reschedules_data is None:
        return allowed_reschedules
    for allowed_reschedule_data in allowed_reschedules_data["allowed_reschedules"]:
        allowed_reschedules.append(AllowedReschedule(**allowed_reschedule_data))
    return allowed_reschedules


def create_allowed_reschedule(tournament_id, allowed_reschedule):
    allowed_reschedule_data = requests_wrapper(
        "post",
        TOSURNAMENT_URL + "tournaments/" + str(tournament_id) + "/allowed_reschedules",
        data=allowed_reschedule.get_table_dict(),
    )
    return AllowedReschedule(**allowed_reschedule_data)


def delete_allowed_reschedule(tournament_id, match_id):
    requests_wrapper(
        "delete",
        TOSURNAMENT_URL + "tournaments/" + str(tournament_id) + "/allowed_reschedules?match_id=" + str(match_id),
    )


# Users
def get_user(user_id):
    user_data = requests_wrapper("get", TOSURNAMENT_URL + "users/" + str(user_id))
    if user_data is None:
        return None
    return User(**user_data)


def get_user_by_discord_user_id(user_id):
    user_data = requests_wrapper("get", TOSURNAMENT_URL + "users?discord_id=" + str(user_id))
    if not user_data["users"]:
        return None
    return User(**user_data["users"][0])


def get_user_by_osu_name(osu_name):
    user_data = requests_wrapper("get", TOSURNAMENT_URL + "users?osu_name_hash=" + str(osu_name))
    if not user_data:
        return None
    return User(**user_data)


def update_user(user):
    requests_wrapper("put", TOSURNAMENT_URL + "users/" + str(user.id), data=user.get_table_dict())
    return user


def create_user(user):
    user_data = requests_wrapper("post", TOSURNAMENT_URL + "users", data=user.get_table_dict())
    if user_data is None:
        return None
    return User(**user_data)
