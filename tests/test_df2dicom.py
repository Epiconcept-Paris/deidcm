# -*- coding: utf-8 -*-

import unittest
import os
import tempfile
import pydicom

import pandas as pd
from pydicom.errors import InvalidDicomError
from PIL import Image

from deidcm.dicom.dicom2df import (
    dicom2df
)

from deidcm.dicom.df2dicom import (
    df2dicom,
    df2hdh
)

SAMPLE_SOP_INSTANCE_UID = "1.3.6.1.4.1.14519.5.2.1.1239.1759.586725248951242926783849287982"
SOP_INSTANCE_UID_HEADER = "SOPInstanceUID_0x00080018_UI_1____"


class Df2dicom(unittest.TestCase):
    """
    The following class contains testing methods for df2dicom.
    The DICOM attributes are not deidentified in this part. For this reason,
    UIDs will not be deidentified during these tests (for attribute
    deidentification, see MetadataDeidentificationTest)
    """
    @classmethod
    def setUpClass(cls):
        """this method is called once before running all tests"""
        super(Df2dicom, cls).setUpClass()
        cls.test_assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        cls.test_mammo_dir = os.path.join(
            cls.test_assets_dir, 'sample_mammograms')
        cls.df = dicom2df(cls.test_mammo_dir, with_pixels=True)
        cls.outfile = SAMPLE_SOP_INSTANCE_UID

    def test_df2dicom_original_png(self):
        """df2dicom with no image deidentification and output in PNG"""
        with tempfile.TemporaryDirectory() as outdirpath:
            df2dicom(
                self.df,
                outdirpath,
                do_image_deidentification=False,
                output_file_formats=["png"]
            )
            # Is there a PNG file in the output directory
            self.assertIn(
                f"{self.outfile}.png", os.listdir(outdirpath),
                msg=f'list files in outdir: {os.listdir(outdirpath)}'
            )
            try:
                Image.open(os.path.join(outdirpath, f"{self.outfile}.png"))
            except IOError:
                self.fail("Expected image file cannot be opened")

    def test_df2dicom_deid_png(self):
        """df2dicom with image deidentification and output in PNG"""
        with tempfile.TemporaryDirectory() as outdirpath:
            df2dicom(
                self.df,
                outdirpath,
                do_image_deidentification=True,
                output_file_formats=["png"]
            )
            # Is there a PNG file in the output directory
            self.assertIn(
                f"{self.outfile}.png", os.listdir(outdirpath),
                msg=f'list files in outdir: {os.listdir(outdirpath)}'
            )
            try:
                Image.open(os.path.join(outdirpath, f"{self.outfile}.png"))
            except IOError:
                self.fail("Expected image file cannot be opened")

    def test_df2dicom_deid_dcm(self):
        """df2dicom with image deidentification and output in DCM"""
        with tempfile.TemporaryDirectory() as outdirpath:
            df2dicom(
                self.df,
                outdirpath,
                do_image_deidentification=True,
                output_file_formats=["dcm"]
            )
            # Is there a DCM file in the output directory
            self.assertIn(
                f"{self.outfile}.dcm", os.listdir(outdirpath),
                msg=f'list files in outdir: {os.listdir(outdirpath)}'
            )
            try:
                pydicom.dcmread(os.path.join(
                    outdirpath, f"{self.outfile}.dcm"))
            except (InvalidDicomError, TypeError):
                self.fail("Expected dicom file cannot be opened")

    def test_df2dicom_original_dcm(self):
        """df2dicom with no image deidentification and output in DCM"""
        with tempfile.TemporaryDirectory() as outdirpath:
            df2dicom(
                self.df,
                outdirpath,
                do_image_deidentification=False,
                output_file_formats=["dcm"]
            )
            # Is there a DCM file in the output directory
            self.assertIn(
                f"{self.outfile}.dcm",  os.listdir(outdirpath),
                msg=f'list files in outdir: {os.listdir(outdirpath)}'
            )
            try:
                pydicom.dcmread(os.path.join(
                    outdirpath, f"{self.outfile}.dcm"))
            except (InvalidDicomError, TypeError):
                self.fail("Expected dicom file cannot be opened")

    def test_df2dicom_multiformat(self):
        """df2dicom with image deidentification and output in DCM and PNG"""
        with tempfile.TemporaryDirectory() as outdirpath:
            df2dicom(
                self.df,
                outdirpath,
                do_image_deidentification=False,
                output_file_formats=["png", "dcm"]
            )
            self.assertIn(
                f"{self.outfile}.dcm", os.listdir(outdirpath),
                "outdir should contain a dicom file"
            )
            self.assertIn(
                f"{self.outfile}.png", os.listdir(outdirpath),
                "outdir should contain a png file"
            )

    def test_df2hdh_deid_img(self):
        """nominal case"""
        with tempfile.TemporaryDirectory() as outdirpath:
            df2hdh(df=self.df, outdir=outdirpath, exclude_images=False)

            self.assertIn('meta.csv', os.listdir(outdirpath))
            self.assertIn(f'{self.outfile}.png',
                          os.listdir(outdirpath))

    def test_df2hdh_meta_only(self):
        """nominal case"""
        with tempfile.TemporaryDirectory() as outdirpath:
            df2hdh(df=self.df, outdir=outdirpath, exclude_images=True)

            self.assertIn('meta.csv', os.listdir(outdirpath))
            self.assertNotIn(f'{self.outfile}.png',
                             os.listdir(outdirpath))

            meta_csv = os.path.join(outdirpath, 'meta.csv')

            output_df = pd.read_csv(meta_csv)
            self.assertEqual(
                output_df[SOP_INSTANCE_UID_HEADER][0],
                SAMPLE_SOP_INSTANCE_UID,
                "The pre-treatment and post-treatment SOP Instance UID should be identical"
            )
