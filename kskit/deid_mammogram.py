import string
import hashlib
import json
import sys
import re
import uuid
from random import choice, randint
import numpy as np
from datetime import datetime
from datetime import timedelta
from pydicom.dataset import Dataset
from PIL import Image, ImageDraw, ImageFilter
from easyocr import Reader


def get_text_areas(pixels):
    """
    Easy OCR function. Gets an image at the path below and gets the 
    text of the picture. 
    """
    reader = Reader(['fr'])
    return reader.readtext(pixels)



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
    pixels = pixels/255
    im = Image.fromarray(np.uint8((pixels)*255))

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



def de_identify_ds(ds, RECIPE):
    """Deidentifies the dataset of the DICOM passed in parameter"""
    attributes = filter_DICOM_attributes(dir(ds))   

    with open(RECIPE) as f:
        recipe = json.load(f)

    ds = remove_confidential_attributes(recipe, attributes, ds)
    ds = add_deid_required_attributes(ds)
    return ds


def filter_DICOM_attributes(attributes):
    """Removes python basic attributes from the dataset and keeps only DICOM attributes"""
    index_attribute = 0
    while index_attribute < len(attributes):
        attribute = attributes[index_attribute]
        if len(attribute) != 0 and attribute[0] not in string.ascii_uppercase:
            attributes.remove(attributes[index_attribute])
        else:
            index_attribute += 1
    return attributes


def remove_confidential_attributes(recipe, attributes, ds):
    """Compares the DICOM's attributes to attributes known for being at risk if 
    kept in clear""" 
    for attribute in attributes:
        if attribute in recipe:
            spec_attribute = recipe[attribute]
            x_id, y_id = get_id(spec_attribute[0])
            
            #Calculates the age with the Birth Date
            if x_id == '0x0010' and y_id == '0x0030':
                if (0x0010, 0x1010) in ds and ds[0x0010, 0x1010].value == '':
                    ds[0x0010, 0x1010].value  = get_age(ds[x_id, y_id].value)
                elif (0x0010, 0x1010) not in ds and ds[x_id, y_id].value != '':
                    ds.add_new([0x0010, 0x1010], 'AS', get_age(ds[x_id, y_id].value))
        else:
            delattr(ds, attribute)
    return ds
    """
    #Zero-length string
    if deid_mode == 'Z' and ds[x_id, y_id].value not in ['','UNKNOWN']:
        #print("ATTRIBUT NON ANONYMISE :", attribute, ds[x_id, y_id].value)
        ds[x_id, y_id].value = ''
    #Delete
    elif deid_mode == 'X' and ds[x_id, y_id].value not in ['','UNKNOWN']:
        #print("ATTRIBUT NON ANONYMISE :", attribute, ds[x_id, y_id].value)
        delattr(ds, attribute)
    """
    #TODO: Investigate on the necessity of removing the private tags
    #ds.remove_private_tags()
    


def get_age(birth_date):
    """Takes the birth date of the patient and returns its age"""
    birth_year = int(birth_date[0:4])
    present_year = datetime.datetime.now().year
    patient_age = present_year - birth_year
    if 10 < patient_age and patient_age < 100:
        patient_age = "0" + str(patient_age) + "Y"
    elif patient_age < 10:
        patient_age = "00" + str(patient_age) + "Y"
    else:
        patient_age = str(patient_age) + "Y"
    print(patient_age)
    return patient_age 
    


def add_deid_required_attributes(ds):
    """Adds the de-identification attributes required by the DICOM standard"""
    
    #PatientIdentityRemoved CS : YES
    if (0x0012, 0x0062) not in ds:
        ds.add_new([0x0012, 0x0062], 'CS', 'YES')
    else:
        ds[0x0012, 0x0062].value = 'YES'
    
    #Deletes the De-identificationMethodSequence attribute and all its sub-attributes
    if (0x0012, 0x0064) in ds:
        delattr(ds, 'DeidentificationMethodCodeSequence')

    ds.add_new([0x0012, 0x0064], 'SQ', [])
    
    ds[0x0012, 0x0064].value.append(Dataset())
    ds[0x0012, 0x0064].value[0].add_new((0x0008, 0x0100), 'SH', '113100')
    ds[0x0012, 0x0064].value[0].add_new((0x0008, 0x0102), 'SH', 'DCM')
    ds[0x0012, 0x0064].value[0].add_new((0x0008, 0x0104), 'LO', 'Basic Application Confidentiality Profile')

    ds[0x0012, 0x0064].value.append(Dataset())
    ds[0x0012, 0x0064].value[1].add_new((0x0008, 0x0100), 'SH', '113101')
    ds[0x0012, 0x0064].value[1].add_new((0x0008, 0x0102), 'SH', 'DCM')
    ds[0x0012, 0x0064].value[1].add_new((0x0008, 0x0104), 'LO', 'Clean Pixel Data Option')

    ds[0x0012, 0x0064].value.append(Dataset())
    ds[0x0012, 0x0064].value[2].add_new((0x0008, 0x0100), 'SH', '113108')
    ds[0x0012, 0x0064].value[2].add_new((0x0008, 0x0102), 'SH', 'DCM')
    ds[0x0012, 0x0064].value[2].add_new((0x0008, 0x0104), 'LO', 'Retain Patient Characteristics Option')

    #Add the attribute DeidentificationMethod
    if (0x0012, 0X0063) in ds:
        delattr(ds, 'DeidentificationMethod')
    ds.add_new((0x0012, 0X0063), 'LO', 'Per DICOM PS 3.15 AnnexE. Details in 0012,0064')

    #BurnedInAnnotation CS : NO (Indicates whether or not image contains sufficient burned in annotation to identify the patient and date the image was acquired.)
    #TODO: investigate on the necessity to modify this attribute
    if (0x0028, 0x0301) not in ds:
        ds.add_new([0x0028, 0x0301], 'CS', 'YES')
    else:
        ds[0x0012, 0x0062].value = 'YES'

    """
    Print and change nested attributes (core elements)
    print("Nested attribute 1", ds[0x0008, 0x2218][0][0x0008, 0x0100].value)
    print("Nested attribute 2", ds[0x0008, 0x2218][0][0x0008, 0x0102].value)
    print("Nested attribute 3", ds[0x0008, 0x2218][0][0x0008, 0x0104].value)
    ds[0x0008, 0x2218][0][0x0008, 0x0104].value = 'Foot'
    """
    return ds



def get_id(id_attribute):
    """reformats the id stored as a string 0xYYYYZZZZ to a tuple"""
    y_id = '0x' + id_attribute[6:len(id_attribute)]
    return (id_attribute[0:6], y_id)


def apply_deidentification(tag: str, valuerep: str, value: str):
    """Deidentifies the attribute depending on the deidentification recipe"""
    rule = get_rule(tag)
    if rule == 'CONSERVER':
        return value
    elif rule == 'EFFACER':
        return ''
    elif rule == 'RETIRER':
        return None
    elif rule == 'PSEUDONYMISER':
        return deidentify(tag, valuerep, value)


def get_rule(tag: str) -> str:
    """Gets the rule associated with the given tag"""
    #rule for 0x50xxxxxx or 0x60xx4000 and 0x60xx3000
    if re.match('^(0x60[0-9a-f]{2}[3-4]{1}000|0x50[0-9a-f]{6})$', tag):
        return 'RETIRER' 
    #normal tag  
    else:
        return 'CONSERVER'


def deidentify(tag: str, valuerep: str, value: str, id_patient: str):
    """Applies a deidentification process depending on the value representation
    (or the tag) of the given attribute"""
    if valuerep in ['DA', 'DT']:
        return offset4date(value, '')
    elif valuerep == 'TM':
        return hide_time()
    elif valuerep == 'PN':
        return f"PATIENT^{gen_dummy_number()}"
    elif valuerep == 'OB' and tag == '0x00340007':
        return datetime.strptime('20220101', '%Y%m%d').isoformat()
    elif valuerep in ['SH', 'LO']:
        return replace_with_dummy_str(valuerep)
    elif valuerep == 'UI':
        return gen_dicom_uid('', value)
    elif valuerep == 'OB' and tag in ['0x00340005', '0x00340002']:
        return gen_uuid128(value)
    elif valuerep == 'UC' and tag == '0x00189367':
        return gen_uuid128(value).hex()


def gen_dicom_uid(patient_id: str, guid: str) -> str:
    """Creates a DICOM GUID based on the patient_id and original guid
    concatenation
    """
    base4hash = f"{patient_id}{guid.replace('.', '')}"
    hash_value = int(hashlib.sha256(base4hash.encode('utf8')).hexdigest(), 16)
    return f"1.2.826.0.1.3680043.10.866.{str(hash_value)[:30]}"


def gen_dicom_uid2() -> str:
    """Returns a DICOM UUID build from the Derived UID method (see standard)"""
    return f"2.25.{uuid.uuid1().int}"


def gen_uuid128(original_uuid) -> bytes:
    """Generates and returns a universally unique identifier generated from
    SHA 256 hash algorithm (256 bits) which is then truncated to a 128 bits
    uuid"""
    return hashlib.sha256(original_uuid.encode('utf8')).digest()[:16]


def offset4date(date: str, offset: int) -> str:
    """Takes a date YYYYMMDD and an offset in days. Returns (date - offset)"""
    d = datetime.strptime(date[:8], '%Y%m%d') - timedelta(days=offset)
    return d.strftime('%Y%m%d')


def hide_time() -> str:
    """Overwrites the previous time value with the 000000 dummy value"""
    return '000000'


def replace_with_dummy_str(valuerep: str) -> str:
    """Generates a random string which length depends on its VR"""
    if valuerep == 'SH':
        return gen_dummy_str(16)
    elif valuerep == 'LO':
        return gen_dummy_str(64)
    else:
        raise ValueError(f"not supported VR : {valuerep} for dummy str")


def gen_dummy_str(length: int) -> str:
    """Generates a random string of a given length"""
    ''.join(choice(string.ascii_letters) for _ in range(length))


def gen_dummy_number(length: int) -> str:
    """Generates a random string of a given length"""
    ''.join(choice(string.ascii_numbers) for _ in range(length))


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

if __name__ == "__main__":
    get_rule('0x50123456')
    get_rule('0x5')
    get_rule('0x50123456')
    get_rule('0x50123456')
    get_rule('0x50123456')
    get_rule('0x50123456')
    get_rule('0x50123456')
    get_rule('0x50123456')
    get_rule('0x50123456')