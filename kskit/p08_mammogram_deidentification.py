import os
import string
import time
import shutil
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from easyocr import Reader
from dpiste import dicom2png, utils, report
from .dicom import dicom2df

def p08_001_anonymize_folder():
    """
    Anonymize a complete directory of DICOM.

    @param

    indir = the initial directory of DICOM to de-identify
    outdir = the final director of DICOM which have been de-identied
    """
    start_time = time.time()
    nb_images_processed = 1
    summary = """\n\n\n
Here is a summary of the DICOMs that have been de-identified.\n\n\n
    """

    indir = utils.get_home('data', 'input', 'hdh','')
    outdir = utils.get_home('data','output','hdh','')
    outdir_intermediate = utils.get_home('data','transform','hdh','')
    confidential_attr_path = utils.get_home('data','confidential_attributes.json')

    list_dicom = sorted(os.listdir(indir))
    for file in list_dicom:
    
        nb_files = len(list_dicom)
        
        if indir.endswith("/"):
            input_path = indir + file
        else:
            input_path = indir + '/' + file
        
        if outdir.endswith("/"):
            output_path = outdir  + os.path.basename(file)
            output_ds = outdir_intermediate + os.path.basename(file) + ".txt"
            output_summary = outdir_intermediate + "summary.log"
        else:
            output_path = outdir  + '/' + os.path.basename(file)
            output_ds = outdir_intermediate + "/" + os.path.basename(file) + ".txt"
            output_summary = outdir_intermediate + "/summary.log"

        (pixels, ds) = dicom2png.dicom2narray(input_path)

        ocr_data = p08_002_get_text_areas(pixels)

        if len(ocr_data):
            print("\n___________A text area has been detected : " + input_path + "___________\n")
            pixels = p08_003_hide_text(pixels, ocr_data)
            ds = p08_004_de_identify_ds(ds, confidential_attr_path)
            dicom2png.narray2dicom(pixels, ds, output_path)
        else:
            print("\nNo text area detected\n")
            print(input_path, output_path)
            shutil.copy2(input_path, output_path)

        print(nb_images_processed, "/", nb_files, "DICOM(s) de-identified")

        with open(output_ds,'a') as f:
            file_path = indir + file
            text = input_path + '\n' + str(ds) + '\n' + "Words recognized : " + \
               str(ocr_data) + '\n'
            f.write(text)

        summary = p08_005_update_summary(summary, file_path, ocr_data)
        nb_images_processed += 1

    
    time_taken = time.time() - start_time
    with open(output_summary, 'w') as f:
        f.write(
          str(round(time_taken/60)) + " minutes taken to de-identify all images.\n" + \
            summary
        )




def p08_002_get_text_areas(pixels):
    """
    Easy OCR function. Gets an image at the path below and gets the 
    text of the picture. 
    """
    reader = Reader(['fr'])
    return reader.readtext(pixels)



def p08_003_hide_text(pixels, ocr_data, mode = "black"):
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

                #If the value is a tuple, the color has to be a tuple (RGB image)
                color = (0,0,0) if type(pixels[0][0]) == tuple else 0
                    
                draw.rectangle([x1, y1, x2, y2], fill=color)
                del draw

    return np.asarray(im)



def p08_004_de_identify_ds(ds, confidential_attr_path):
    """Deidentifies the dataset of the DICOM passed in parameter"""
    attributes = filter_DICOM_attributes(dir(ds))   

    with open(confidential_attr_path) as f:
        confidential_attributes = json.load(f)

    remove_confidential_attributes(confidential_attributes, attributes, ds)
    add_deid_required_attributes(ds)
    


def filter_DICOM_attributes(attributes):
    """Removes python basic attributes and keeps only DICOM attributes"""
    index_attribute = 0
    while index_attribute < len(attributes):
        attribute = attributes[index_attribute]
        if len(attribute) != 0 and attribute[0] not in string.ascii_uppercase:
            attributes.remove(attributes[index_attribute])
        else:
            index_attribute += 1
    return attributes



def remove_confidential_attributes(confidential_attributes, attributes, ds):
    """Compares the DICOM's attributes to attributes known for being at risk if kept in clear"""
    
    """
    for attribute in attributes:
        if attribute in confidential_attributes:
            (deid_mode, id_attribute) = confidential_attributes[attribute]
            x_id, y_id = get_id(id_attribute)
            
            #Zero-length string
            if deid_mode == 'Z' and ds[x_id, y_id].value not in ['','UNKNOWN']:
                print("ATTRIBUT NON ANONYMISE :", attribute, ds[x_id, y_id].value)
                ds[x_id, y_id].value = ''
            #Delete
            elif deid_mode == 'X' and ds[x_id, y_id].value not in ['','UNKNOWN']:
                #print("ATTRIBUT NON ANONYMISE :", attribute, ds[x_id, y_id].value)
                delattr(ds, attribute)
    #TODO: Investigate on the necessity of removing the private tags
    #ds.remove_private_tags()
    """
    recipe = DeidRecipe("/home/williammadie/GitHub/deep.piste/dpiste/test_reports/deid.dicom-group")
    recipe.deid
    OrderedDict([('format', 'dicom'),
                ('values',
                OrderedDict([('cookie_names',
                                [{'action': 'SPLIT',
                                'field': 'PatientID',
                                'value': 'by="^";minlength=4'}]),
                            ('operator_names',
                                [{'action': 'FIELD',
                                'field': 'startswith:Operator'}])])),
                ('fields',
                OrderedDict([('instance_fields',
                                [{'action': 'FIELD',
                                'field': 'contains:Instance'}])])),
                ('header',
                [{'action': 'ADD',
                    'field': 'PatientIdentityRemoved',
                    'value': 'Yes'},
                {'action': 'REPLACE',
                    'field': 'values:cookie_names',
                    'value': 'var:id'},
                {'action': 'REPLACE',
                    'field': 'values:operator_names',
                    'value': 'var:source_id'}])])


def add_deid_required_attributes(ds):
    """Adds the de-identification attributes required by the DICOM standard"""
    #Deletes the De-identificationMethodSequence attribute and all its sub-attributes
    """
    if (0x0012, 0x0064) in ds:
        delattr(ds, 'DeidentificationMethodCodeSequence')
    """
    
    #PatientIdentityRemoved CS : YES
    if (0x0012, 0x0062) not in ds:
        ds.add_new([0x0012, 0x0062], 'CS', 'YES')
    else:
        ds[0x0012, 0x0062].value = 'YES'
    #BurnedInAnnotation CS : NO (Indicates whether or not image contains sufficient burned in annotation to identify the patient and date the image was acquired.)
    #TODO: investigate on the necessity to modify this attribute
    if (0x0028, 0x0301) not in ds:
        ds.add_new([0x0028, 0x0301], 'CS', 'NO')
    else:
        ds[0x0012, 0x0062].value = 'NO'



def get_id(id_attribute):
    """reformats the id stored as a string (0xYYYY,0xZZZZ) to a tuple"""
    id_attribute = id_attribute.replace('(','')
    id_attribute = id_attribute.replace(')','')
    beginning_ids = ["0x", "0x"]
    end_ids = id_attribute.split(",")
    beginning_ids[0] += end_ids[0]
    beginning_ids[1] += end_ids[1]
    return tuple(beginning_ids)
    



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