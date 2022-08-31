import re
import os
import uuid
import json
import glob
import base64
import string
import hashlib
import pydicom
import cv2
from random import choice
import numpy as np
import pandas as pd
from datetime import datetime
from datetime import timedelta
from pydicom.dataset import Dataset
from pydicom.pixel_data_handlers.util import (
    apply_color_lut,
    apply_modality_lut,
    apply_voi_lut,
    convert_color_space
)
from PIL import Image, ImageDraw, ImageFilter
from easyocr import Reader
from kskit.dicom.dicom2df import dicom2df
from kskit.dicom.utils import log


def deidentify_image(infile: str) -> bytes:
    """Deidentifies and returns infile as bytes"""
    ds = pydicom.read_file(infile)
    pixels = ds.pixel_array
    ocr_data = get_text_areas(pixels)
    pixels = hide_text(pixels, ocr_data) if ocr_data else pixels
    return numpy2bytes(pixels.copy(), ds)


def deidentify_image_png(infile: str, outdir: str, filename: str) -> None:
    """Deidentifies and writes a given mammogram in outdir as filename.png"""
    ds = pydicom.read_file(infile)
    ocr_data = get_text_areas(np.array(get_PIL_image(ds)))
    pixels = ds.pixel_array
    pixels = hide_text(pixels, ocr_data) if ocr_data else pixels
    outfile = os.path.join(outdir, f'{filename}.png')
    try:
        Image.fromarray(pixels).save(outfile)
    except TypeError:
        dimensions = pixels.shape
        if len(dimensions) == 3 and all(map(lambda x: x > 3, dimensions)):
            log("3D image, cannot process, kept unchanged")
            # TODO : Find a way to save a 3D img as a PNG file
        else:
            raise TypeError(f"Unknown format for pixels : {dimensions}")
    return


def get_LUT_value(data, window, level):
    """Apply the RGB Look-Up Table for the given
       data and window/level value."""
    return np.piecewise(data,
                        [data <= (level - 0.5 - (window - 1) / 2),
                         data > (level - 0.5 + (window - 1) / 2)],
                        [0, 255, lambda data: ((data - (level - 0.5)) /
                         (window - 1) + 0.5) * (255 - 0)])


def get_PIL_image(dataset):
    """Get Image object from Python Imaging Library(PIL)"""
    
    if ('PixelData' not in dataset):
        raise TypeError("Cannot show image -- DICOM dataset does not have "
                        "pixel data")
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


def numpy2bytes(pixels: np.ndarray, ds: pydicom.Dataset) -> bytes:
    """Returns bytes form of a numpy array built with proper ds' settings"""
    #pixels[pixels < 300] = 0
    if ds.BitsAllocated == 8:
        return pixels.astype(np.uint8).tobytes()
    elif ds.BitsAllocated == 16:  
        return pixels.astype(np.uint16).tobytes()
    #return pixels.tobytes()


def get_text_areas(pixels):
    """
    Easy OCR function. Gets an image at the path below and returns the 
    text of the picture. 
    """
    reader = Reader(['fr'], gpu=False, verbose=False)
    ocr_data = reader.readtext(pixels)
    # ocr data[0][2] is the level of confidence of the result
    # If the result is near 0, it is very likely that there is no text
    try:
        if ocr_data[0][2] > 0.3:
            return remove_authorized_words_from(ocr_data)
    except Exception:
        return []


def remove_authorized_words_from(ocr_data: list) -> list:
    """Prevents Authorized Words such as RMLO, LCC, OBLIQUE G to be censored"""
    authorized_words = load_authorized_words()
    if ocr_data is None:
        filtered_ocr_data = ocr_data
    else:
        filtered_ocr_data = []
        for data in ocr_data:
            if data[1].upper() in authorized_words:
                log(f'Ignoring word {data[1].upper()}')
            else:
                filtered_ocr_data.append(data)
    return filtered_ocr_data


def load_authorized_words() -> list:
    home_folder = os.environ.get('DP_HOME')
    if home_folder is None:
        raise ValueError('cannot load DP_HOME')
    filepath = os.path.join(home_folder, 'data', 'input', 'epiconcept', 'ocr_deid_ignore.txt')
    if not os.path.exists(filepath):
        raise FileNotFoundError(f'Cannot load {filepath}')
    with open(filepath, 'r') as f:
        words = list(map(str.strip, f.readlines()))
    return words


def hide_text(pixels, ocr_data, color_value = None, mode = "black"):
    """
    Get a NUMPY array, a list of the coordinates of the different text areas 
    in this array and (optional) a mode which can be : 
    blur" or "black". It returns the modified NUMPY array.

    MODES (optional):

    "black" mode (default) ==> add a black rectangle on the text areas
    "blur" mode            ==> blur the text areas
    """
    #Create a pillow image from the numpy array
    im = Image.fromarray(pixels)
    #Gets the coordinate of the top-left and the bottom-right points
    for found in ocr_data:
        #This condition avoids common false positives
        if found[1] != "" and len(found[1]) > 1:
            x1, y1 = int(found[0][0][0]), int(found[0][0][1])
            x2, y2 = int(found[0][2][0]), int(found[0][2][1])
            box = (x1,y1,x2,y2)
            
            #Applies a hiding effect
            if mode == "blur":
                cut = im.crop(box)
                for i in range(30):
                    cut = cut.filter(ImageFilter.BLUR)
                im.paste(cut, box)
            else:
                #Add a black rectangle on the targeted text
                draw = ImageDraw.Draw(im)

                #If the value in the pixel array is a tuple, the color has to be a tuple (RGB image)
                if color_value == 'white':
                    color = (255,255,255) if type(pixels[0][0]) == tuple else 255
                else:
                    color = (0,0,0) if type(pixels[0][0]) == tuple else 0
                draw.rectangle([x1, y1, x2, y2], fill=color)
                del draw

    return np.asarray(im)


def deidentify_attributes(indir: str, outdir: str, erase_outdir: bool = True) -> pd.DataFrame:
    """Deidentify a folder of dicom.

    Arguments:
    indir -- the input directory (files to deidentify)
    outdir -- the output directory (deidentified/resulting files)
    """
    if False in list(map(lambda x: os.path.exists(x), [indir, outdir])):
        raise ValueError(f"Path \"{indir}\" or \"{outdir}\" does not exist.")

    if erase_outdir:
        for file in os.listdir(outdir):
            os.remove(os.path.join(outdir, file))
    
    df = dicom2df(indir)
    recipe = load_recipe()

    for file in df.index:
        for attribute in df.columns:
            value = df[attribute][file]  
            if attribute != 'FilePath':
                df[attribute][file] = apply_deidentification(
                    attribute, 
                    value, 
                    recipe
                )
    df['PatientIdentityRemoved_0x00120062_CS_1____'] = 'YES'
    return df


def load_recipe() -> dict:
    """Gets the recipe from recipe.json and loads it into a python dict."""
    recipe = os.path.join(os.path.dirname(__file__), 'recipe.json')
    try:
        with open(recipe, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise ValueError(f"Recipe file {recipe} cannot be found.")
    

def get_id(id_attribute):
    """reformats the id stored as a string 0xYYYYZZZZ to a tuple"""
    y_id = '0x' + id_attribute[6:len(id_attribute)]
    return (id_attribute[0:6], y_id)


def apply_deidentification(attribute: str, value: str, recipe: dict):
    """Deidentifies the attribute depending on the deidentification recipe"""
    attr_el = attribute.split('_')
    tags = list(filter(lambda x: x if x.startswith('0x') else None, attr_el))
    valuerep = get_vr(attr_el)
    rules = list(map(lambda x: get_rule(x, recipe), tags))

    if 'RETIRER' in rules:
        return float("NaN")
    elif 'EFFACER' in rules:
        return ''
    elif 'PSEUDONYMISER' in rules:
        return deidentify(tags, valuerep, value)
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
        detectVR =lambda x: x if str.isupper(x) and x != 'SQ' else None 
        vr = list(filter(detectVR, attr_el))
        return vr[0] if len(vr) == 1 else 'SQ'


def get_rule(tag: str, recipe: dict) -> str:
    """Gets the rule associated with the given tag"""
    #rule for 0x50xxxxxx, 0x60xx4000, 0x60xx3000, 0xggggeeee where gggg is odd
    if re.match('^(0x60[0-9a-f]{2}[3-4]{1}000|0x50[0-9a-f]{6})$', tag) or \
        int(tag[2:6], 16) % 2:
        return 'RETIRER' 
    #normal tag  
    else:
        try:
            return recipe[tag][2]
        except KeyError:
            return 'RETIRER'


def deidentify(tags: list, vr: str, value: str) -> None:
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
            #return offset4date(value) if value != '' else value
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
            return gen_dicom_uid('', value)
        elif vr == 'OB' and any_in(tags, ['0x00340005', '0x00340002']):
            return base64.b64encode(gen_uuid128(value)).decode("UTF-8")
        elif vr == 'UC' and any_in(tags, ['0x00189367']):
            return gen_uuid128(value).hex()
    else:
        return value


def any_in(list1: list, list2: list) -> bool:
    """Check if at least one item in list1 exists in list2"""
    return not set(list1).isdisjoint(list2)


def gen_dicom_uid(patient_id: str, guid: str) -> str:
    """Creates a DICOM GUID based on the patient_id + original guid"""
    base4hash = f"{patient_id}{guid.replace('.', '')}"
    hash_value = int(hashlib.sha256(base4hash.encode('utf8')).hexdigest(), 16)
    return f"1.2.826.0.1.3680043.10.866.{str(hash_value)[:30]}"


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
            new_tuple = (found[0], found[1].replace(' ',''), found[2])
            ocr_data.remove(found)
            ocr_data.append(new_tuple)
        ocr_words.append(found[1])
    for found in sorted(ocr_words):
        summary += found.lower() + " |"
    return summary
