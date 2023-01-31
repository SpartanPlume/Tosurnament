"""User table"""

from encrypted_mysqldb.table import Table
from encrypted_mysqldb.fields import StrField, HashField, BoolField, IntField


class User(Table):
    """User class"""

    discord_id = HashField()
    discord_id_snowflake = StrField()
    osu_id = StrField()
    verified = BoolField()
    code = HashField()
    osu_name = StrField()
    osu_name_hash = HashField()
    osu_previous_name = StrField()
    osu_std_rank = IntField()
    osu_taiko_rank = IntField()
    osu_ctb_rank = IntField()
    osu_mania_rank = IntField()
    country = StrField()
