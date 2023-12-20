# -*- coding: utf-8 -*-

import unittest
import os
import tempfile

import pandas as pd
from PIL import Image

from kskit.dicom.dicom2df import (
    dicom2df
)

from kskit.dicom.df2dicom import (
    df2dicom
)

SAMPLE_SOP_INSTANCE_UID = "1.3.6.1.4.1.14519.5.2.1.1239.1759.586725248951242926783849287982"

class Df2dicom(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """this method is called before once before running all tests"""
        super(Df2dicom, cls).setUpClass()
        cls.test_assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        cls.test_mammo_dir = os.path.join(cls.test_assets_dir, 'sample_mammograms')
        cls.df = dicom2df(cls.test_mammo_dir, with_pixels=True)
        cls.outfile = SAMPLE_SOP_INSTANCE_UID
    
    def test_df2dicom_original_png(self):
        with tempfile.TemporaryDirectory() as outdirpath:
            df2dicom(
                self.df,
                outdirpath,
                do_image_deidentification=False,
                output_file_format="png"
            )
            # Is there a PNG file in the output directory
            self.assertTrue(
                f"{self.outfile}.png" in os.listdir(outdirpath),
                msg=f'list files in outdir: {os.listdir(outdirpath)}'
            )
            try:
                im = Image.open(os.path.join(outdirpath, f"{self.outfile}.png"))
            except IOError:
                self.fail("Expected image file cannot be opened")

    def test_df2dicom_deid_png(self):
        with tempfile.TemporaryDirectory() as outdirpath:
            df2dicom(
                self.df,
                outdirpath,
                do_image_deidentification=True,
                output_file_format="png"
            )
            # Is there a PNG file in the output directory
            self.assertTrue(
                f"{self.outfile}.png" in os.listdir(outdirpath),
                msg=f'list files in outdir: {os.listdir(outdirpath)}'
            )
            try:
                im = Image.open(os.path.join(outdirpath, f"{self.outfile}.png"))
            except IOError:
                self.fail("Expected image file cannot be opened")