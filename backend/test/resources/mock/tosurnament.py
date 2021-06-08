"""All Tosurnament module mock objects."""

import copy
import json
import os
from unittest import mock

from mysqldb_wrapper import crypt

from common.utils import load_json
from common.api.spreadsheet import Spreadsheet, Worksheet, Cell
from common.databases.user import User


def query_side_effect_wrapper(session_mock):
    """Side effect for the query function, used to return the stubs in the storage."""

    def query_side_effect(table):
        tablename = table.__tablename__
        if tablename in session_mock.tables:
            query_mock = QueryMock(session_mock, session_mock.tables[tablename])
        else:
            query_mock = QueryMock(session_mock, [])
        return query_mock

    return query_side_effect


def add_side_effect_wrapper(session_mock):
    """Side effect for the add function, used to add an id to the input table."""

    def add_side_effect(table):
        tablename = table.__tablename__
        if tablename in session_mock.tables and len(session_mock.tables[tablename]) > 0:
            max_id = 0
            stub_id_present = False
            for stub in session_mock.tables[tablename]:
                if stub.id > max_id:
                    max_id = stub.id
                if stub.id == table.id:
                    stub_id_present = True
            if stub_id_present:
                table.id = max_id + 1
        else:
            session_mock.tables[tablename] = []
            if table.id < 1:
                table.id = 1
        session_mock.tables[tablename].append(table)
        return table

    return add_side_effect


def delete_side_effect_wrapper(session_mock):
    """Side effect for the add function, used to add an id to the input table."""

    def delete_side_effect(table):
        if table:
            tablename = table.__tablename__
            if tablename in session_mock.tables:
                stubs = session_mock.tables[tablename]
                for index, stub in enumerate(stubs):
                    if stub.id == table.id:
                        session_mock.tables[tablename].pop(index)
                        table.id = 0
                        return table
        return table

    return delete_side_effect


class QueryMock:
    def __init__(self, mock_session, stubs):
        self.mock_session = mock_session
        self.stubs = stubs

    def where(self, *args):
        for key, value in args:
            selected_stubs = []
            for stub in self.stubs:
                if getattr(stub, key) == value:
                    selected_stubs.append(stub)
            self.stubs = selected_stubs
        return self

    def first(self):
        if self.stubs:
            return self.stubs[0]
        return None

    def all(self):
        return self.stubs

    def delete(self):
        for stub in self.stubs:
            self.mock_session.delete(stub)


class SessionMock:
    """A mock for the session. Includes utility functions to simulate a storage."""

    def __init__(self):
        self.tables = {}
        self.add = mock.Mock(side_effect=add_side_effect_wrapper(self))
        self.update = mock.Mock(side_effect=(lambda x: x))
        self.query = mock.MagicMock(side_effect=query_side_effect_wrapper(self))
        self.delete = mock.MagicMock(side_effect=delete_side_effect_wrapper(self))

    def add_stub(self, stub):
        """Adds a stub in the mock. The added stubs will be used when retrieving an object."""
        stub._session = self
        add_side_effect_wrapper(self)(stub)

    def reset_stub(self, table):
        """Resets all the stubs of the table."""
        self.tables[table.__tablename__] = []


def compare_table_objects(self, other):
    """Compares 2 table class objects."""
    if not type(self) == type(other):
        return False
    fields = vars(self)
    for key in fields.keys():
        if not key.startswith("_") and (
            crypt.is_encrypted(self, key) or (isinstance(getattr(type(self)(), key), crypt.Id) and key != "id")
        ):
            if getattr(self, key) != getattr(other, key):
                print(key + ": (expected) " + str(getattr(self, key)) + " vs (current) " + str(getattr(other, key)))
                return False
    return True


class Matcher:
    """Comparator of table class objects. To use with mock.call and to check against a call_args_list."""

    def __init__(self, table_obj):
        self.table_obj = table_obj

    def __eq__(self, other):
        return compare_table_objects(self.table_obj, other)


class BaseMock:
    def __eq__(self, other):
        if other == mock.ANY:
            return True
        for key in vars(self).keys():
            if not key.startswith("_"):
                if getattr(self, key) != getattr(other, key):
                    return False
        return True


class MessageMock(BaseMock):
    def __init__(self, message_id):
        self.id = message_id
        self.delete = mock.AsyncMock()


DEFAULT_MESSAGE_MOCK = MessageMock(3249076)
SETUP_MESSAGE_MOCK = MessageMock(234098)
PREVIEW_MESSAGE_MOCK = MessageMock(824598)


class ChannelMock(BaseMock):
    def __init__(self, channel_id, messages=None):
        self.id = channel_id
        if messages is None:
            self.messages = [DEFAULT_MESSAGE_MOCK, SETUP_MESSAGE_MOCK, PREVIEW_MESSAGE_MOCK]
        else:
            self.messages = messages

    async def fetch_message(self, message_id):
        for message in self.messages:
            if message.id == message_id:
                return message
        return None


DEFAULT_CHANNEL_MOCK = ChannelMock(890342)
SETUP_CHANNEL_MOCK = ChannelMock(79052)
STAFF_CHANNEL_MOCK = ChannelMock(3245098)
DM_CHANNEL_MOCK = ChannelMock(453678)


class BotMock(BaseMock):
    def __init__(self, channels=None):
        self.session = SessionMock()
        self.command_prefix = ";"
        self.loop = mock.MagicMock()
        self.on_verified_user = mock.AsyncMock()
        self.tasks = []
        self.languages = ["en"]
        self._strings = []
        if channels is None:
            self.channels = [DEFAULT_CHANNEL_MOCK, SETUP_CHANNEL_MOCK, STAFF_CHANNEL_MOCK]
        else:
            self.channels = channels

    @property
    def strings(self):
        if not self._strings:
            self._strings = load_json.load_directory("bot/replies")
            self._strings = load_json.replace_placeholders(self.strings)
        return self._strings

    def get_channel(self, channel_id):
        for channel in self.channels:
            if channel.id == channel_id:
                return channel
        return None


class RoleMock(BaseMock):
    def __init__(self, name, role_id=1):
        self.id = role_id
        self.name = name


USER_NAME = "User name"
USER_TAG = "User name#1234"


class UserMock(BaseMock):
    def __init__(self, user_id=20934809, user_name=USER_NAME, user_tag=USER_TAG, roles=[]):
        self.id = user_id
        self.roles = roles
        self.display_name = user_name
        self.mention = user_name
        self.user_tag = user_tag
        self.dm_channel = None
        self.add_roles = mock.AsyncMock()
        self.edit = mock.AsyncMock()

    def __str__(self):
        return self.user_tag

    async def create_dm(self):
        self.dm_channel = DM_CHANNEL_MOCK
        return self.dm_channel


DEFAULT_USER_MOCK = UserMock(20934809, "User name", "User name#1234")
DEFAULT_USER_STUB = User(
    discord_id=DEFAULT_USER_MOCK.id,
    discord_id_snowflake=DEFAULT_USER_MOCK.id,
    osu_id="2553166",
    verified=True,
    osu_name="Spartan Plume",
    osu_name_hash="Spartan Plume",
)

GUILD_OWNER_USER_MOCK = UserMock(10293284854, "Guild owner", "Guild owner#1234")

ANOTHER_USER_MOCK = UserMock(18349804, "Another User name", "Another User name#1234")
ANOTHER_USER_STUB = User(
    discord_id=ANOTHER_USER_MOCK.id,
    discord_id_snowflake=ANOTHER_USER_MOCK.id,
    osu_id=str(ANOTHER_USER_MOCK.id),
    verified=True,
    osu_name=ANOTHER_USER_MOCK.display_name,
    osu_name_hash=ANOTHER_USER_MOCK.display_name,
)


PLAYER_ROLE_MOCK = RoleMock("Player", 234567)
PLAYER_USER_MOCK = UserMock(43590, PLAYER_ROLE_MOCK.name, roles=[PLAYER_ROLE_MOCK])
PLAYER_USER_STUB = User(
    discord_id=PLAYER_USER_MOCK.id,
    discord_id_snowflake=PLAYER_USER_MOCK.id,
    osu_id=str(PLAYER_USER_MOCK.id),
    verified=True,
    osu_name=PLAYER_USER_MOCK.display_name,
    osu_name_hash=PLAYER_USER_MOCK.display_name,
)

REFEREE_ROLE_MOCK = RoleMock("Referee", 987245)
REFEREE_USER_MOCK = UserMock(234789, REFEREE_ROLE_MOCK.name, roles=[REFEREE_ROLE_MOCK])
REFEREE_USER_STUB = User(
    discord_id=REFEREE_USER_MOCK.id,
    discord_id_snowflake=REFEREE_USER_MOCK.id,
    osu_id=str(REFEREE_USER_MOCK.id),
    verified=True,
    osu_name=REFEREE_USER_MOCK.display_name,
    osu_name_hash=REFEREE_USER_MOCK.display_name,
)

STREAMER_ROLE_MOCK = RoleMock("Streamer", 789245)
STREAMER_USER_MOCK = UserMock(890234, STREAMER_ROLE_MOCK.name, roles=[STREAMER_ROLE_MOCK])
STREAMER_USER_STUB = User(
    discord_id=STREAMER_USER_MOCK.id,
    discord_id_snowflake=STREAMER_USER_MOCK.id,
    osu_id=str(STREAMER_USER_MOCK.id),
    verified=True,
    osu_name=STREAMER_USER_MOCK.display_name,
    osu_name_hash=STREAMER_USER_MOCK.display_name,
)

COMMENTATOR_ROLE_MOCK = RoleMock("Commentator", 43789)
COMMENTATOR_USER_MOCK = UserMock(345789, "Commentator 1", roles=[COMMENTATOR_ROLE_MOCK])
COMMENTATOR_USER_STUB = User(
    discord_id=COMMENTATOR_USER_MOCK.id,
    discord_id_snowflake=COMMENTATOR_USER_MOCK.id,
    osu_id=str(COMMENTATOR_USER_MOCK.id),
    verified=True,
    osu_name=COMMENTATOR_USER_MOCK.display_name,
    osu_name_hash=COMMENTATOR_USER_MOCK.display_name,
)

COMMENTATOR2_USER_MOCK = UserMock(345790, "Commentator 2", roles=[COMMENTATOR_ROLE_MOCK])
COMMENTATOR2_USER_STUB = User(
    discord_id=COMMENTATOR2_USER_MOCK.id,
    discord_id_snowflake=COMMENTATOR2_USER_MOCK.id,
    osu_id=str(COMMENTATOR2_USER_MOCK.id),
    verified=True,
    osu_name=COMMENTATOR2_USER_MOCK.display_name,
    osu_name_hash=COMMENTATOR2_USER_MOCK.display_name,
)


class GuildMock(BaseMock):
    def __init__(self, guild_id, roles=None):
        self.id = guild_id
        self.owner = GUILD_OWNER_USER_MOCK
        if roles is None:
            self.roles = [PLAYER_ROLE_MOCK, REFEREE_ROLE_MOCK, STREAMER_ROLE_MOCK, COMMENTATOR_ROLE_MOCK]
        else:
            self.roles = roles
        self.members = [
            DEFAULT_USER_MOCK,
            ANOTHER_USER_MOCK,
            PLAYER_USER_MOCK,
            REFEREE_USER_MOCK,
            STREAMER_USER_MOCK,
            COMMENTATOR_USER_MOCK,
            COMMENTATOR2_USER_MOCK,
        ]

    def get_member(self, user_id):
        for member in self.members:
            if member.id == user_id:
                return member
        return UserMock(user_id=user_id)

    def get_member_named(self, user_name):
        for member in self.members:
            if member.display_name == user_name:
                return member
        return UserMock(user_name=user_name)


DEFAULT_GUILD_MOCK = GuildMock(325098354)
ANOTHER_GUILD_MOCK = GuildMock(109843543)


class CommandMock(BaseMock):
    def __init__(self, cog_name="", name=""):
        self.cog_name = cog_name
        self.name = name


class CtxMock(BaseMock):
    def __init__(
        self,
        bot=BotMock(),
        author=DEFAULT_USER_MOCK,
        guild=DEFAULT_GUILD_MOCK,
        channel=DEFAULT_CHANNEL_MOCK,
        command=CommandMock(),
    ):
        self.bot = bot
        self.author = author
        self.guild = guild
        self.command = command
        self.message = DEFAULT_MESSAGE_MOCK
        self.channel = channel
        self.send = mock.AsyncMock()


class EmojiMock(BaseMock):
    def __init__(self, name, emoji_id=1):
        self.id = emoji_id
        self.name = name


OSU_USER_ID = "2553166"
OSU_USER_NAME = "Spartan Plume"


class OsuMock:
    class OsuUser:
        def __init__(self):
            self.id = OSU_USER_ID
            self.name = OSU_USER_NAME
            self.rank = "12345"
            self.pp = "1234"
            self.country = "fr"

    def __init__(self):
        self.get_user = mock.Mock()
        self.get_user.return_value = OsuMock.OsuUser()
        self.get_from_string = mock.Mock(side_effect=(lambda name: name))


async def send_reply_side_effect(*args, **kwargs):
    return_mock = mock.Mock()
    return_mock.id = 0
    return_mock.add_reaction = mock.AsyncMock()
    return return_mock


def mock_cog(cog):
    cog.send_reply = mock.MagicMock(side_effect=send_reply_side_effect)
    cog.on_cog_command_error = mock.AsyncMock()
    return cog


def create_worksheet(index, name, values):
    cells = []
    for y, row in enumerate(values):
        cells.append([])
        for x, value in enumerate(row):
            cells[y].append(Cell(x, y, value))
    return Worksheet(index, name, cells)


def load_spreadsheet(path):
    worksheets = []
    with open(path) as f:
        spreadsheet_data = json.load(f)
    spreadsheet = Spreadsheet(spreadsheet_data["spreadsheet_id"])
    for i, worksheet_data in enumerate(spreadsheet_data["worksheets"]):
        worksheets.append(create_worksheet(i, worksheet_data["name"], worksheet_data["cells"]))
    spreadsheet.worksheets = worksheets
    # TODO mock pickles
    spreadsheet.update_pickle()


def setup_spreadsheets():
    for root, _, files in os.walk("test/resources/spreadsheets"):
        for filename in files:
            if filename.endswith(".json"):
                load_spreadsheet(os.path.join(root, filename))
