"""Post result message table"""

from mysqldb_wrapper import Base, Id


class PostResultMessage(Base):
    """Post result message class"""

    __tablename__ = "post_result_message"

    id = Id()
    tournament_id = Id()
    bracket_id = Id()
    referee_id = bytes()
    message_id = int()  # TODO maybe use for update ?
    preview_message_id = int()
    setup_message_id = int()
    step = int(1)
    match_id = str()
    score_team1 = int(0)
    score_team2 = int(0)
    best_of = int(0)
    roll_team1 = int(0)
    roll_team2 = int(0)
    n_warmup = int(0)
    mp_links = str("")
    bans_team1 = str("")
    bans_team2 = str("")
    tb_bans_team1 = str("")
    tb_bans_team2 = str("")
    created_at = int()
