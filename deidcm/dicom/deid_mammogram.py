"""This module is a mammograms deidentification toolbox.

This module contains functions related to deidentification of mammograms. It
fulfills the following purposes:

* deidentifying mammogram's images
* deidentifying mammogram's metadata
"""

import re
import os
import uuid
import base64
import string
import hashlib
import warnings
from random import choice
from typing import List
from datetime import datetime
from datetime import timedelta

import pydicom
from pydicom import Dataset
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFilter
from easyocr import Reader

from deidcm.config import Config
from deidcm.dicom.dicom2df import dicom2df
from deidcm.dicom.utils import log


def deidentify_image_ndarray(ds: Dataset) -> np.ndarray:
    """Deidentify image and return the image as a numpy array"""
    img = get_PIL_image(ds)

    if img is None:
        raise ValueError(f'Cannot open image from pydicom dataset {ds}')

    ocr_data = get_text_areas(np.array(img))
    pixels = ds.pixel_array
    pixels = hide_text(pixels, ocr_data) if ocr_data else pixels
    return pixels


def deidentify_image_dcm(infile: str) -> bytes:
    """Deidentify image and return bytes according to ds settings"""
    ds = pydicom.read_file(infile)
    pixels = deidentify_image_ndarray(ds)
    return numpy2bytes(pixels.copy(), ds)


def deidentify_image_png(infile: str, outdir: str, filename: str) -> None:
    """Deidentify and write a given mammogram's image in outdir as filename.png

    This function invokes the OCR reader for getting all potential words on a 
    mammogram's image. Then, it hides all found words by higlighting them in black. 

    Args:
        infile: The path of the DICOM file to deidentify.
        outdir: The path of the directory that will store the output.
        filename: The name of the resulting PNG file. (don't add the file extension).
    """
    ds = pydicom.read_file(infile)
    pixels = deidentify_image_ndarray(ds)
    outfile = os.path.join(outdir, filename)
    save_deidentified_image_png(pixels, outfile)


def save_deidentified_image_png(pixels: np.ndarray, outfile: str) -> None:
    """write a deidentified mammogram's image in outdir as outfile.png"""
    try:
        Image.fromarray(pixels).save(f'{outfile}.png')
    except TypeError:
        dimensions = pixels.shape
        if len(dimensions) == 3 and all(map(lambda x: x > 3, dimensions)):
            log("3D image, cannot process, cannot write PNG")
        else:
            raise TypeError(f"Unknown format for pixels : {dimensions}")


def get_LUT_value(data, window, level):
    """Apply the RGB Look-Up Table for the given
       data and window/level value."""
    return np.piecewise(data,
                        [data <= (level - 0.5 - (window - 1) / 2),
                         data > (level - 0.5 + (window - 1) / 2)],
                        [0, 255, lambda data: ((data - (level - 0.5)) /
                         (window - 1) + 0.5) * (255 - 0)])


def get_PIL_image(dataset: pydicom.dataset.Dataset) -> Image:
    """Get Image object from Python Imaging Library(PIL)

    Get the image from the pydicom dataset and convert it from a numpy.ndarray
    to a PIL image object. If available, the function will use metadata information 
    contained inside the pydicom dataset for the conversion.  

    Args:
        dataset: A pydicom dataset which can be obtained from a DICOM file.

    Returns:
        Image: A PIL image object.
    """

    if ('PixelData' not in dataset):
        log("Cannot get image -- DICOM dataset does not have pixel data")
        return None
    # can only apply LUT if these window info exists
    if ('WindowWidth' not in dataset) or ('WindowCenter' not in dataset):
        bits = dataset.BitsAllocated
        samples = dataset.SamplesPerPixel
        if bits == 8 and samples == 1:
            mode = "L"
        elif bits == 8 and samples == 3:
            mode = "RGB"
        elif bits == 16:
            # not sure about this -- PIL source says is 'experimental'
            # and no documentation. Also, should bytes swap depending
            # on endian of file and system??
            mode = "I;16"
        else:
            raise TypeError("Don't know PIL mode for %d BitsAllocated "
                            "and %d SamplesPerPixel" % (bits, samples))
        # PIL size = (width, height)
        size = (dataset.Columns, dataset.Rows)
        # Recommended to specify all details
        # by http://www.pythonware.com/library/pil/handbook/image.htm
        im = Image.frombuffer(mode, size, dataset.PixelData,
                              "raw", mode, 0, 1)
    else:
        ew = dataset['WindowWidth']
        ec = dataset['WindowCenter']
        ww = int(ew.value[0] if ew.VM > 1 else ew.value)
        wc = int(ec.value[0] if ec.VM > 1 else ec.value)
        image = get_LUT_value(dataset.pixel_array, ww, wc)
        # Convert mode to L since LUT has only 256 values:
        #   http://www.pythonware.com/library/pil/handbook/image.htm
        im = Image.fromarray(image).convert('L')
    return im


def numpy2bytes(pixels: np.ndarray, ds: pydicom.dataset.Dataset) -> bytes:
    """Returns bytes form of a numpy array built with proper ds' settings"""
    # pixels[pixels < 300] = 0
    if ds.BitsAllocated == 8:
        return pixels.astype(np.uint8).tobytes()
    elif ds.BitsAllocated == 16:
        return pixels.astype(np.uint16).tobytes()
    # return pixels.tobytes()


def get_text_areas(pixels: np.ndarray, languages: list = ['fr']) -> list:
    """Read and return words of an image.

    This function takes a pixel array in input and submits it to the easyOCR Reader.
    This Reader will then return a list of found words. This function implicitly 
    remove authorized words from the computed list.

    Args:
        pixels: An array representing an image.
        languages:
            A list of supported languages for the OCR Reader.
            This allows to submit images with text written in different languages.

    Returns:
        list: A list of words detected on the submitted image.
    """
    reader = Reader(languages, gpu=False, verbose=False)
    ocr_data = reader.readtext(pixels)
    # ocr data[0][2] is the level of confidence of the result
    # If the result is near 0, it is very likely that there is no text
    try:
        if ocr_data[0][2] > 0.3:
            return remove_authorized_words_from(ocr_data)
    # If ocr_data is empty, trying to access for
    # checking level of confidence will raise IndexError
    except IndexError:
        return []


def remove_authorized_words_from(ocr_data: list) -> list:
    """Remove authorized words from ocr_data list

    This function allows to remove authorized words from easyOCR output.
    It is useful if you want to keep some text information on your image such
    as image laterality information (RMLO, LCC, OBLIQUE G...).

    Args:
        ocr_data: A list of words and coordinates obtained after submitting an image to easyOCR Reader.

    Returns:
        The same list of words and coordinates minus the authorized words elements.
    """
    config = Config()
    if ocr_data is None:
        filtered_ocr_data = ocr_data
    else:
        filtered_ocr_data = []
        for data in ocr_data:
            if data[1].upper() in config.authorized_words:
                log(f'Ignoring word {data[1].upper()}')
            else:
                filtered_ocr_data.append(data)
    return filtered_ocr_data


def hide_text(pixels: np.ndarray, ocr_data: list, color_value: str = "black", mode: str = "rectangle", margin=300) -> np.ndarray:
    """Censor text present on the pixels array representing an image.

    Take the input image and draw new shapes with PIL package in order to
    censor OCR-detected words.

    Args:
        pixels: A pixels array representing an image
        ocr_data: A list of words and coordinates obtained by easyOCR Reader after submitting an image.
        color_value: A string indicating the color of the rectangle used for censoring information (`white` or `black`)
        mode: A string indicating the method for censoring information. (`blur` or `rectangle`)

    Returns:
        The deidentified pixels array.
    """
    # Create a pillow image from the numpy array
    im = Image.fromarray(pixels)
    # Gets the coordinate of the top-left and the bottom-right points
    for found in ocr_data:
        # This condition avoids common false positives
        if found[1] != "" and len(found[1]) > 1:
            x1, y1 = int(found[0][0][0]), int(found[0][0][1])
            x2, y2 = int(found[0][2][0]), int(found[0][2][1])

            if x1 < x2:
                x1 = x1 - margin
                x2 = x2 + margin
            else:
                x1 = x1 + margin
                x2 = x2 - margin

            if y1 < y2:
                y1 = y1 - margin
                y2 = y2 + margin
            else:
                y1 = y1 + margin
                y2 = y2 - margin

            box = (x1, y1, x2, y2)

            # Applies a hiding effect
            if mode == "blur":
                cut = im.crop(box)
                for i in range(30):
                    cut = cut.filter(ImageFilter.BLUR)
                im.paste(cut, box)
            else:
                # Add a black rectangle on the targeted text
                draw = ImageDraw.Draw(im)

                # If the value in the pixel array is a tuple, the color has to be a tuple (RGB image)
                if color_value == 'white':
                    color = (255, 255, 255) if type(
                        pixels[0][0]) == tuple else 255
                else:
                    color = (0, 0, 0) if type(pixels[0][0]) == tuple else 0
                draw.rectangle([x1, y1, x2, y2], fill=color)
                del draw

    return np.asarray(im)


def deidentify_attributes(indir: str, outdir: str, org_root: str, erase_outdir: bool = True) -> pd.DataFrame:
    """Produce a Pandas dataframe with deidentified information from a folder of DICOM files.

    This function creates a Pandas dataframe from all files present in the `indir` folder.
    Then, it loads the deidentification recipe and iterates through the dataframe to
    deidentify its content. Finally, it returns the deidentified dataframe object. 

    It also takes `outdir` and `erase_outdir`
    arguments for handling output directory auto-cleaning in the context of a data
    pipeline. If you're not interested in auto-cleaning your output repository, simply
    specify `outdir` and set `erase_outdir` to `False`.

    Args:
        indir: The input directory (DICOM files to deidentify)
        outdir: The output directory (deidentified/resulting files)
        org_root: An organization root identifier for deidentifying DICOM UIDs.
        erase_outdir: Empty the output directory if True

    Returns:
        A Pandas dataframe containing all metadata/attributes information.
    """
    if False in list(map(os.path.exists, [indir, outdir])):
        raise ValueError(f"Path {indir} or {outdir} does not exist.")

    if erase_outdir:
        for file in os.listdir(outdir):
            os.remove(os.path.join(outdir, file))

    df = dicom2df(indir)

    config = Config()
    for file in df.index:
        for attribute in df.columns:
            value = df[attribute][file]
            if attribute != 'FilePath':
                df.loc[file, attribute] = apply_deidentification(
                    attribute,
                    value,
                    config.recipe,
                    org_root
                )
    df['PatientIdentityRemoved_0x00120062_CS_1____'] = 'YES'
    return df


def get_id(id_attribute):
    """reformats the id stored as a string 0xYYYYZZZZ to a tuple"""
    y_id = '0x' + id_attribute[6:len(id_attribute)]
    return (id_attribute[0:6], y_id)


def apply_deidentification(attribute: str, value: str, recipe: dict, org_root: str):
    """Deidentifies the attribute depending on the deidentification recipe"""
    attr_el = attribute.split('_')
    tags = list(filter(lambda x: x if x.startswith('0x') else None, attr_el))
    valuerep = get_vr(attr_el)
    rules = list(map(lambda x: get_general_rule(
        x, recipe["general_rules"]), tags))
    specific_rules = get_specific_rule(tags, recipe["specific_rules"])
    rules = [specific_rules] if specific_rules is not None else rules

    if 'RETIRER' in rules:
        return float("NaN")
    elif 'EFFACER' in rules:
        return ''
    elif 'PSEUDONYMISER' in rules:
        return deidentify(tags, valuerep, value, org_root)
    elif 'CONSERVER' in rules:
        return value
    else:
        raise ValueError(f"Unknown rule {rules}")


def get_vr(attr_el: list) -> str:
    """Isolates and returns the VR of the attribute

    If the attribute is inside one or more sequence(s), it looks for
    the last VR. For example: something like '_SQ_..._SQ_..._LO_' will 
    return 'LO'. In the case of an empty sequence, it will return 'SQ'.
    """
    vr = attr_el[2]
    if vr != 'SQ':
        return vr
    else:
        def detectVR(x): return x if str.isupper(x) and x != 'SQ' else None
        vr = list(filter(detectVR, attr_el))
        return vr[0] if len(vr) == 1 else 'SQ'


def get_general_rule(tag: str, recipe: dict) -> str:
    """Get the rule associated with the given tag in `recipe.json`

    Args:
        tag: A DICOM tag
        recipe: A Python dictionary containing recipe elements. See `load_recipe()`

    Returns:
        The action associated to this DICOM tag in the provided recipe. It can be anything among deidentification actions (CONSERVER, RETIRER EFFACER, PSEUDONYMISER)
    """
    # rule for 0x50xxxxxx, 0x60xx4000, 0x60xx3000, 0xggggeeee where gggg is odd
    if re.match('^(0x60[0-9a-f]{2}[3-4]{1}000|0x50[0-9a-f]{6})$', tag) or \
            int(tag[2:6], 16) % 2:
        return 'RETIRER'
    # normal tag
    else:
        try:
            return recipe[tag][2]
        except KeyError:
            return 'RETIRER'


def get_specific_rule(tags: List[str], recipe: dict) -> str:
    """Extract the specific rule from a list of tags in `recipe.json` if there is one.

    Args:
        tags: A list of DICOM tags. The parent attribute is always before the child attribute. 
            For instance, if we take ['AAA', 'BBB', 'CCC'], 'AAA' is a sequence containing 'BBB' and 'BBB'
            is a sequence containing the attribute 'CCC'.  
        recipe: A Python dictionary containing recipe elements. See `load_recipe()`

    Returns:
        The action associated to this DICOM tag in the provided recipe. Same values as `get_general_rules`. 
            It can also return `None` if no specific rules are defined for tags inside the list.
    """
    if len(tags) == 1:
        return

    child_tag = tags[-1]
    if child_tag not in recipe.keys():
        return

    if recipe[child_tag]['sequence'] not in tags:
        return

    return recipe[child_tag]['rule']


def deidentify(tags: list, vr: str, value: str, org_root: str) -> None:
    """deidentify a single attribute of a given tag

    Applies a deidentification process depending on the value representation
    (or the tag) of the given attribute.

    Arguments:
    tag         -- tag of the attribute
    vr          -- DICOM Value Representation of the attribute
    value       -- value of the attribute
    id_patient  -- unique identifier of the patient in a LUT
    """
    if not pd.isna(value):
        if vr in ['DA', 'DT']:
            # return offset4date(value) if value != '' else value
            return get_first_day_year(value) if value != '' else value
        elif vr == 'TM':
            return hide_time()
        elif vr == 'PN' or any_in(tags, ['0x00100020']):
            return f"PATIENT^{gen_dummy_str(8, 0)}"
        elif vr == 'OB' and any_in(tags, ['0x00340007']):
            return datetime.strptime('20220101', '%Y%m%d').isoformat()
        elif vr in ['SH', 'LO']:
            return replace_with_dummy_str(vr) if value != '' else value
        elif vr == 'UI':
            return gen_dicom_uid('', value, org_root)
        elif vr == 'OB' and any_in(tags, ['0x00340005', '0x00340002']):
            return base64.b64encode(gen_uuid128(value)).decode("UTF-8")
        elif vr == 'UC' and any_in(tags, ['0x00189367']):
            return gen_uuid128(value).hex()
    else:
        return value


def any_in(list1: list, list2: list) -> bool:
    """Check if at least one item in list1 exists in list2"""
    return not set(list1).isdisjoint(list2)


def gen_dicom_uid(patient_id: str, guid: str, org_root: str) -> str:
    """Create a DICOM GUID based on the patient_id + original guid

    Args:
        patient_id: An identifier generated for each patient of your project.
        guid: The DICOM UID to deidentify.
        org_root: An organization root identifier for deidentifying DICOM UIDs.

    """
    base4hash = f"{patient_id}{guid.replace('.', '')}"
    hash_value = int(hashlib.sha256(base4hash.encode('utf8')).hexdigest(), 16)
    return f"{org_root}.{str(hash_value)[:30]}"


def gen_dicom_uid2() -> str:
    """Returns a DICOM UUID build from the Derived UID method (see standard)"""
    return f"2.25.{uuid.uuid1().int}"


def gen_uuid128(original_uuid) -> bytes:
    """Generates a 128-bit UUID

    Generates and returns a universally unique identifier generated from
    SHA 256 hash algorithm (256 bits) which is then truncated to a 128 bits
    uuid

    original_uuid   -- original uuid/value of the DICOM attribute
    """
    return base64.b64encode(hashlib.sha256(original_uuid.encode('utf8')).hexdigest()[:16].encode('UTF-8'))


def offset4date(date: str, offset: int = 100000) -> str:
    """Takes a date YYYYMMDD and an offset in days. Returns (date - offset)"""
    d = datetime.strptime(date[:8], '%Y%m%d') - timedelta(days=offset)
    return d.strftime('%Y%m%d')


def get_first_day_year(date: str) -> str:
    """Takes a date YYYYMMDD. Returns YYYY0101"""
    return f"{date[:4]}0101"


def hide_time() -> str:
    """Overwrites the previous time value with the 000000 dummy value"""
    return '000000'


def replace_with_dummy_str(valuerep: str) -> str:
    """Generates a random string which length depends on its VR"""
    if valuerep == 'SH':
        return gen_dummy_str(16, 1)
    elif valuerep == 'LO':
        return gen_dummy_str(64, 1)
    else:
        raise ValueError(f"not supported VR : {valuerep} for dummy str")


def gen_dummy_str(length: int, mode: int) -> str:
    """Generates a random string of a given length

    Arguments:
    length  -- The length of the returned string
    mode    -- 1 for letters / 0 for numbers
    """
    if mode:
        return ''.join(choice(string.ascii_letters) for _ in range(length))
    else:
        return ''.join(choice(string.digits) for _ in range(length))


def replace_patient_name(number: int) -> str:
    return f"PATIENT^{number}"


def p08_005_update_summary(summary, file_path, ocr_data):
    summary += "\n" + file_path + "\n↪words : "
    ocr_words = []
    for found in ocr_data:
        if ' ' in found[1]:
            new_tuple = (found[0], found[1].replace(' ', ''), found[2])
            ocr_data.remove(found)
            ocr_data.append(new_tuple)
        ocr_words.append(found[1])
    for found in sorted(ocr_words):
        summary += found.lower() + " |"
    return summary
