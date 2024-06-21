import os
import unittest

from deidcm.config import Config


class ConfigTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """this method is called once before running all tests"""
        super(ConfigTest, cls).setUpClass()
        cls.test_assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        cls.test_fonts_dir = os.path.join(
            cls.test_assets_dir, 'fonts')
        cls.user_files = os.path.join(cls.test_assets_dir, 'user_files')
        cls.authorized_words_filepath = os.path.join(
            cls.user_files, 'authorized_words.txt')
        cls.config = Config(
            authorized_words_path=cls.authorized_words_filepath)

    def test_singleton(self):
        """Check that this object cannot be instanciated more than one time"""
        config1 = Config()
        self.assertEqual(self.config, config1)
        config2 = Config(recipe_path="blabla",
                         authorized_words_path="nonsense")
        self.assertEqual(self.config, config2)

        self.assertNotEqual(config2.recipe, "blabla")
        self.assertEqual(config2.recipe, self.config.recipe)

        self.assertNotEqual(config2.authorized_words, "nonsense")
        self.assertEqual(config2.authorized_words,
                         self.config.authorized_words)
