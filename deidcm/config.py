"""Hold the environment settings"""

import json
import os
from typing_extensions import Self


class Config:
    """Singleton object to easily access env settings"""
    _instance = None

    def __new__(cls) -> Self:
        """
        Create a new instance of Config if it does not exist.

        Returns:
            Config: The single instance of the Config class.
        """
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> Self:
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def set_recipe(self, filepath) -> None:
        self._recipe = self.load_recipe(filepath)

    def set_ocr_ignored_words(self, filepath) -> None:
        self._ocr_ignored_words = self.load_authorized_words(filepath)

    @classmethod
    def load_authorized_words(cls, ocr_ignored_words_filepath: str) -> list:
        if not os.path.exists(ocr_ignored_words_filepath):
            raise FileNotFoundError(
                f'Cannot load {ocr_ignored_words_filepath}')
        with open(ocr_ignored_words_filepath, 'r', encoding="utf8") as f:
            words = list(map(str.strip, f.readlines()))
        return words

    @classmethod
    def load_recipe(cls, recipe_filepath: str) -> dict:
        """Get the recipe from recipe.json and load it into a python dict.

        This function reads `recipe.json`. If a user-defined version of the file
        is detected, it will be used. Otherwise, the inbuilt version of the file will be used.

        Be aware that the inbuilt version of the file does not suit a generic usage.
        It was created for the Deep.piste study. It is highly recommended to create
        your own version of `recipe.json`.

        Returns:
            A Python dictionary with recipe elements.
        """
        recipe = None

        # Load user customized recipe.json file
        if not os.path.exists(recipe_filepath):
            print(
                f"WARNING: No customized recipe.json found at {recipe_filepath}. Defaulting to package inbuilt recipe.json")
        else:
            recipe = recipe_filepath

        # Load default inbuilt recipe.json file
        if recipe is None:
            recipe = os.path.join(os.path.dirname(__file__), 'recipe.json')

        try:
            with open(recipe, 'r', encoding="utf8") as f:
                return json.load(f)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Recipe file {recipe} cannot be found.") from exc

    @property
    def recipe_filepath(self) -> str:
        return self.recipe_filepath

    @property
    def recipe(self) -> dict:
        return self.recipe

    @property
    def ocr_ignored_words_filepath(self) -> str:
        return self.ocr_ignored_words_filepath

    @property
    def ocr_ignored_words(self) -> list:
        return self.ocr_ignored_words
