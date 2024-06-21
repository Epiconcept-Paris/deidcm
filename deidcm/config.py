"""Class used to define environment configuration."""

import json
import os
import warnings
from typing_extensions import Self


class Config:
    """This class is used to change the configuration of your environment.

    This singleton object has to be instanciated for deidentification tasks.
    It allows you to define the path to a custom recipe and the path to 
    a authorized_words.txt file.

    - `recipe.json`: a JSON file that contains the recipe orchestrating the
    attribute deidentification process.
    - `authorized_words.txt`: a TXT file that contains one word per line. Each
    word will be kept on the image even if it is detected by the OCR reader.
    """
    _instance = None
    _recipe = None
    _authorized_words = []

    def __new__(cls, recipe_path: str = None, authorized_words_path: str = None) -> Self:
        """
        Create a new instance of Config if it does not exist.

        Args:
            recipe_path: the path of your custom `recipe.json` file.
            authorized_words_path: the path of your custom `authorized_words.txt` file

        Returns:
            Config: The single instance of the Config class.
        """
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)

            # Init recipe
            cls._recipe = cls.load_recipe(recipe_path)

            # Init authorized_words
            if authorized_words_path is None:
                print(
                    "No authorized_words.txt file given. All OCR detected words will be erased.")
            else:
                cls._authorized_words = cls.load_authorized_words(
                    authorized_words_path)

        return cls._instance

    @classmethod
    def load_authorized_words(cls, authorized_words_filepath: str) -> list:
        """Get and load the list of authorized words from authorized_words.json

        This function reads `authorized_words.txt` and load it into a python list.
        If the file is not defined, the deidentification process will erase
        all detected words.

        Returns:
            A Python list of authorized words
        """
        if not os.path.exists(authorized_words_filepath):
            raise FileNotFoundError(
                f'Cannot load {authorized_words_filepath}')
        with open(authorized_words_filepath, 'r', encoding="utf8") as f:
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
        if recipe_filepath is None or not os.path.exists(recipe_filepath):
            print(
                f"No customized recipe.json found at path `{recipe_filepath}`. Defaulting to package inbuilt recipe.json")
        else:
            recipe = recipe_filepath

        # Load default inbuilt recipe.json file
        if recipe is None:
            recipe = os.path.join(os.path.dirname(
                __file__), 'dicom', 'recipe.json')

        try:
            with open(recipe, 'r', encoding="utf8") as f:
                return json.load(f)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Recipe file {recipe} cannot be found.") from exc

    @property
    def recipe(self) -> dict:
        """Getter of recipe"""
        if self._recipe is None:
            raise RuntimeError("Recipe has not been initialized")
        return self._recipe

    @property
    def authorized_words(self) -> list:
        """Getter of authorized_words"""
        return self._authorized_words
