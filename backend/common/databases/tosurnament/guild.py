"""Guild table"""

from mysqldb_wrapper import Base, Id


class Guild(Base):
    """Guild class"""

    __tablename__ = "guild"

    id = Id()
    guild_id = bytes()
    guild_id_snowflake = int()
    verified_role_id = int()
    admin_role_id = int()
    last_notification_date = str()
    language = str()
    created_at = int()
    updated_at = int()
