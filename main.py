"""Starts the bot"""

import sys
import logging
from client import Client
import constants

def main():
    """Main function"""
    client = Client()
    client.log(logging.INFO, "Tosurnament Bot started")
    client.run(constants.TOKEN)
    print("test")

if __name__ == '__main__':
    sys.exit(main())
