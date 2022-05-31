"""Post result message table"""

from encrypted_mysqldb.fields import IdField, StrField, IntField
from .base_message import BaseAuthorLockMessage


class PostResultMessage(BaseAuthorLockMessage):
    """Post result message class"""

    tournament_id = IdField()
    bracket_id = IdField()
    preview_message_id = IntField()
    setup_message_id = IntField()
    step = IntField(1)
    match_id = StrField()
    score_team1 = IntField()
    score_team2 = IntField()
    best_of = IntField()
    roll_team1 = IntField()
    roll_team2 = IntField()
    n_warmup = IntField()
    mp_links = StrField()
    bans_team1 = StrField()
    bans_team2 = StrField()
    tb_bans_team1 = StrField()
    tb_bans_team2 = StrField()
