#!/usr/bin/python3

"""Main file used to start the bot"""

import asyncio
import sys

import discord

from bot.client import Client
from common.config import constants


async def main():
    """Main function"""
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    bot = Client(intents=intents)
    if bot.error_code == 0:
        async with bot:
            await bot.start(constants.BOT_TOKEN)
    else:
        print("Bot could not start, error code returned is: {0}".format(bot.error_code))
    return bot.error_code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
