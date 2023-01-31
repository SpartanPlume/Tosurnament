"""Team table"""

from encrypted_mysqldb.table import Table
from encrypted_mysqldb.fields import IdField, StrField, DatetimeField


class Team(Table):
    """Team class"""

    bracket_id = IdField()
    name = StrField()
    utc = StrField()
    created_at = DatetimeField()
