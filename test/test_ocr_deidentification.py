# -*- coding: utf-8 -*-


import unittest
import os
import tempfile

from PIL import Image

from kskit.dicom.deid_mammogram import (
    deidentify_image_png
)


class OcrDeidentificationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """this method is called before once before running all tests"""
        super(OcrDeidentificationTest, cls).setUpClass()
        cls.test_assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        cls.test_mammo_dir = os.path.join(
            cls.test_assets_dir, 'sample_mammograms')

    def test_png_deidentification(self):
        sample_mammo_path = os.path.join(self.test_mammo_dir, 'cmmd-1.dcm')

        with tempfile.TemporaryDirectory() as outdirpath:
            deidentify_image_png(sample_mammo_path, outdirpath, 'removeme')
            self.assertTrue("removeme.png" in os.listdir(outdirpath))
            try:
                im = Image.open(os.path.join(outdirpath, "removeme.png"))
            except IOError:
                self.fail("Expected image file cannot be opened")
