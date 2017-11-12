"""Base of all modules"""

import logging
import discord

DEFAULT_HELP_EMBED_COLOR = 3447003
COMMAND_NOT_FOUND_EMBED_COLOR = 3447003

class BaseModule():
    """Contains main functions used by modules"""

    def __init__(self, client):
        self.client = client
        self.prefix = None
        self.name = "module"
        self.help_messages = {}
        self.commands = {}

    async def on_message(self, message, content):
        """Executes a command according to the message"""
        channel = message.channel
        parameters = content.split(" ", 1)
        if len(parameters) != 2:
            parameters.append("")
        command = parameters[0]
        text = None
        if command in self.commands:
            self.client.log(logging.INFO, self.name + ": " + command + ": " + parameters[1])
            channel, text, embed = await self.commands[command](message, parameters[1])
        else:
            embed = discord.Embed(colour=COMMAND_NOT_FOUND_EMBED_COLOR)
            embed.title = "Command not found"
            embed.description = self.client.prefix + self.prefix + content
        return (channel, text, embed)

    async def help(self, message, *_, color=DEFAULT_HELP_EMBED_COLOR):
        """Shows all commands of the module"""
        self.client.log(logging.INFO, self.name + ": help")
        embed = discord.Embed(colour=color,
                              title="`" + self.name + " commands`",
                              description="All commands of the " + self.name + " module")
        for command, tup in self.help_messages.items():
            parameter, help_message = tup
            field_name = self.client.prefix + self.prefix + command + " " + parameter
            embed.add_field(name=field_name, value=help_message, inline=False)
        return (message.channel, None, embed)
