import os
import importlib
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler

import MySQLdb
import mysqldb_wrapper
from common.config import constants

logging_handler = TimedRotatingFileHandler(
    filename="log/api.log",
    when="W1",
    utc=True,
    backupCount=4,
    atTime=datetime.time(hour=12),
)
logging_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s: %(message)s"))


RESOURCES_DIR = "common/databases/tosurnament"
for root, _, files in os.walk(RESOURCES_DIR):
    for filename in files:
        if filename.endswith(".py"):
            importlib.import_module(root.replace("/", ".").replace("\\", ".") + "." + filename[:-3])

try:
    db = mysqldb_wrapper.Session(
        constants.DB_USERNAME, constants.DB_PASSWORD, constants.DB_NAME, constants.ENCRYPTION_KEY, logging_handler
    )
except MySQLdb._exceptions.OperationalError:
    db = None
