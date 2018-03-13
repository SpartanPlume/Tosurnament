"""Starts the bot"""

import sys
import os
import asyncio
import discord
from discord.ext import commands
from client import Client
import constants

MODULES_DIR = "modules"

def main():
    """Main function"""
    bot = Client()
    bot.run(constants.TOKEN, bot=True, reconnect=True)
    return bot.error_code

if __name__ == '__main__':
    sys.exit(main())
