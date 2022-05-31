"""Token class"""

from encrypted_mysqldb.table import Table
from encrypted_mysqldb.fields import StrField, HashField, DatetimeField


class Token(Table):
    """Token class"""

    session_token = HashField()
    discord_user_id = StrField()
    access_token = StrField()
    token_type = StrField()
    access_token_expiry_date = DatetimeField()
    refresh_token = StrField()
    scope = StrField()
    expiry_date = DatetimeField()
