"""Guild table"""

from encrypted_mysqldb.table import Table
from encrypted_mysqldb.fields import StrField, DatetimeField, HashField


class Guild(Table):
    """Guild class"""

    guild_id = HashField()
    guild_id_snowflake = StrField()
    verified_role_id = StrField()
    admin_role_id = StrField()
    last_notification_date = DatetimeField()
    language = StrField()
    created_at = DatetimeField()
    updated_at = DatetimeField()
