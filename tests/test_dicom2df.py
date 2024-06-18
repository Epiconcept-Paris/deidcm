# -*- coding: utf-8 -*-

import unittest
import os

import pandas as pd

from deidcm.dicom.dicom2df import (
    dicom2df
)


class Dicom2dfTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """this method is called once before running all tests"""
        super(Dicom2dfTest, cls).setUpClass()
        cls.test_assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        cls.test_mammo_dir = os.path.join(
            cls.test_assets_dir, 'sample_mammograms')

    def test_dicom2df(self):
        df = dicom2df(self.test_mammo_dir, with_pixels=True)
        self.assertEqual(type(df), pd.DataFrame)
        self.assertTrue('PixelData_0x7fe00010_OB_1____' in df.columns)
