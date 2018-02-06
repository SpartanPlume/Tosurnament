"""Base of all modules"""

import helpers.load_json

DEFAULT_HELP_EMBED_COLOR = 3447003
COMMAND_NOT_FOUND_EMBED_COLOR = 3447003

class BaseModule():
    """Contains main functions used by modules"""

    def __init__(self, client):
        self.client = client
        self.name = "module"

    def get_string(self, command_name, field_name, *args):
        """Gets string from strings.json file"""
        if command_name:
            return helpers.load_json.replace_in_string(self.client.strings[self.name][command_name][field_name], *args)
        else:
            return helpers.load_json.replace_in_string(self.client.strings[self.name][field_name], *args)
            