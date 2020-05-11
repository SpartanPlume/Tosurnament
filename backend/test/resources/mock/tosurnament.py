"""All Tosurnament module mock objects."""

from unittest import mock

from mysqldb_wrapper import crypt

from common.api.osu import User as OsuUser


def query_side_effect_wrapper(session_mock):
    """Side effect for the query function, used to return the stubs in the storage."""

    def query_side_effect(table):
        query_mock = mock.Mock()
        tablename = table.__tablename__
        if tablename in session_mock.tables and len(session_mock.tables[tablename]) > 0:
            query_mock.first.return_value = session_mock.tables[tablename][0]
            query_mock.all.return_value = session_mock.tables[tablename]
        else:
            query_mock.first.return_value = None
            query_mock.all.return_value = []
        query_mock.where.return_value = query_mock
        return query_mock

    return query_side_effect


def add_side_effect_wrapper(session_mock):
    """Side effect for the add function, used to add an id to the input table."""

    def add_side_effect(table):
        tablename = table.__tablename__
        if tablename in session_mock.tables and len(session_mock.tables[tablename]) > 0:
            stubs = session_mock.tables[tablename]
            max_id = max(stub.id for stub in stubs)
            table.id = max_id + 1
        else:
            table.id = 1
        return table

    return add_side_effect


class SessionMock:
    """A mock for the session. Includes utility functions to simulate a storage."""

    def __init__(self):
        self.tables = {}
        self.add = mock.Mock(side_effect=add_side_effect_wrapper(self))
        self.update = mock.Mock(side_effect=(lambda x: x))
        self.query = mock.MagicMock(side_effect=query_side_effect_wrapper(self))

    def add_stub(self, stub):
        """Adds a stub in the mock. The added stubs will be used when retrieving an object."""
        tablename = stub.__tablename__
        if tablename in self.tables:
            self.tables[tablename].append(stub)
        else:
            self.tables[tablename] = [stub]

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
    def __init__(self, role_id, name):
        self.id = role_id
        self.name = name


class CtxMock:
    def __init__(self, bot=BotMock()):
        self.bot = bot

        self.author = mock.Mock()
        self.author.id = 1
        self.author.roles = []

        self.guild = mock.Mock()
        self.guild.id = 1

        self.command = mock.Mock()
        self.command.name = ""


USER_ID = "2553166"
USER_NAME = "Spartan Plume"


class OsuMock:
    def __init__(self):
        self.get_user = mock.Mock()
        self.get_user.return_value = OsuUser({"user_id": USER_ID, "username": USER_NAME})


async def send_reply_side_effect(*args, **kwargs):
    return_mock = mock.Mock()
    return_mock.id = 0
    return return_mock


def mock_cog(cog):
    cog.send_reply = mock.MagicMock(side_effect=send_reply_side_effect)
    return cog
