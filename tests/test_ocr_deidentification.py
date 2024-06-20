# -*- coding: utf-8 -*-


import unittest
import os
import tempfile

import numpy as np
from PIL import Image

from deidcm.dicom.deid_mammogram import (
    deidentify_image_png,
    get_text_areas,
)
from deidcm.config import Config


class OcrDeidentificationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """this method is called once before running all tests"""
        super(OcrDeidentificationTest, cls).setUpClass()
        cls.test_assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        cls.test_mammo_dir = os.path.join(
            cls.test_assets_dir, 'sample_mammograms')
        cls.png_dir = os.path.join(cls.test_assets_dir, 'png_files')
        cls.user_files = os.path.join(cls.test_assets_dir, 'user_files')
        cls.ocr_deid_ignore_words_filepath = os.path.join(
            cls.user_files, 'ocr_deid_ignore.txt')
        cls.config = Config.get_instance()
        cls.config.set_ocr_ignored_words(cls.ocr_deid_ignore_words_filepath)

    def test_png_deidentification(self):
        sample_mammo_path = os.path.join(self.test_mammo_dir, 'cmmd-1.dcm')

        with tempfile.TemporaryDirectory() as outdirpath:
            deidentify_image_png(sample_mammo_path, outdirpath, 'removeme')
            self.assertTrue("removeme.png" in os.listdir(outdirpath))
            try:
                Image.open(os.path.join(outdirpath, "removeme.png"))
            except IOError:
                self.fail("Expected image file cannot be opened")

    def test_load_authorized_words(self):
        """nominal case"""
        words = Config.load_authorized_words(
            self.ocr_deid_ignore_words_filepath)
        self.assertEqual(['HELLO', 'ALTER', 'DSQLD'], words,
                         "Both lists should contain the same words")

    def test_get_text_areas_w_b(self):
        """
        check if text is correctly detected for white text on black background
        """
        im = Image.open(os.path.join(self.png_dir, 'white-txt-black-bg.png'))
        pixels = np.array(im)
        detected_elements = get_text_areas(pixels)
        detected_words = set([el[1] for el in detected_elements])
        self.assertEqual(
            detected_words,
            set(['JTRX4', 'SHOCR', 'DSLC72']),
            "Words detected should match words written on PNG image"
        )
