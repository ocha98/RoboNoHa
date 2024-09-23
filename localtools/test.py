from lib import cleaing_txt
import unittest

class TestStringMethods(unittest.TestCase):
    def test_cleaning_txt(self):
        input_txt = [
            "@hoge.example.com abc",
            "テキスト  example.com/hoge/huga...",
            "テキストhttps://www.example.com",
            "http://img.example.com テキスト",
            "@abc テスト @def",
        ]
        expected = [
            "abc",
            "テキスト",
            "テキスト",
            "テキスト",
            "テスト"
        ]

        for i in range(len(input_txt)):
            with self.subTest(i=i):
                self.assertEqual(cleaing_txt(input_txt[i]), expected[i])

if __name__ == '__main__':
    unittest.main()
