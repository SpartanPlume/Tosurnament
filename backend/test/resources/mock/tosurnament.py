"""All Tosurnament module mock objects."""

from unittest import mock

from mysqldb_wrapper import crypt

from common.api.osu import User as OsuUser


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
    for key, value in fields.items():
        if not key.startswith("_") and (
            crypt.is_encrypted(self, key) or (isinstance(getattr(type(self)(), key), crypt.Id) and key != "id")
        ):
            print(key, getattr(self, key), getattr(other, key))
            if getattr(self, key) != getattr(other, key):
                return False
    return True


class Matcher:
    """Comparator of table class objects. To use with mock.call and to check against a call_args_list."""

    def __init__(self, table_obj):
        self.table_obj = table_obj

    def __eq__(self, other):
        return compare_table_objects(self.table_obj, other)


class BotMock:
    def __init__(self):
        self.session = SessionMock()


class RoleMock:
    def __init__(self, name, role_id=1):
        self.id = role_id
        self.name = name


USER_ID = 20934809
NOT_USER_ID = 18349804
USER_NAME = "User name"


class UserMock:
    def __init__(self, user_id=USER_ID):
        self.id = user_id
        self.roles = []
        self.display_name = USER_NAME


GUILD_ID = 325098354
NOT_GUILD_ID = 109843543


class GuildMock:
    OWNER_ID = 10293284854

    def __init__(self, guild_id=GUILD_ID):
        self.id = guild_id
        self.owner = UserMock(user_id=GuildMock.OWNER_ID)


class ChannelMock:
    def __init__(self, channel_id=1):
        self.id = channel_id


class CtxMock:
    def __init__(self, bot=BotMock(), author=UserMock(), guild=GuildMock()):
        self.bot = bot
        self.author = author
        self.guild = guild

        self.command = mock.Mock()
        self.command.name = ""


class EmojiMock:
    def __init__(self, name, emoji_id=1):
        self.id = emoji_id
        self.name = name


OSU_USER_ID = "2553166"
OSU_USER_NAME = "Spartan Plume"


class OsuMock:
    def __init__(self):
        self.get_user = mock.Mock()
        self.get_user.return_value = OsuUser({"user_id": OSU_USER_ID, "username": OSU_USER_NAME})


async def send_reply_side_effect(*args, **kwargs):
    return_mock = mock.Mock()
    return_mock.id = 0
    return return_mock


def mock_cog(cog):
    cog.send_reply = mock.MagicMock(side_effect=send_reply_side_effect)
    return cog
