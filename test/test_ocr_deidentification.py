# -*- coding: utf-8 -*-


import unittest
import os
import tempfile

import numpy as np
from PIL import Image

from kskit.dicom.deid_mammogram import (
    deidentify_image_png,
    load_authorized_words,
    get_text_areas,
)


class OcrDeidentificationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """this method is called once before running all tests"""
        super(OcrDeidentificationTest, cls).setUpClass()
        cls.test_assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        cls.test_mammo_dir = os.path.join(
            cls.test_assets_dir, 'sample_mammograms')
        cls.png_dir = os.path.join(cls.test_assets_dir, 'png_files')
        cls.dp_home = os.path.join(cls.test_assets_dir, 'dp_home')
        os.environ['DP_HOME'] = cls.dp_home

    @classmethod
    def tearDownClass(cls):
        """this method is called once after running all tests"""
        os.environ.pop('DP_HOME')

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
        words = load_authorized_words()
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
