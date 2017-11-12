"""osu! API wrapper"""

import collections
from decimal import Decimal
import re
import requests
import helpers.class_readonly as class_readonly
import helpers.bitfield as bitfield
import constants

URL_LOGO = "https://osu.ppy.sh/images/layout/osu-logo.png"
URL_BEATMAP = "https://osu.ppy.sh/b/"
URL_USER = "https://osu.ppy.sh/u/"
URL_THUMBNAIL = "https://b.ppy.sh/thumb/"
URL_PROFILE_PICTURE = "https://a.ppy.sh/"

URL_GET_BEATMAPS = "https://osu.ppy.sh/api/get_beatmaps"
URL_GET_USER = "https://osu.ppy.sh/api/get_user"
URL_GET_SCORES = "https://osu.ppy.sh/api/get_scores"
URL_GET_USER_BEST = "https://osu.ppy.sh/api/get_user_best"
URL_GET_USER_RECENT = "https://osu.ppy.sh/api/get_user_recent"

KEY_API_KEY = 'k'
KEY_USER = 'u'
KEY_BEATMAP = 'b'
KEY_LIMIT = 'limit'

class OsuApi():
    """Uses to do API call"""
    def __init__(self, user):
        pass

    @staticmethod
    def get_beatmaps(beatmap_id):
        """Returns a User dict"""
        payload = {KEY_API_KEY: constants.OSU_API_KEY, KEY_BEATMAP: beatmap_id}
        request = requests.get(URL_GET_BEATMAPS, params=payload)
        if request.status_code != 200:
            return {}
        try:
            beatmaps = request.json()
        except ValueError:
            return {}
        return beatmaps

    @staticmethod
    def get_user(user):
        """Returns a User dict"""
        payload = {KEY_API_KEY: constants.OSU_API_KEY, KEY_USER: user}
        request = requests.get(URL_GET_USER, params=payload)
        if request.status_code != 200:
            return {}
        try:
            users = request.json()
        except ValueError:
            return {}
        return users

    @staticmethod
    def get_scores(beatmap_id, user=None, limit=50):
        """Returns Score dicts list of the best scores on the beatmap"""
        payload = {KEY_API_KEY: constants.OSU_API_KEY, KEY_BEATMAP: beatmap_id, KEY_LIMIT: limit}
        if user:
            payload[KEY_USER] = user
        request = requests.get(URL_GET_SCORES, params=payload)
        if request.status_code != 200:
            return {}
        try:
            scores = request.json()
        except ValueError:
            return {}
        return scores

    @staticmethod
    def get_user_best(user, limit=10):
        """Returns Score dicts list of the best scores of the user"""
        payload = {KEY_API_KEY: constants.OSU_API_KEY, KEY_USER: user, KEY_LIMIT: limit}
        request = requests.get(URL_GET_USER_BEST, params=payload)
        if request.status_code != 200:
            return {}
        try:
            scores = request.json()
        except ValueError:
            return {}
        return scores

    @staticmethod
    def get_user_recent(user, limit=10):
        """Returns Score dicts list of the recent scores of the user"""
        payload = {KEY_API_KEY: constants.OSU_API_KEY, KEY_USER: user, KEY_LIMIT: limit}
        request = requests.get(URL_GET_USER_RECENT, params=payload)
        if request.status_code != 200:
            return {}
        try:
            scores = request.json()
        except ValueError:
            return {}
        return scores

RANK = {
    'XH' : 'SS',
    'X' : 'SS',
    'SH' : 'S',
    'S' : 'S',
    'A' : 'A',
    'B' : 'B',
    'C' : 'C',
    'D' : 'D'
}

class Mod:
    """Enum of mods"""
    NoFail = 1
    Easy = 2
    #NoVideo = 4
    Hidden = 8
    HardRock = 16
    SuddenDeath = 32
    DoubleTime = 64
    Relax = 128
    HalfTime = 256
    Nightcore = 512 # Only set along with DoubleTime. i.e: NC only gives 576
    Flashlight = 1024
    #Autoplay = 2048
    SpunOut = 4096
    #Relax2 = 8192	# Autopilot?
    Perfect = 16384 # Only set along with SuddenDeath. i.e: PF only gives 16416
    Key4 = 32768
    Key5 = 65536
    Key6 = 131072
    Key7 = 262144
    Key8 = 524288
    #keyMod = Key4 | Key5 | Key6 | Key7 | Key8
    FadeIn = 1048576
    #Random = 2097152
    #LastMod = 4194304
    #FreeModAllowed = NoFail | Easy | Hidden | HardRock | SuddenDeath | Flashlight | FadeIn | Relax | Relax2 | SpunOut | keyMod
    Key9 = 16777216
    Key10 = 33554432
    Key1 = 67108864
    Key3 = 134217728
    Key2 = 268435456

Mod = class_readonly.readonly(Mod)

MOD_ACRONYMS = collections.OrderedDict({
    "NoFail": "NF",
    "Easy": "EZ",
    #"NoVideo": "",
    "Hidden": "HD",
    "HardRock": "HR",
    "SuddenDeath": "SD",
    "DoubleTime": "DT",
    "Relax": "RL",
    "HalfTime": "HT",
    "Nightcore": "NC",
    "Flashlight": "FL",
    #"Autoplay": "",
    "SpunOut": "SO",
    #"Relax2": "",
    "Perfect": "PF",
    "Key4": "4K",
    "Key5": "5K",
    "Key6": "6K",
    "Key7": "7K",
    "Key8": "8K",
    #"keyMod": "",
    "FadeIn": "FI",
    #"Random": "",
    #"LastMod": "",
    #"FreeModAllowed": "",
    "Key9": "9K",
    "Key10": "10K",
    "Key1": "1K",
    "Key2": "2K",
    "Key3": "3K"
})

MOD_ORDER = [
    "None",
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
    "1K",
    "2K",
    "3K",
    "4K",
    "5K",
    "6K",
    "7K",
    "8K",
    "9K",
    "10K"
]

class Beatmap:
    """Contains fields of a beatmap"""
    ID = "beatmap_id"
    BEATMAPSET_ID = "beatmapset_id"
    FILE_MD5 = "file_md5"
    APPROVED = "approved"
    APPROVED_DATE = "approved_date"
    LAST_UPDATE = "last_update"
    ARTIST = "artist"
    TITLE = "title"
    VERSION = "version"
    CREATOR = "creator"
    BPM = "bpm"
    STARS = "difficultyrating"
    CS = "diff_size"
    OD = "diff_overall"
    AR = "diff_approach"
    HP = "diff_drain"
    MODE = "mode"
    TOTAL_LENGTH = "total_length"
    HIT_LENGTH = "hit_length"
    MAX_COMBO = "max_combo"
    SOURCE = "source"
    GENRE_ID = "genre_id"
    LANGUAGE_ID = "language_id"
    TAGS = "tags"
    FAVORITE_COUNT = "favorite_count"
    PLAYCOUNT = "playcount"
    PASSCOUNT = "passcount"
    RANK_STATUS = {
        "-2": "Graveyard",
        "-1": "WIP",
        "0": "Pending",
        "1": "Ranked",
        "2": "Approved",
        "3": "Qualified",
        "4": "Loved"
    }

    @staticmethod
    def get_from_string(string):
        """Returns the id of a beatmap from a string"""
        if string.startswith(URL_BEATMAP):
            string = re.search(r'\d+', string).group()
        return string

    @staticmethod
    def get_thumbnail_url(beatmap):
        """Returns url of the thumbnail of a beatmap"""
        return URL_THUMBNAIL + beatmap[Beatmap.BEATMAPSET_ID] + "l.jpg"

    @staticmethod
    def get_stars(beatmap):
        """Returns the star difficulty"""
        return "{0:.2f}*".format(float(beatmap[Beatmap.STARS]))

    @staticmethod
    def get_rank_status(beatmap):
        """Returns a string corresponding to the number of the rank status"""
        return Beatmap.RANK_STATUS[beatmap[Beatmap.APPROVED]]

    @staticmethod
    def get_total_length(beatmap):
        """Returns a formmated string of the total length"""
        minutes, seconds = divmod(int(beatmap[Beatmap.TOTAL_LENGTH]), 60)
        return '{:d}:{:02d}'.format(minutes, seconds)

    @staticmethod
    def get_hit_length(beatmap):
        """Returns a formmated string of the hit length"""
        minutes, seconds = divmod(int(beatmap[Beatmap.HIT_LENGTH]), 60)
        return '{:d}:{:02d}'.format(minutes, seconds)

    def __setattr__(self, key, value):
        if hasattr(self, key):
            raise AttributeError("can't set attribute")
        super().__setattr__(key, value)

class User:
    """Contains fields of a user"""
    ID = "user_id"
    NAME = "username"
    COUNT_300 = "count300"
    COUNT_100 = "count100"
    COUNT_50 = "count50"
    PLAYCOUNT = "playcount"
    RANKED_SCORE = "ranked_score"
    TOTAL_SCORE = "total_score"
    RANK = "pp_rank"
    LEVEL = "level"
    PP = "pp_raw"
    ACCURACY = "accuracy"
    COUNT_SS = "count_rank_ss"
    COUNT_S = "count_rank_s"
    COUNT_A = "count_rank_a"
    COUNTRY = "country"
    COUNTRY_RANK = "pp_country_rank"
    EVENTS = "events"

    def __setattr__(self, key, value):
        if hasattr(self, key):
            raise AttributeError("can't set attribute")
        super().__setattr__(key, value)

    @staticmethod
    def get_from_string(string):
        """Returns the id or name of a user from string"""
        if string.startswith('http'):
            if string.endswith('/'):
                string = string[:-1]
            string = string.split('/')[-1]
            string = string.split('&')[0]
            string = string.split('#')[0]
        return string

    class Event:
        """Contains fields of an event"""
        DISPLAY_HTML = "display_html"
        BEATMAP_ID = "beatmap_id"
        BEATMAPSET_ID = "beatmapset_id"
        DATE = "date"
        EPICFACTOR = "epicfactor"

        def __setattr__(self, key, value):
            if hasattr(self, key):
                raise AttributeError("can't set attribute")
            super().__setattr__(key, value)

class Score:
    """Contains fields of a score"""
    BEATMAP_ID = "beatmap_id"
    SCORE = "score"
    USER_NAME = "username"
    USER_ID = "user_id"
    COUNT_300 = "count300"
    COUNT_KATU = "countkatu"
    COUNT_100 = "count100"
    COUNT_GEKI = "countgeki"
    COUNT_50 = "count50"
    COUNT_MISS = "countmiss"
    MAX_COMBO = "maxcombo"
    PERFECT = "perfect"
    ENABLED_MODS = "enabled_mods"
    DATE = "date"
    RANK = "rank"
    PP = "pp"

    def __setattr__(self, key, value):
        if hasattr(self, key):
            raise AttributeError("can't set attribute")
        super().__setattr__(key, value)

    @staticmethod
    def get_accuracy(score):
        """Gets accuracy of a score from counts"""
        accuracy = Decimal(int(score[Score.COUNT_300]))
        accuracy += Decimal(int(score[Score.COUNT_100]) / 3)
        accuracy += Decimal(int(score[Score.COUNT_50]) / 6)
        accuracy *= 100
        max_notes = int(score[Score.COUNT_300])
        max_notes += int(score[Score.COUNT_100])
        max_notes += int(score[Score.COUNT_50])
        max_notes += int(score[Score.COUNT_MISS])
        accuracy /= Decimal(max_notes)
        return "{0:.2f}%".format(accuracy)

    @staticmethod
    def get_mods(score):
        """Gets a string of all enabled mods from bitfield"""
        enabled_mods = score[Score.ENABLED_MODS]
        bit_field = bitfield.BitField(enabled_mods)
        pattern = re.compile('|'.join(MOD_ACRONYMS.keys()))
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

    @staticmethod
    def get_score(score):
        """Returns a formatted score"""
        value = score[Score.SCORE]
        return '{:,}'.format(int(value)).replace(',', ' ')
