"""
Reusable tools for deidentification purposes
"""


import os
import traceback
import base64
import json

import pandas as pd
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.sequence import Sequence
from PIL import Image
from deidcm.dicom.utils import log
from deidcm.dicom.deid_mammogram import (
    deidentify_image_ndarray,
    deidentify_image_png,
    save_deidentified_image_png,
    numpy2bytes
)

PIXEL = ('0x7fe0010', 'OB')
MAMMO_ID_COL = 'SOPInstanceUID_0x00080018_UI_1____'


def df2dicom(df, outdir, do_image_deidentification=False, test=False, output_file_formats=None):
    """
    Deidentifies DICOM files and generates PNG files for each mammogram alongside
    a CSV file containing all deidentified tags
    """
    for index in range(len(df)):
        ds = build_dicom(df, index, parent_path='')
        num_file = df[MAMMO_ID_COL][index]
        img_path = df["FilePath"][index]
        outfile = os.path.basename(img_path)

        # Backward compatibility with old tests in deidcm package
        # This parameter should not be True otherwise
        if test:
            ds.save_as(f"{outdir}/{outfile}", write_like_original=False)
            continue

        outpath = os.path.join(outdir, num_file)

        if output_file_formats is None:
            output_file_formats = ["png"]
        else:
            output_file_formats = [f.lower() for f in output_file_formats]

        if do_image_deidentification:
            ds = pydicom.read_file(img_path)
            pixels = deidentify_image_ndarray(ds)

        if "png" in output_file_formats:
            if do_image_deidentification:
                save_deidentified_image_png(pixels, outpath)
            else:
                pixels = get_original_img(img_path)
                Image.fromarray(pixels).save(f'{outpath}.png')

        if "dcm" in output_file_formats:
            if do_image_deidentification:
                ds.add_new(PIXEL[0], PIXEL[1], numpy2bytes(pixels, ds))
            else:
                ds.add_new(PIXEL[0], PIXEL[1], get_original_img(img_path))
            try:
                # write_like_original=False in order to force pydicom to write
                #  correct DICOM headers at file writing time
                ds.save_as(f'{outpath}.dcm', write_like_original=False)
            except (ValueError, AttributeError):
                traceback.print_exc()
                raise ValueError(f"DICOM file may be malformed")


def df2hdh(df: pd.DataFrame, outdir: str, exclude_images: bool) -> None:
    """Special pipeline for HDH. 

    Deidentifies all the mammograms listed in df
    Write all the deidentified mammograms in outdir
    Write df as meta.csv in outdir 
    """
    if not exclude_images:
        for _, index in enumerate(range(len(df))):
            try:
                deidentify_image_png(
                    df["FilePath"][index], outdir, df[MAMMO_ID_COL][index])
            except ValueError:
                traceback.print_exc()
                raise ValueError(
                    f"The file {df['FilePath'][index]} may be corrupted")
    df.to_csv(os.path.join(outdir, 'meta.csv'))


def get_original_img(filepath) -> bytes:
    """Finds and returns the original image"""
    return pydicom.read_file(filepath).pixel_array


def get_ds_attr(df, parent_path, attr):
    """Gets and returns a list of distinct @i extracted from the elements in the sequence"""
    # filters the columns names starting with parent_path and attr
    child_attr = [col.replace(parent_path + attr, '')
                  for col in df.columns if col.startswith(parent_path + attr)]
    # extract @i. and remove duplicates from the list
    child_attr = list(set([attr[:3] for attr in child_attr]))
    child_attr.sort()
    return child_attr


def build_seq(df, index, parent_path, seq_attr):
    """
    Builds and returns a pydicom sequence and : 0 for a basic sequence | 1 for an
    empty sequence that needs to be represented even if it is empty.
    """
    seq = Sequence()

    for ds_attr in get_ds_attr(df, parent_path, seq_attr):
        ds = build_dicom(df, index, parent_path+seq_attr+ds_attr)
        if ds is not None:
            seq.append(ds)
        else:
            return [], 1
    return seq, 0


def get_seq_attr(attrs):
    """
    Gets and returns a list of unique names of the sequence attributes 
    without the @child_attribute
    """
    nom_seq = set([attr.split('@')[0]
                  for attr in attrs])  # extract the part before the @
    return list(nom_seq)  # keep only unique values


def get_value(df, index, parent_path, child_path):
    """Gets and returns the value of a given attribute name"""
    return df[parent_path+child_path][index]


def get_vr(column_name):
    """Returns the type as it is defined in the pydicom definition"""
    return pydicom.sequence.Sequence if 'SQ' in column_name else ''


def add_file_meta(df, ds, meta_attrs, index, parent_path):
    """Creates and returns a dataset containing the meta-information of the dicom file"""
    ds.file_meta = FileMetaDataset()
    for attr in meta_attrs:
        if not pd.isna(get_value(df, index, parent_path, attr)):
            attr_tag, attr_vr, attr_vm = attr.split('_')[1], attr.split('_')[

                2], attr.split('_')[3]
            attr_value = decode_unit(

                get_value(df, index, parent_path, attr), attr_vr, attr_vm)
            ds.file_meta.add_new(attr_tag, attr_vr, attr_value)

        # Fills 2 ds.properties needed in order to save the dicom file
        if '0x00020010' in attr_tag:
            if '1.2.840.10008.1.2.1' in attr_value:
                ds.is_little_endian, ds.is_implicit_VR = True, False
            elif ('1.2.840.10008.1.2.2' in attr_value) or ('1.2.840.10008.1.2.99' in attr_value):
                ds.is_little_endian, ds.is_implicit_VR = False, False
            else:
                ds.is_little_endian, ds.is_implicit_VR = True, True
    return ds


def build_dicom(df, index, parent_path=''):
    """Builds one DICOM file from the dataframe information"""
    seq_attrs, nonseq_attrs, meta_attrs = [], [], []
    child_attr = [col.replace(parent_path, '') for col in df.columns if col.startswith(
        parent_path)]  # name of the column without the parent name
    # filters child_attr into two lists (sequences and not sequences)
    [seq_attrs.append(attr) if get_vr(
        attr) == pydicom.sequence.Sequence else nonseq_attrs.append(attr) for attr in child_attr]
    if 'FilePath' in nonseq_attrs:
        nonseq_attrs.remove('FilePath')

    ds = Dataset()

    # NON-SEQUENCE ATTRIBUTES
    for attr in nonseq_attrs:
        if not pd.isna(get_value(df, index, parent_path, attr)):
            if attr != 'empty':
                try:
                    attr_tag, attr_vr, attr_vm = attr.split('_')[1], attr.split('_')[
                        2], attr.split('_')[3]
                except IndexError:
                    if attr != '':
                        log(
                            f'This attribute is malformed and will be ignored: {attr}', logtype=1)
                    continue
                if '0x0002' in attr_tag:
                    meta_attrs.append(attr)
                else:
                    ds.add_new(attr_tag, attr_vr, decode_unit(
                        get_value(df, index, parent_path, attr), attr_vr, attr_vm))
            else:
                return None

    # SEQUENCE ATTRIBUTES
    for attr in get_seq_attr(seq_attrs):
        # If the sequence is present in the DICOM, test_sequence would take a value != NaN
        for test in child_attr:
            if attr in test:
                test_sequence = test

        # If test_sequence == NaN, the sequence does not appear in this DICOM.
        if not pd.isna(get_value(df, index, parent_path, test_sequence)):
            seq, empty_but_present = build_seq(df, index, parent_path, attr)

            if not empty_but_present:
                # If the sequence is not empty then we add the sequence to the ds
                if seq:
                    ds.add_new(attr.split('_')[1], attr.split('_')[2], seq)
            # create an empty sequence (if the initial dicom had an empty sequence it has
            # to rebuild it
            else:
                ds.add_new(attr.split('_')[1], attr.split('_')[2], None)

    # META-FILE ATTRIBUTES
    ds = add_file_meta(df, ds, meta_attrs, index, parent_path)
    return ds


def decode_unit(value, vr, vm):
    """convert DICOM type to Python type"""
    # if the value is None : no need to decode
    if value == str(None):
        return None
    else:
        integer_types = ['IS', 'SS', 'SL', 'US', 'UL']
        known_encodings = ['CS', 'DS', 'FD', 'UN']
        if vm != '1':
            if (vr in integer_types or vr in known_encodings) and vm != '0':
                return [decode_unit(e, vr, '1') for e in json.loads(value)]
        else:
            if vr == 'OB' or vr == 'OW' or vr == 'UN':
                # alt if not working: return value.encode('utf8')
                return base64.b64encode(value.encode('UTF-8'))
            elif vr in integer_types:
                return int(value)
            elif vr == 'FD':
                return float(value)
        return value
