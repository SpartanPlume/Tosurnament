"""Commands to show profile, music, etc; of osu!"""

import collections
import discord
import modules.module
import api.osu

EMBED_COLOUR = 3447003

class Module(modules.module.BaseModule):
    """Class that contains commands to use"""

    def __init__(self, client):
        super(Module, self).__init__(client)
        self.prefix = "osu::"
        self.name = "osu"
        self.commands = {
            "help": self.help,
            "beatmap": self.beatmap,
            "user": self.user,
            "score": self.score,
            "scores": self.scores,
            "user_best": self.user_best,
            "screenshot": self.screenshot
        }
        self.help_messages = collections.OrderedDict([
            ("beatmap", ("<beatmap>", "Shows details of the <beatmap>")),
            ("user", ("<user>", "Shows the profile of <user>")),
            ("score", ("<beatmap> <user>", "Shows the score of <user> on the <beatmap>")),
            ("scores", ("<beatmap>", "Shows the top 5 scores of the <beatmap>")),
            ("user_best", ("<user>", "Shows the top 5 pp scores of <user>")),
            ("screenshot", ("<beatmap> <url> <description>", "Shows a screenshot (<url>) and a link to the <beatmap>, <description> is an optional text to describe the screenshot"))
        ])

    async def beatmap(self, message, parameter):
        """Shows the top scores of a beatmap"""
        embed = discord.Embed(colour=EMBED_COLOUR)
        embed.title = "::osu::beatmap <beatmap>"
        embed.description = "<beatmap> can be an id or an url."
        if parameter != "":
            beatmap_id = api.osu.Beatmap.get_from_string(parameter)
            beatmaps = api.osu.OsuApi.get_beatmaps(beatmap_id)
            if not beatmaps:
                embed.add_field(name="Beatmap not Found", value=parameter)
            else:
                beatmap = beatmaps[0]
                author_name = beatmap[api.osu.Beatmap.TITLE]
                author_name += " [" + beatmap[api.osu.Beatmap.VERSION] + "]"
                author_name += " - " + api.osu.Beatmap.get_stars(beatmap)
                length_value = api.osu.Beatmap.get_total_length(beatmap)
                length_value += " (" + api.osu.Beatmap.get_hit_length(beatmap) + " drain)"
                difficulty_value = "CS: " + beatmap[api.osu.Beatmap.CS]
                difficulty_value += " - AR: " + beatmap[api.osu.Beatmap.AR]
                difficulty_value += " - OD: " + beatmap[api.osu.Beatmap.OD]
                difficulty_value += " - HP: " + beatmap[api.osu.Beatmap.HP]
                embed.set_author(name=author_name, url=api.osu.URL_BEATMAP + beatmap_id)
                embed.title = ""
                embed.description = beatmap[api.osu.Beatmap.ARTIST]
                embed.set_thumbnail(url=api.osu.Beatmap.get_thumbnail_url(beatmap))
                embed.set_footer(text="Data provided by osu!", icon_url=api.osu.URL_LOGO)
                embed.add_field(name="Creator", value=beatmap[api.osu.Beatmap.CREATOR])
                embed.add_field(name="Rank status", value=api.osu.Beatmap.get_rank_status(beatmap))
                embed.add_field(name="Length", value=length_value)
                embed.add_field(name="BPM", value=beatmap[api.osu.Beatmap.BPM])
                embed.add_field(name="Difficulty", value=difficulty_value)
        return (message.channel, None, embed)

    async def user(self, message, parameter):
        """Shows the profile of a user"""
        embed = discord.Embed(colour=EMBED_COLOUR)
        embed.title = "::osu::user <user>"
        embed.description = "<user> can be an id, a pseudo or an url."
        if parameter != "":
            user_id = api.osu.User.get_from_string(parameter)
            users = api.osu.OsuApi.get_user(user_id)
            if not users:
                embed.add_field(name="User not Found", value=parameter)
            else:
                user = users[0]
                flag = ":flag_" + user[api.osu.User.COUNTRY].lower() + ":  "
                embed.title = flag + user[api.osu.User.NAME]
                embed.url = api.osu.URL_USER + user[api.osu.User.ID]
                embed.description = "osu! profile"
                embed.set_thumbnail(url=(api.osu.URL_PROFILE_PICTURE + user[api.osu.User.ID]))
                embed.set_footer(text="Data provided by osu!", icon_url=api.osu.URL_LOGO)
                embed.add_field(name="Rank", value=user[api.osu.User.RANK])
                embed.add_field(name="PP", value=user[api.osu.User.PP])
                embed.add_field(name="Country Rank", value=user[api.osu.User.COUNTRY_RANK])
                embed.add_field(name="Level", value=user[api.osu.User.LEVEL])
                embed.add_field(name="Playcount", value=user[api.osu.User.PLAYCOUNT])
        return (message.channel, None, embed)

    async def score(self, message, parameter):
        """Shows the score of a user on a beatmap"""
        embed = discord.Embed(colour=EMBED_COLOUR)
        embed.title = "::osu::score <beatmap> <user>"
        embed.description = "<beatmap> can be an id or an url."
        embed.description += "\n<user> can be an id, a pseudo or an url."
        parameters = parameter.split(" ", 1)
        if parameter != "" and len(parameters) == 2:
            beatmap_id = api.osu.Beatmap.get_from_string(parameters[0])
            user = api.osu.User.get_from_string(parameters[1])
            beatmaps = api.osu.OsuApi.get_beatmaps(beatmap_id)
            scores = api.osu.OsuApi.get_scores(beatmap_id, user)
            if not beatmaps:
                embed.add_field(name="Beatmap not Found", value=parameters[0])
            elif not scores:
                embed.add_field(name="Score not Found", value=parameters[1])
            else:
                beatmap = beatmaps[0]
                score = scores[0]
                author_name = beatmap[api.osu.Beatmap.TITLE]
                author_name += " [" + beatmap[api.osu.Beatmap.VERSION] + "]"
                author_name += " - " + api.osu.Beatmap.get_stars(beatmap)
                embed.set_author(name=author_name, url=api.osu.URL_BEATMAP + beatmap_id)
                embed.title = score[api.osu.Score.USER_NAME]
                embed.url = api.osu.URL_USER + score[api.osu.Score.USER_ID]
                embed.description = score[api.osu.Score.DATE]
                embed.set_thumbnail(url=api.osu.Beatmap.get_thumbnail_url(beatmap))
                embed.set_footer(text="Data provided by osu!", icon_url=api.osu.URL_LOGO)
                embed.add_field(name="Rank", value=api.osu.RANK[score[api.osu.Score.RANK]])
                embed.add_field(name="Accuracy", value=api.osu.Score.get_accuracy(score))
                embed.add_field(name="Score", value=api.osu.Score.get_score(score))
                embed.add_field(name="Max Combo", value=score[api.osu.Score.MAX_COMBO])
                embed.add_field(name="PP", value=score[api.osu.Score.PP])
                embed.add_field(name="Mods", value=api.osu.Score.get_mods(score))
        return (message.channel, None, embed)

    async def scores(self, message, parameter):
        """Shows the top scores of a beatmap"""
        embed = discord.Embed(colour=EMBED_COLOUR)
        embed.title = "::osu::scores <beatmap>"
        embed.description = "<beatmap> can be an id or an url."
        if parameter != "":
            beatmap_id = api.osu.Beatmap.get_from_string(parameter)
            beatmaps = api.osu.OsuApi.get_beatmaps(beatmap_id)
            scores = api.osu.OsuApi.get_scores(beatmap_id, limit=5)
            if not beatmaps or not scores:
                embed.add_field(name="Beatmap not Found", value=parameter)
            else:
                beatmap = beatmaps[0]
                author_name = beatmap[api.osu.Beatmap.TITLE]
                author_name += " [" + beatmap[api.osu.Beatmap.VERSION] + "]"
                author_name += " - " + api.osu.Beatmap.get_stars(beatmap)
                embed.set_author(name=author_name, url=api.osu.URL_BEATMAP + beatmap_id)
                embed.title = ""
                embed.description = "Top 5 scores"
                embed.set_thumbnail(url=api.osu.Beatmap.get_thumbnail_url(beatmap))
                embed.set_footer(text="Data provided by osu!", icon_url=api.osu.URL_LOGO)
                for i, score in enumerate(scores):
                    user_name = str(i + 1) + ". " + score[api.osu.Score.USER_NAME]
                    user_name += " - " + api.osu.RANK[score[api.osu.Score.RANK]]
                    user_name += " - " + api.osu.Score.get_accuracy(score)
                    user_score = api.osu.Score.get_mods(score)
                    user_score += " - " + api.osu.Score.get_score(score)
                    user_score += " - x" + score[api.osu.Score.MAX_COMBO]
                    embed.add_field(name=user_name, value=user_score, inline=False)
        return (message.channel, None, embed)

    async def user_best(self, message, parameter):
        """Shows the best pp score of a user"""
        embed = discord.Embed(colour=EMBED_COLOUR)
        embed.title = "::osu::user_best <user>"
        embed.description = "<user> can be an id, a pseudo or an url."
        if parameter != "":
            user_id = api.osu.User.get_from_string(parameter)
            users = api.osu.OsuApi.get_user(user_id)
            scores = api.osu.OsuApi.get_user_best(user_id, limit=5)
            if not users or not scores:
                embed.add_field(name="User not Found", value=parameter)
            else:
                user = users[0]
                flag = ":flag_" + user[api.osu.User.COUNTRY].lower() + ":  "
                embed.title = flag + user[api.osu.User.NAME]
                embed.url = api.osu.URL_USER + user[api.osu.User.ID]
                embed.description = "osu! best scores"
                embed.set_thumbnail(url=(api.osu.URL_PROFILE_PICTURE + user[api.osu.User.ID]))
                embed.set_footer(text="Data provided by osu!", icon_url=api.osu.URL_LOGO)
                for score in scores:
                    beatmap = api.osu.OsuApi.get_beatmaps(score[api.osu.Score.BEATMAP_ID])[0]
                    score_name = beatmap[api.osu.Beatmap.TITLE]
                    score_name += " [" + beatmap[api.osu.Beatmap.VERSION] + "]"
                    score_name += " - " + api.osu.Beatmap.get_stars(beatmap)
                    score_value = api.osu.RANK[score[api.osu.Score.RANK]]
                    score_value += " - " + api.osu.Score.get_accuracy(score)
                    score_value += " - " + api.osu.Score.get_mods(score)
                    score_value += " - " + score[api.osu.Score.PP] + "pp"
                    score_value += " - [beatmap](" + api.osu.URL_BEATMAP + beatmap[api.osu.Beatmap.ID] + ")"
                    embed.add_field(name=score_name, value=score_value, inline=True)
        return (message.channel, None, embed)

    async def screenshot(self, message, parameter):
        """Shows a screenshot with a link to the beatmap"""
        embed = discord.Embed(colour=EMBED_COLOUR)
        embed.title = "::osu::screenshot <beatmap> <url>"
        embed.description = "<beatmap> can be an id or an url."
        embed.description += "\n<url> must be a valid url of an image."
        parameters = parameter.split(" ", 2)
        if parameter != "" and len(parameters) >= 2:
            beatmap_id = api.osu.Beatmap.get_from_string(parameters[0])
            image_url = parameters[1]
            beatmaps = api.osu.OsuApi.get_beatmaps(beatmap_id)
            if not beatmaps:
                embed.add_field(name="Beatmap not Found", value=parameters[0])
            else:
                beatmap = beatmaps[0]
                author_name = beatmap[api.osu.Beatmap.TITLE]
                author_name += " [" + beatmap[api.osu.Beatmap.VERSION] + "]"
                author_name += " - " + api.osu.Beatmap.get_stars(beatmap)
                embed.set_author(name=author_name, url=api.osu.URL_BEATMAP + beatmap_id)
                embed.title = ""
                if len(parameters) != 3:
                    embed.description = "osu! screenshot"
                else:
                    embed.description = parameters[2]
                #embed.set_thumbnail(url=api.osu.Beatmap.get_thumbnail_url(beatmap))
                embed.set_footer(text="Data provided by osu!", icon_url=api.osu.URL_LOGO)
                embed.set_image(url=image_url)
        return (message.channel, None, embed)
