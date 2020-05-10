"""osu! API wrapper"""

import collections
import re
import requests
from common.config import constants

URL_LOGO = "https://osu.ppy.sh/images/layout/osu-logo.png"
URL_BEATMAP = "https://osu.ppy.sh/b/"
URL_USER = "https://osu.ppy.sh/u/"
URL_THUMBNAIL = "https://b.ppy.sh/thumb/"
URL_PROFILE_PICTURE = "https://a.ppy.sh/"

URL_API_BASE = "https://osu.ppy.sh/api/"
URL_GET_BEATMAPS = URL_API_BASE + "get_beatmaps"
URL_GET_USER = URL_API_BASE + "get_user"
URL_GET_SCORES = URL_API_BASE + "get_scores"
URL_GET_USER_BEST = URL_API_BASE + "get_user_best"
URL_GET_USER_RECENT = URL_API_BASE + "get_user_recent"
URL_GET_MATCH = URL_API_BASE + "get_match"

KEY_API_KEY = "k"
KEY_USER = "u"
KEY_BEATMAP = "b"
KEY_MATCH = "mp"
KEY_LIMIT = "limit"


class Mod:
    """Enum of mods"""

    NoFail = 1
    Easy = 2
    TouchDevice = 4
    Hidden = 8
    HardRock = 16
    SuddenDeath = 32
    DoubleTime = 64
    Relax = 128
    HalfTime = 256
    Nightcore = 512  # Only set along with DoubleTime. i.e: NC only gives 576
    Flashlight = 1024
    # Autoplay = 2048
    SpunOut = 4096
    # Relax2 = 8192	# Autopilot?
    Perfect = 16384  # Only set along with SuddenDeath. i.e: PF only gives 16416
    Key4 = 32768
    Key5 = 65536
    Key6 = 131072
    Key7 = 262144
    Key8 = 524288
    FadeIn = 1048576
    # Random = 2097152
    # Cinema = 4194304
    # Target = 8388608
    Key9 = 16777216
    KeyCoop = 33554432
    Key1 = 67108864
    Key3 = 134217728
    Key2 = 268435456
    ScoreV2 = 536870912
    LastMod = 1073741824
    # KeyMod = Key4 | Key5 | Key6 | Key7 | Key8
    # FreeModAllowed = NoFail | Easy | Hidden | HardRock
    # | SuddenDeath | Flashlight | FadeIn | Relax | Relax2 | SpunOut | keyMod
    # ScoreIncreaseMods = Hidden | HardRock | DoubleTime | Flashlight | FadeIn

    def __setattr__(self, key, value):
        if hasattr(self, key):
            raise AttributeError("can't set attribute")
        super().__setattr__(key, value)


MOD_ACRONYMS = collections.OrderedDict(
    {
        "NoFail": "NF",
        "Easy": "EZ",
        "TouchDevice": "TD",
        "Hidden": "HD",
        "HardRock": "HR",
        "SuddenDeath": "SD",
        "DoubleTime": "DT",
        "Relax": "RX",
        "HalfTime": "HT",
        "Nightcore": "NC",
        "Flashlight": "FL",
        # "Autoplay": "",
        "SpunOut": "SO",
        "Relax2": "AP",
        "Perfect": "PF",
        "Key4": "4K",
        "Key5": "5K",
        "Key6": "6K",
        "Key7": "7K",
        "Key8": "8K",
        "FadeIn": "FI",
        # "Random": "",
        # "Cinema": "",
        # "Target": "",
        "Key9": "9K",
        "KeyCoop": "KC",
        "Key1": "1K",
        "Key3": "3K",
        "Key2": "2K",
        "ScoreV2": "SV2",
        # "LastMod": "",
    }
)

MOD_ORDER = [
    "None",
    "TD",
    "SO",
    "NF",
    "EZ",
    "HD",
    "HR",
    "FI",
    "DT",
    "NC",
    "HT",
    "FL",
    "PF",
    "SD",
    "RX",
    "AP",
    "1K",
    "2K",
    "3K",
    "4K",
    "5K",
    "6K",
    "7K",
    "8K",
    "9K",
    "KC",
    "SV2",
]


class BitField(int):
    """Stores an int and converts it to a string corresponding to an enum"""

    def to_string(self, enum):
        return " ".join([i for i, j in enum._asdict().items() if self & j])


def build_mp_link(mp_id):
    return "https://osu.ppy.sh/community/matches/" + mp_id + "\n"


def build_mp_links(mp_ids):
    mp_links = []
    for mp_id in mp_ids:
        mp_links.append("https://osu.ppy.sh/community/matches/" + mp_id)
    return mp_links


def get_mods(enabled_mods):
    """Gets a string of all enabled mods from bitfield"""
    if not isinstance(enabled_mods, int):
        return enabled_mods
    bit_field = BitField(enabled_mods)
    pattern = re.compile("|".join(MOD_ACRONYMS.keys()))
    mods = pattern.sub(lambda x: MOD_ACRONYMS[x.group()], bit_field.to_string(Mod))
    if not mods or mods == "":
        return "No Mods"
    else:
        if "NC" in mods:
            mods = mods.replace("DT ", "")
            mods = mods.replace(" DT", "")
        if "PF" in mods:
            mods = mods.replace("SD ", "")
            mods = mods.replace(" SD", "")
    return " ".join(sorted(mods.split(" "), key=(lambda x: MOD_ORDER.index(x))))


class Base:
    """Base class"""

    def __init__(self, dic={}):
        for key, value in vars(self.__class__).items():
            if str(value) in dic:
                if isinstance(value, Base):
                    dic_value = dic[str(value)]
                    if isinstance(dic_value, list):
                        array = []
                        for item in dic_value:
                            array.append(type(value)(item))
                        object.__setattr__(self, key, array)
                    else:
                        object.__setattr__(self, key, type(value)(dic_value))
                else:
                    object.__setattr__(self, key, dic[value])

    def __setattr__(self, key, value):
        if hasattr(self, key):
            raise AttributeError("can't set attribute")
        super().__setattr__(key, value)


class User(Base):
    """Contains fields of a user"""

    class Event(Base):
        """Contains fields of an event"""

        def __str__(self):
            return "events"

        display_html = "display_html"
        beatmap_id = "beatmap_id"
        beatmapset_id = "beatmapset_id"
        date = "date"
        epicfactor = "epicfactor"

    id = "user_id"
    name = "username"
    count_300 = "count300"
    count_100 = "count100"
    count_50 = "count50"
    playcount = "playcount"
    ranked_score = "ranked_score"
    total_score = "total_score"
    rank = "pp_rank"
    level = "level"
    pp = "pp_raw"
    accuracy = "accuracy"
    countSS = "count_rank_ss"
    countS = "count_rank_s"
    countA = "count_rank_a"
    country = "country"
    country_rank = "pp_country_rank"
    events = Event()


class Beatmap(Base):
    """Contains fields of a beatmap"""

    id = "beatmap_id"
    beatmapset_id = "beatmapset_id"
    md5 = "file_md5"
    approved = "approved"
    approved_date = "approved_date"
    last_update = "last_update"
    artist = "artist"
    title = "title"
    version = "version"
    creator = "creator"
    bpm = "bpm"
    stars = "difficultyrating"
    cs = "diff_size"
    od = "diff_overall"
    ar = "diff_approach"
    hp = "diff_drain"
    mode = "mode"
    total_length = "total_length"
    hit_length = "hit_length"
    max_combo = "max_combo"
    source = "source"
    genre_id = "genre_id"
    language_id = "language_id"
    tags = "tags"
    favorite_count = "favorite_count"
    playcount = "playcount"
    passcount = "passcount"

    RANK_STATUS = {
        "-2": "Graveyard",
        "-1": "WIP",
        "0": "Pending",
        "1": "Ranked",
        "2": "Approved",
        "3": "Qualified",
        "4": "Loved",
    }

    def __init__(self, dic={}):
        super().__init__(dic)
        object.__setattr__(self, "approved", Beatmap.RANK_STATUS[self.approved])


class Score(Base):
    """Contains fields of a score"""

    beatmap_id = "beatmap_id"
    score = "score"
    username = "username"
    user_id = "user_id"
    count_300 = "count300"
    count_katu = "countkatu"
    count_100 = "count100"
    count_geki = "countgeki"
    count_50 = "count50"
    count_miss = "countmiss"
    max_combo = "maxcombo"
    perfect = "perfect"
    enabled_mods = "enabled_mods"
    date = "date"
    rank = "rank"
    pp = "pp"

    def __init__(self, dic={}):
        super().__init__(dic)
        object.__setattr__(self, "enabled_mods", get_mods(self.enabled_mods))


class Match(Base):
    """Contains fields of a match"""

    class MatchData(Base):
        def __str__(self):
            return "match"

        id = "match_id"
        name = "name"
        start_time = "start_time"
        end_time = "end_time"

    class Game(Base):
        """Contains fields of a game"""

        def __init__(self, dic={}):
            super().__init__(dic)
            object.__setattr__(self, "mods", get_mods(self.mods))

        def __str__(self):
            return "games"

        class GameScore(Base):
            """Contains fields of a game score"""

            def __str__(self):
                return "scores"

            slot = "slot"
            team = "team"
            user_id = "user_id"
            score = "score"
            max_combo = "maxcombo"
            rank = "rank"
            count_300 = "count300"
            count_katu = "countkatu"
            count_100 = "count100"
            count_geki = "countgeki"
            count_50 = "count50"
            count_miss = "countmiss"
            perfect = "perfect"
            passed = "pass"

        id = "game_id"
        start_time = "start_time"
        end_time = "end_time"
        beatmap_id = "beatmap_id"
        play_mode = "play_mode"
        match_type = "match_type"
        scoring_type = "scoring_type"
        team_type = "team_type"
        mods = "mods"
        scores = GameScore()

    match = MatchData()
    games = Game()


def get_from_string(string):
    """Returns the id or name of a user from string"""
    if "/" in string:
        string = string.rstrip("/")
        string = string.split("/")[-1]
        string = string.split("&")[0]
        string = string.split("#")[0]
    return string


def get_user(user):
    """Returns a User"""
    payload = {KEY_API_KEY: constants.OSU_API_KEY, KEY_USER: get_from_string(user)}
    request = requests.get(URL_GET_USER, params=payload)
    if request.status_code != 200:
        return None
    try:
        users = request.json()
    except ValueError:
        return None
    if len(users) > 0:
        return User(users[0])
    return None


def get_beatmap(beatmap_id):
    """Returns a Beatmap"""
    payload = {
        KEY_API_KEY: constants.OSU_API_KEY,
        KEY_BEATMAP: get_from_string(beatmap_id),
    }
    request = requests.get(URL_GET_BEATMAPS, params=payload)
    if request.status_code != 200:
        return None
    try:
        beatmaps = request.json()
    except ValueError:
        return None
    if len(beatmaps) > 0:
        return Beatmap(beatmaps[0])
    return None


def get_scores(beatmap_id, user=None, limit=50):
    """Returns a list of Scores of the best scores on the beatmap"""
    payload = {
        KEY_API_KEY: constants.OSU_API_KEY,
        KEY_BEATMAP: get_from_string(beatmap_id),
        KEY_LIMIT: limit,
    }
    if user:
        payload[KEY_USER] = get_from_string(user)
    request = requests.get(URL_GET_SCORES, params=payload)
    if request.status_code != 200:
        return []
    try:
        scores = request.json()
    except ValueError:
        return []
    if len(scores) > 0:
        array = []
        for score in scores:
            array.append(Score(score))
        return array
    return []


def get_user_best(user, limit=10):
    """Returns a list of Scores of the best scores of the user"""
    payload = {
        KEY_API_KEY: constants.OSU_API_KEY,
        KEY_USER: get_from_string(user),
        KEY_LIMIT: limit,
    }
    request = requests.get(URL_GET_USER_BEST, params=payload)
    if request.status_code != 200:
        return []
    try:
        scores = request.json()
    except ValueError:
        return []
    if len(scores) > 0:
        array = []
        for score in scores:
            array.append(Score(score))
        return array
    return []


def get_user_recent(user, limit=10):
    """Returns a list of Scores of the recent scores of the user"""
    payload = {
        KEY_API_KEY: constants.OSU_API_KEY,
        KEY_USER: get_from_string(user),
        KEY_LIMIT: limit,
    }
    request = requests.get(URL_GET_USER_RECENT, params=payload)
    if request.status_code != 200:
        return []
    try:
        scores = request.json()
    except ValueError:
        return []
    if len(scores) > 0:
        array = []
        for score in scores:
            array.append(Score(score))
        return array
    return []


def get_match(match_id):
    """Returns Score dicts list of the recent scores of the user"""
    payload = {KEY_API_KEY: constants.OSU_API_KEY, KEY_MATCH: get_from_string(match_id)}
    request = requests.get(URL_GET_MATCH, params=payload)
    if request.status_code != 200:
        return None
    try:
        matches = request.json()
    except ValueError:
        return None
    return Match(matches)


def usernames_to_ids(names):
    ids = []
    for name in names:
        osu_user = get_user(name)
        if not osu_user:
            return None
        ids.append(osu_user.id)
    return ids
