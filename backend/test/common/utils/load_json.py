"""All tests concerning the load_json module"""

from common.utils import load_json

DIRECTORY_PATH = "test/resources/replies"


def test_load_directory():
    """Load a directory with json files and convert it to python dictionnary"""
    data = load_json.load_directory(DIRECTORY_PATH)
    assert data["others"]["hot"]["food"] == "chicken"
    assert data["others"]["cold"] == "drink"

    data = data["strings"]
    assert data["sub"] == "sub"
    assert data["main"]["two"] == "2"
    assert data["main"]["absolute"]["not_absolute"] == "in_absolute"
    assert data["main"]["absolute"]["two_and_four"] == "$strings/main/two and 4"
    assert data["main"]["absolute"]["two_two"] == "$strings/main/two $strings/main/two"
    assert data["main"]["absolute"]["sub"] == "$strings/sub"
    assert data["main"]["relative"]["two"] == "$../two"
    assert data["main"]["relative"]["sub_and_not_absolute"] == "$../../sub and $./.././absolute/not_absolute"
    assert data["main"]["relative"]["same_level"] == "$not_relative"
    assert data["from_others"]["absolute_hot_food"] == "$others/hot/food"
    assert data["from_others"]["relative_cold"] == "$../../others/cold"


def test_replace_placeholders():
    """Replace $ placeholders in objects"""
    data = load_json.load_directory(DIRECTORY_PATH)
    data = load_json.replace_placeholders(data)
    data = data["strings"]
    assert data["main"]["absolute"]["two_and_four"] == "2 and 4"
    assert data["main"]["absolute"]["two_two"] == "2 2"
    assert data["main"]["absolute"]["sub"] == "sub"
    assert data["main"]["relative"]["two"] == "2"
    assert data["main"]["relative"]["sub_and_not_absolute"] == "sub and in_absolute"
    assert data["main"]["relative"]["same_level"] == "same_level"
    assert data["from_others"]["absolute_hot_food"] == "chicken"
    assert data["from_others"]["relative_cold"] == "drink"


def test_replace_in_object():
    """Replace % placeholders in objects"""
    string = "I am %0. This is a %1. You are not %0."
    first_parameter = "Spartan Plume"
    second_parameter = "cat"
    expected_string = (
        "I am " + first_parameter + ". This is a " + second_parameter + ". You are not " + first_parameter + "."
    )
    obj = {"content": string}
    new_obj = load_json.replace_in_object(obj, first_parameter, second_parameter)
    assert new_obj["content"] == expected_string
