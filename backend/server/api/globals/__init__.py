import os
import importlib

from cryptography.fernet import Fernet
from encrypted_mysqldb.database import Database
from encrypted_mysqldb.errors import DatabaseInitializationError

from common.config import constants

RESOURCES_DIR = "common/databases/tosurnament"
for root, _, files in os.walk(RESOURCES_DIR):
    for filename in files:
        if filename.endswith(".py"):
            importlib.import_module(root.replace("/", ".").replace("\\", ".") + "." + filename[:-3])

try:
    db = Database(constants.DB_USERNAME, constants.DB_PASSWORD, constants.DB_NAME, Fernet(constants.ENCRYPTION_KEY))
except DatabaseInitializationError as e:
    db = None
