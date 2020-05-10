"""All tests concerning the load_json module"""

import unittest

from common.utils import load_json

DIRECTORY_PATH = "test/resources/replies"


class LoadJsonTestCase(unittest.TestCase):
    def test_load_directory(self):
        """Load a directory with json files and convert it to python dictionnary"""
        data = load_json.load_directory(DIRECTORY_PATH)
        self.assertEqual(data["others"]["hot"]["food"], "chicken")
        self.assertEqual(data["others"]["cold"], "drink")
        data = data["strings"]
        self.assertEqual(data["sub"], "sub")
        self.assertEqual(data["main"]["two"], "2")
        self.assertEqual(data["main"]["absolute"]["not_absolute"], "in_absolute")
        self.assertEqual(data["main"]["absolute"]["two_and_four"], "$strings/main/two and 4")
        self.assertEqual(data["main"]["absolute"]["two_two"], "$strings/main/two $strings/main/two")
        self.assertEqual(data["main"]["absolute"]["sub"], "$strings/sub")
        self.assertEqual(data["main"]["relative"]["two"], "$../two")
        self.assertEqual(
            data["main"]["relative"]["sub_and_not_absolute"], "$../../sub and $./.././absolute/not_absolute",
        )
        self.assertEqual(data["main"]["relative"]["same_level"], "$not_relative")
        self.assertEqual(data["from_others"]["absolute_hot_food"], "$others/hot/food")
        self.assertEqual(data["from_others"]["relative_cold"], "$../../others/cold")

    def test_replace_placeholders(self):
        """Replace $ placeholders in objects"""
        data = load_json.load_directory(DIRECTORY_PATH)
        data = load_json.replace_placeholders(data)
        data = data["strings"]
        self.assertEqual(data["main"]["absolute"]["two_and_four"], "2 and 4")
        self.assertEqual(data["main"]["absolute"]["two_two"], "2 2")
        self.assertEqual(data["main"]["absolute"]["sub"], "sub")
        self.assertEqual(data["main"]["relative"]["two"], "2")
        self.assertEqual(data["main"]["relative"]["sub_and_not_absolute"], "sub and in_absolute")
        self.assertEqual(data["main"]["relative"]["same_level"], "same_level")
        self.assertEqual(data["from_others"]["absolute_hot_food"], "chicken")
        self.assertEqual(data["from_others"]["relative_cold"], "drink")

    def test_replace_in_object(self):
        """Replace % placeholders in objects"""
        string = "I am %0. This is a %1. You are not %0."
        first_parameter = "Spartan Plume"
        second_parameter = "cat"
        expected_string = (
            "I am " + first_parameter + ". This is a " + second_parameter + ". You are not " + first_parameter + "."
        )
        obj = {"content": string}
        new_obj = load_json.replace_in_object(obj, first_parameter, second_parameter)
        self.assertEqual(new_obj["content"], expected_string)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(LoadJsonTestCase("test_load_directory"))
    suite.addTest(LoadJsonTestCase("test_replace_placeholders"))
    suite.addTest(LoadJsonTestCase("test_replace_in_object"))
    return suite
