"""Loads json and edit it"""

import json
import re
import os
import copy

JSONDecodeError = json.JSONDecodeError


def load_directory(directory, root="."):
    """
    Loads all json files in a directory recursively and returns an multi-dimensional array.
    Can throw a FileNotFoundError or a json.JSONDecodeError exception.
    """
    strings = dict()
    current_path = os.path.join(root, directory)
    with os.scandir(current_path) as it:
        for entry in it:
            name = entry.name
            if entry.is_file() and name.endswith(".json"):
                f = open(os.path.join(current_path, name))
                strings[name[:-5]] = json.load(f)
                f.close()
            elif entry.is_dir():
                strings[name] = load_directory(name, current_path)
    return strings


def return_path_value(strings, path):
    tmp_keys = path.split("/")
    tmp_data = strings
    try:
        for tmp_key in tmp_keys:
            tmp_data = tmp_data[tmp_key]
    except KeyError:
        return None
    if isinstance(tmp_data, str):
        return tmp_data
    return None


def replace_placeholders_string_case(string, strings_root, current_path):
    string_left = string
    while "$" in string_left:
        absolute_path = ""
        relative_path = current_path
        string_left = string_left.split("$", 1)[1]
        variable = re.search(r"[./]*[^\\\\` ,;:\"'!?.\n\*%$~]+", string_left)
        if not variable:
            continue
        variable = variable.group(0)
        tmp_keys = variable.split("/")
        for tmp_key in tmp_keys:
            if tmp_key == ".":
                continue
            elif tmp_key == "..":
                relative_path = relative_path.rsplit("/", 1)[0]
            else:
                relative_path = "/".join(filter(None, [relative_path, tmp_key]))
                absolute_path = "/".join(filter(None, [absolute_path, tmp_key]))
        if value := return_path_value(strings_root, relative_path):
            string = string.replace("$" + variable, value)
        elif value := return_path_value(strings_root, absolute_path):
            string = string.replace("$" + variable, value)
    return string


def replace_placeholders_dict_case(strings, strings_root, current_path):
    new_strings = dict()
    for key, value in strings.items():
        if isinstance(value, str):
            new_strings[key] = replace_placeholders_string_case(value, strings_root, current_path)
        elif isinstance(value, dict):
            new_strings[key] = replace_placeholders_dict_case(
                value, strings_root, "/".join(filter(None, [current_path, key]))
            )
        else:
            new_strings[key] = value
    return new_strings


def replace_placeholders(strings):
    """Replace placeholders by their corresponding values"""
    if isinstance(strings, dict):
        return replace_placeholders_dict_case(strings, strings, "")
    return strings


def replace_in_string(string, *args):
    i_args = len(args) - 1
    while i_args >= 0:
        string = string.replace("%" + str(i_args), str(args[i_args]))
        i_args -= 1
    return string


def replace_in_object(dictionnary, *args):
    for key, value in dictionnary.items():
        if isinstance(value, str):
            i_args = len(args) - 1
            while i_args >= 0:
                value = value.replace("%" + str(i_args), str(args[i_args]))
                i_args -= 1
            dictionnary[key] = value
        elif isinstance(value, dict):
            dictionnary[key] = replace_in_object(value, *args)
        elif isinstance(value, list):
            new_value = []
            for subvalue in value:
                if isinstance(subvalue, str):
                    i_args = len(args) - 1
                    while i_args >= 0:
                        subvalue = subvalue.replace("%" + str(i_args), str(args[i_args]))
                        i_args -= 1
                    new_value.append(subvalue)
                if isinstance(subvalue, dict):
                    new_value.append(replace_in_object(subvalue, *args))
            dictionnary[key] = new_value
    return dictionnary
