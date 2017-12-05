"""Loads json and edit it"""

import sys
import json
import re

def open_file(filename):
    """Opens a json file and edits variables"""
    try:
        f = open(filename)
    except FileNotFoundError:
        sys.exit("strings.json not found")
    try:
        data = json.load(f)
    except json.JSONDecodeError:
        sys.exit("strings.json is not a valid json file.")
    lines = ""
    f = open(filename)
    for line in f:
        while "$" in line:
            variable = line.split("$", 1)[1]
            variable = re.split("[\\\\` ,;:\"'!?.]+", variable, 1)[0]
            keys = variable.split("/")
            tmp_data = data
            for key in keys:
                tmp_data = tmp_data[key]
            line = line.replace("$" + variable, tmp_data)
        lines += line
    return json.loads(lines)

def replace_in_string(string, *args):
    count = 1
    for arg in args:
        string = string.replace("%" + str(count), arg)
        count += 1
    return string