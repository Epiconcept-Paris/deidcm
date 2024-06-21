# -*- coding: utf-8 -*-

import os
import unittest

import numpy as np
from PIL import Image
from pydicom import Dataset

from deidcm.config import Config
from deidcm.deid_verification import (
    is_background_black_enough,
    levenshtein_distance,
    gen_ui_case,
    DICOM_PREFIX_UID,
    DICOM_SUFFIX_UID,
    gen_sq_case,
    gen_obuc_case,
    gen_tm_case,
    gen_shlo_case,
    gen_dadt_case,
    check_resources,
    generate_random_words,
    add_words_on_image,
    compare_ocr_data_and_reality
)

from deidcm.test_cases.cases import (
    ui_tags,
    sq_tags,
    dadt_tags,
    shlo_tags,
    tm_tags
)

from deidcm.dicom.deid_mammogram import get_text_areas


class MetadataDeidentificationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """this method is called once before running all tests"""
        super(MetadataDeidentificationTest, cls).setUpClass()
        cls.test_assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        cls.test_fonts_dir = os.path.join(
            cls.test_assets_dir, 'fonts')
        cls.user_files = os.path.join(cls.test_assets_dir, 'user_files')
        cls.authorized_words_filepath = os.path.join(
            cls.user_files, 'authorized_words.txt')
        cls.config = Config(
            authorized_words_path=cls.authorized_words_filepath)

    def test_is_background_black_enough_black_img(self):
        """nominal case with a pitch black image"""
        pitch_black_img = Image.new("RGB", (100, 100), color="black")
        self.assertTrue(is_background_black_enough(
            2, 2, 10, 10, pitch_black_img))

    def test_is_background_black_enough_white_img(self):
        """nominal case with a pitch white image"""
        pitch_white_img = Image.new("RGB", (100, 100), color="white")
        self.assertFalse(is_background_black_enough(
            2, 2, 10, 10, pitch_white_img))

    def test_levenshtein_distance(self):
        """test function for levenshtein_distance"""
        self.assertEqual(levenshtein_distance("chien", "niche"), 4)
        self.assertEqual(levenshtein_distance(
            "javawasneat", "scalaisgreat"), 7)
        self.assertEqual(levenshtein_distance("forward", "drawrof"), 6)
        self.assertEqual(levenshtein_distance("distance", "eistancd"), 2)
        self.assertEqual(levenshtein_distance("sturgeon", "urgently"), 6)
        self.assertEqual(levenshtein_distance("difference", "distance"), 5)
        self.assertEqual(levenshtein_distance("example", "samples"), 3)
        self.assertEqual(levenshtein_distance("bsfhebfkrn", "bsthebtkrn"), 2)
        self.assertEqual(levenshtein_distance("cie", "cle"), 1)

    def test_gen_ui_case(self):
        """nominal case"""
        ds = gen_ui_case(Dataset())
        self.assertEqual(len(ds), len(ui_tags))
        for field in ds:
            self.assertEqual(
                field.value,
                f"{DICOM_PREFIX_UID}{DICOM_SUFFIX_UID}"
            )

    def test_gen_sq_case(self):
        """nominal case"""
        ds = gen_sq_case(Dataset())
        self.assertEqual(len(ds), len(sq_tags))
        for sequence in ds:
            self.assertEqual(
                len(sequence[0]),
                3,
                "sequence should contain exactly 3 elements"
            )

    def test_gen_obuc_case(self):
        """nominal case"""
        ds = gen_obuc_case(Dataset())
        self.assertEqual(len(ds), 4)

    def test_gen_tm_case(self):
        """nominal case"""
        ds = gen_tm_case(Dataset())
        self.assertEqual(len(ds), len(tm_tags))
        for field in ds:
            self.assertRegex(field.value, r"^(?:[01]\d|2[0-3])[0-5]\d[0-5]\d$")

    def test_gen_shlo_case(self):
        """nominal case"""
        ds = gen_shlo_case(Dataset())
        self.assertEqual(len(ds), len(shlo_tags))
        for field in ds:
            self.assertTrue(len(field.value) >= 0)
            self.assertTrue(len(field.value) <= 16)

    def test_gen_dadt_case(self):
        """nominal case"""
        ds = gen_dadt_case(Dataset())
        self.assertEqual(len(ds), len(dadt_tags))
        for field in ds:
            self.assertRegex(field.value, r"^\d{8}$")

    def test_check_resources(self):
        """nominal case"""
        fonts = ["Arial.ttf", "Courier_New.ttf",
                 "Georgia.ttf", "NotoSansCJK-Regular.ttc"]
        try:
            check_resources(self.test_fonts_dir, fonts, [1, 3, 4], [1, 3, 10])
        except (ValueError, TypeError):
            self.fail("These settings should be valid")

    def test_generate_random_words(self):
        """nominal case"""
        random_words = generate_random_words(10, 100, nb_character_min=5)
        self.assertTrue(len(random_words), 10)
        for word in random_words:
            self.assertTrue(len(word) >= 5)
            self.assertTrue(len(word) <= 100)

    def test_add_words_on_image(self):
        """nominal case"""
        words = ["Hi", "World"]
        pitch_black_img = Image.new("RGB", (500, 500), color="black")
        pixels = np.array(pitch_black_img)
        font = os.path.join(self.test_fonts_dir, "Arial.ttf")
        res = add_words_on_image(
            pixels, words, 3, font, color=(255, 255, 255))

        # OCR System is set to french language by default
        detected_elements = get_text_areas(res[0], languages=["en"])
        detected_words = set([el[1] for el in detected_elements])
        self.assertEqual(
            detected_words,
            set(words),
            f"{detected_words} should be identical to {words}"
        )

    def test_compare_ocr_data_and_reality(self):
        """nominal case"""
        words = ["Hi", "World"]
        pitch_black_img = Image.new("RGB", (500, 500), color="black")
        pixels = np.array(pitch_black_img)
        font = os.path.join(self.test_fonts_dir, "Arial.ttf")
        pixels_with_text = add_words_on_image(
            pixels, words, 3, font, color=(255, 255, 255))

        # OCR System is set to french language by default
        detected_elements = get_text_areas(
            pixels_with_text[0], languages=["en"])
        res = compare_ocr_data_and_reality(
            words, pixels_with_text[1], detected_elements)
        self.assertEqual(res[0], len(words))
        self.assertEqual(res[1], len(words))
