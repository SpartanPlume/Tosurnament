"""Guild table"""

from mysqldb_wrapper import Base, Id


class Guild(Base):
    """Guild class"""

    __tablename__ = "guild"

    id = Id()
    guild_id = bytes()
    guild_id_snowflake = str()
    guild_id_snowflake_str = str()
    verified_role_id = str()
    verified_role_id_str = str()
    admin_role_id = str()
    admin_role_id_str = str()
    last_notification_date = str()
    language = str()
    created_at = int()
    updated_at = int()
