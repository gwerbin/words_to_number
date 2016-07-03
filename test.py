import unittest
from words_to_number import (split_text,
                             parse_tokens,
                             find_numbers,
                             replace_numbers)

class TestSplitWhitespace(unittest.TestCase):
    def test_misc(self):
        self.assertEqual(split_text("six hundred sixty-six"),
                         ["six", "hundred", "sixty", "six"])

class TestParseTokens(unittest.TestCase):
    def test_misc(self):
        self.assertEqual(parse_tokens("six hundred sixty-six".split(" ")), 666)
        self.assertEqual(parse_tokens("one thousand two".split(" ")), 1002)
        self.assertEqual(parse_tokens("ninety-seven hundred one".split(" ")), 9701)
        with self.assertRaises(ValueError):
            parse_tokens('six point seven')


class TestFindNumbers(unittest.TestCase):
    def test_gettysburg(self):
        s = "Four score and seven years ago"
        expected = {4: (0, 1), 7: (3, 1)}
        self.assertEqual(find_numbers(s), expected)

    def test_summer_of_love(self):
        s = "In the year of our Lord nineteen hundred and sixty-nine"
        expected = {1969: (6, 5)}
        self.assertEqual(find_numbers(s), expected)


class TestReplaceNumbers(unittest.TestCase):
    def test_gettysburg(self):
        s = "Four score and seven years ago"
        expected = "4 score and 7 years ago"
        self.assertEqual(replace_numbers(s), expected)

    def test_summer_of_love(self):
        s = "In the year of our Lord nineteen hundred and sixty-nine"
        expected = "in the year of our lord 1969"
        self.assertEqual(replace_numbers(s), expected)

    def test_rent(self):
        s = "Five hundred twenty-five thousand six hundred minutes"
        expected = "525600 minutes"
        self.assertEqual(replace_numbers(s), expected)

    def test_dr_evil(self):
        s = "One hundred billion dollars"
        expected = "100000000000 dollars"
        self.assertEqual(replace_numbers(s), expected)
