import random
import base64
import string
import itertools
import os
from datetime import datetime
from datetime import timedelta
from typing import List

import pydicom
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageFilter

from deidcm.dicom2png import dicom2narray
from deidcm.dicom.df2dicom import df2dicom
from deidcm.dicom.deid_mammogram import (
    deidentify_attributes,
    gen_uuid128,
    replace_with_dummy_str,
    gen_dicom_uid,
    get_text_areas
)
from deidcm.dicom.utils import write_all_ds, format_ds_tag
from deidcm.test_cases.cases import (
    ui_tags,
    sq_tags,
    dadt_tags,
    shlo_tags,
    tm_tags,
    rm_tags,
    kp_tags,
    er_tags
)

SAMPLE_ORG_ROOT = "SAMPLE_ORG_ROOT"
FONT_COLOR_THRESHOLD = 20

DICOM_PREFIX_UID = '1.3.6.1.4.1.14519.5.2.1.2135.6389.'
DICOM_SUFFIX_UID = 799402065306178004127703292730


def search_false_positives(indir, list_dicom, list_chosen, outdir_intermediate, repetition, nb_images_tested, fp, tn):
    summary = "\nF stands for the FONT path" + \
        "\nB stands for the BLUR strength" + \
        "\nS stands for the text SIZE"
    summary += "\n\n\nTested for detecting possible false positives x" + \
        str(repetition) + "\n\n\n"
    for _ in range(repetition):
        (pixels, ds, dicom, file_path, list_chosen) = get_random_dicom_ds_array(
            list_dicom, indir, list_chosen)
        ocr_data = get_text_areas(pixels)
        if is_there_ghost_words(ocr_data):
            fp += 1
        else:
            tn += 1
        save_dicom_info(
            f"{outdir_intermediate}/{os.path.basename(dicom)}_FP_FP_FP.txt",
            file_path, ds, ocr_data, [], 0
        )
        summary += "\n" + file_path + "\n↪parameters : F = - | B = - | S = -"
        nb_images_tested += 1

    return (nb_images_tested, list_chosen, summary, fp, tn)


def get_random_dicom_ds_array(list_dicom, indir, list_chosen):
    """Returns the dataset and the array of a random dicom file in the folder"""
    while True:
        dicom = list_dicom[random.randint(0, len(list_dicom)-1)]
        if dicom not in list_chosen:
            list_chosen.append(dicom)
            break
        else:
            if len(list_chosen) == len(list_dicom):
                break

    file_path = dicom
    (pixels, ds) = dicom2narray(file_path)
    return (pixels, ds, dicom, file_path, list_chosen)


def check_resources(fonts_folder: str, fonts: List[str], size: List[int], blur: List[int]) -> None:
    """Checks if all font resources are existing and correct"""
    for f in fonts:
        if not os.path.isfile(os.path.join(fonts_folder, f)):
            raise TypeError(f"Font {f} does not exist. Please check spelling.")

    if max(size) > 5 or min(size) < 1:
        raise ValueError("Possible text sizes are [1, 2, 3, 4, 5]")

    if max(blur) > 10 or min(blur) < 0:
        raise ValueError("Possible blur strengths are [0..10]")


def save_dicom_info(output_ds, file_path, ds, ocr_data, test_words, total_words):
    """Write OCR test information about the process on a particular dicom"""
    with open(output_ds, 'a', encoding="utf8") as f:
        f.write(
            datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            ) + '\n' + file_path + "\nRecognized words :\n")
        ocr_words = []
        if ocr_data is not None:
            for found in ocr_data:
                if ' ' in found[1]:
                    new_tuple = (found[0], found[1].replace(' ', ''), found[2])
                    ocr_data.remove(found)
                    ocr_data.append(new_tuple)
                ocr_words.append(found[1])
            for found in sorted(ocr_words):
                f.write(found.lower() + " |")
        f.write("\nReal words :\n")

        if total_words == len(test_words):
            for word in sorted(test_words):
                f.write(word + " |")


def generate_random_words(nb_words, nb_character_max, nb_character_min=3):
    """
    Generates 'nb_words' random words composed from 1 to 'nb_character_max' ASCII characters.
    """
    words = []

    for _ in range(nb_words):
        word = string.ascii_letters
        word = ''.join(
            random.choice(word) for i in range(
                random.randint(nb_character_min, nb_character_max)
            )
        )
        words.append(word)

    return words


def add_words_on_image(pixels: np.array, words: List[str], text_size: str,
                       font: str, color: int = 255, blur: int = 0):
    """Writes text on each picture located in the folder path."""
    nb_rows = 15

    # No words = empty array
    if len(words) == 0:
        words_array = words_array = np.full((nb_rows, nb_rows), 0)
        return (pixels, words_array, words)

    # Create a pillow image from the numpy array
    pixels = pixels/255
    im = Image.fromarray(np.uint8((pixels)*255))

    # Auto-scale the size of the text according to the image width
    if text_size == 'auto':
        text_size = auto_scale_font_size(pixels, font, 1)
        print(text_size)
    else:
        text_size = auto_scale_font_size(pixels, font, text_size)
    img_font = ImageFont.truetype(font, text_size)

    # Intialize the information for 'words_array'
    image_width, image_height = pixels.shape[1], pixels.shape[0]
    length_cell, height_cell = image_width/nb_rows, image_height/nb_rows

    # Creates an array of 'nb_rows x nb_rows' filled with 0.
    words_array = words_array = np.full((nb_rows, nb_rows), 0)

    count = 0
    for _ in words:
        # While the cell is occupied by a word or too luminous, we keep looking for anoter free cell
        random_cell, x_cell, y_cell, nb_tries = -1, -1, -1, 0
        is_null = False
        while not is_null:
            random_cell = random.randint(0, words_array.size)

            # Gets the x and the y of the random_cell
            num_cell = 0
            for x in range(nb_rows):
                for y in range(nb_rows):
                    if num_cell == random_cell:
                        x_cell, y_cell = x, y
                    num_cell += 1

            # The array memorizes the position of the word in the list 'words'
            if words_array[x_cell][y_cell] == 0 and x_cell < nb_rows-2 \
                    and is_background_black_enough(
                        x_cell, y_cell, length_cell, height_cell, im):

                occupied = False
                for cell in range(5, 0, -1):
                    if x_cell+cell >= len(words_array):
                        occupied = True
                        break
                    if words_array[x_cell+cell][y_cell] != 0:
                        occupied = True
                        break

                if not occupied:
                    for cell in range(5, 0, -1):
                        words_array[x_cell+cell][y_cell] = count+1
                    is_null = True
                    nb_tries = 0
            nb_tries += 1

            # If the number of tries exceeds the limit, we remove the word from the list
            if nb_tries >= 120:
                break

        if nb_tries < 120:
            # x and y coordinates on the image
            x_cell = x_cell * length_cell
            y_cell = y_cell * height_cell

            # Position of the word on the image
            draw = ImageDraw.Draw(im)

            # Adds the text on the pillow image
            draw.text((x_cell, y_cell),
                      words[count], fill=color, font=img_font)

            # Blur effect
            if blur != 0:
                im = blur_it(im, blur, x_cell, y_cell,
                             length_cell, height_cell)

            count += 1
            del draw

    # Converts the pillow image into a numpy array and returns it
    print("test")
    return (np.array(im), words_array, words)


def auto_scale_font_size(pixels, font, rescale_size):
    """
    Rescale the text depending on the the width of an image.
    Parameters : pixels (narray of the image)
    words : a list of the words to add on the picture
    font : the path of the font to use 
    rescale_size : from 1 to 5 (1 is the smaller size / 5 is the bigger size)
    """
    text_size = 1
    img_font = ImageFont.truetype(font, text_size)

    rescale_sizes = [0.1, 0.2, 0.3, 0.4, 0.5]
    img_fraction = rescale_sizes[rescale_size-1]
    while img_font.getbbox("1234567890")[2] < img_fraction*pixels.shape[1]:
        text_size += 1
        img_font = ImageFont.truetype(font, text_size)
    text_size -= 1

    if text_size < 18:
        text_size = 18

    return text_size


def blur_it(image, blur, x, y, length_cell, height_cell):
    """
    Blur a specified rectangle area on a picture. Parameters :
    Image to blur, strength of the blur effect, x and y of the top-left 
    corner of the area,
    length_cell and height_cell : length and height of the rectangle.  
    """
    box = (int(x), int(y), int(x + 4 * length_cell), int(y + height_cell))
    cut = image.crop(box)
    for _ in range(blur):
        cut = cut.filter(ImageFilter.BLUR)
    image.paste(cut, box)

    return image


def is_background_black_enough(x, y, length, height, im):
    """
    Checks if the area chosen for the text is black enough to set white text on it.
    Returns True if the area is correct. Returns False otherwise.

    Parameters:
    - x: X-coordinate of the chosen area.
    - y: Y-coordinate of the chosen area.
    - length: Length of the chosen area.
    - height: Height of the chosen area.
    - image: Input image.

    Returns:
    - bool: True if the area is black enough, False otherwise.
    """

    if x == -1 and y == -1:
        return False

    x_im = x * length
    y_im = y * height

    box = (x_im, y_im, x_im + length, y_im + height)
    cut = im.crop(box)

    area_array = np.array(cut)
    avg_pixel_value = np.mean(area_array)

    return avg_pixel_value < FONT_COLOR_THRESHOLD


def levenshtein_distance(word_1, word_2):
    """
    Calculates the levenshtein distance (= the number of letters to add/
    substitute/interchange in order to pass from word_1 to word_2)
    """
    array = [[0 for i in range(len(word_2)+1)] for y in range(len(word_1)+1)]

    for i in range(len(word_1)+1):
        array[i][0] = i
    for j in range(len(word_2)+1):
        array[0][j] = j

    for i in range(1, len(word_1)+1):
        for j in range(1, len(word_2)+1):
            cost = 0 if word_1[i-1] == word_2[j-1] else 1
            array[i][j] = min(
                array[i-1][j] + 1,
                array[i][j-1] + 1,
                array[i-1][j-1] + cost
            )

    return array[len(word_1)][len(word_2)]


def is_there_ghost_words(ocr_data):
    """
    Calculates the amount of ghost words on the image.
    Ghost words refers to words or letters recognized by the OCR module 
    where there is actually no word or letter. 
    """
    if ocr_data is not None:
        for _ in ocr_data:
            return True
    return False


def calculate_test_values(
    total_words, ocr_recognized_words,
    tp, tn, fn
):
    """
    Calculates the model test values :
    TP : True Positive  (There are words and every word has been recognized)
    TN : True Negative  (There is no word and no word has been recognized)
    FP : False Positive (There is no word but a word (or more) has been recognized)
    FN : False Negative (There are words and NOT every word has been recognized)
    """

    if total_words == 0:
        tn += 1
    else:
        if ocr_recognized_words/total_words == 1:
            tp += 1
        else:
            fn += 1
    return (tp, tn, fn)


def compare_ocr_data_and_reality(test_words, words_array, ocr_data):
    """
    Calculates the amount of recognized words compared to the total of words on the image
    """
    indices_words_reality = []
    ocr_recognized_words = 0

    test_words = test_words.copy()

    for found in ocr_data:
        if ' ' in found[1]:
            print(found[1])
            new_tuple = (found[0], found[1].replace(' ', ''), found[2])
            ocr_data.remove(found)
            ocr_data.append(new_tuple)
        print(found[1])
    # If the array contains an indice different than 0, we add it to a list.
    indices_words_reality = [
        word for row in words_array for word in row if word != 0]

    # Remove duplicates
    indices_words_reality = list(dict.fromkeys(indices_words_reality))

    # Get the number of words present on the picture
    total_words = 0
    for word in indices_words_reality:
        total_words += 1

    # Set each word to lower case
    test_words = [word.lower() for word in test_words]

    # Get the number of words recognized
    unrecognized_words = []
    for found in ocr_data:
        if found[1].lower() in test_words:
            ocr_recognized_words += 1
            test_words.remove(found[1].lower())
        # The OCR module has a tendency to confuse i and l or o and q. We help it because it does not matter for our work.
        else:
            for i, word in enumerate(test_words):
                difference = levenshtein_distance(
                    found[1].lower(), word)
                if (difference <= 3 and min(len(found[1]), len(word)) > 3) or \
                        (difference <= 1 and min(len(found[1]), len(word)) <= 3):
                    print(found[1].lower(), "&&", word,
                          "==", difference)
                    ocr_recognized_words += 1
                    test_words.remove(word)
                    break
                elif i == len(test_words)-1:
                    if found[1] not in unrecognized_words:
                        unrecognized_words.append(found[1])

    print("Unrecognized :", unrecognized_words)
    if len(unrecognized_words) != 0:
        sum_words = ""
        for word in unrecognized_words:
            sum_words += word
            print(sum_words)
        for word in test_words:
            if sum_words.find(word) != -1:
                ocr_recognized_words += 1
                test_words.remove(word)
                print(word, "is contained in", sum_words)

    return (ocr_recognized_words, total_words)


def save_test_information(nb_images_tested, nb_images_total, sum_ocr_recognized_words, sum_total_words,
                          ocr_recognized_words, total_words, tp, tn, fp, fn, outdir_intermediate, file_path, result):
    """
    Save the test information in a .txt file. 
    It contains main values linked to the past test.
    """
    # Counter Division by zero
    if tp != 0 or fp != 0:
        accuracy = (tp + tn) / (tp + tn + fn + fp)*100
        precision = tp / (tp+fp)
        recall = tp / (tp+fn)
        if precision == 0 and recall == 0:
            f1_score = -1
        else:
            f1_score = (2 * precision * recall) / (precision + recall)
    else:
        accuracy, precision, recall, f1_score = -1, -1, -1, -1

    if total_words != 0:
        percentage_recognized = round(
            (ocr_recognized_words/total_words)*100, 1)
    else:
        percentage_recognized = 100

    if sum_total_words != 0:
        percentage_total_recognized = round(
            (sum_ocr_recognized_words/sum_total_words)*100, 1)
    else:
        percentage_total_recognized = 100

    accuracy, precision = round(accuracy, 1), round(precision, 1)
    recall, f1_score = round(recall, 1), round(f1_score, 1)
    hour = datetime.now().strftime("%H:%M:%S")
    prompt = f"""
\n
================================================================================================
Image :                                                         {file_path}
Image tested at :                                               {hour}
Amount of images tested:                                        {nb_images_tested}/{nb_images_total}
TOTAL:                                                          {ocr_recognized_words}/{total_words} words recognized (last image) ({percentage_recognized}%)
GRAND TOTAL:                                                    {sum_ocr_recognized_words}/{sum_total_words} words recognized ({percentage_total_recognized}%)
True Positive   (IMAGE: x words | OCR : x words):               {tp}
False Negative  (IMAGE: x words | OCR : y words):               {fn}
False Positive  (IMAGE: no words | OCR : detects word(s)):      {fp}
True Negative   (IMAGE: no words | OCR : no words):             {tn}
Precision:                                                      {precision}
Recall:                                                         {recall}
F1_Score:                                                       {f1_score}
Accuracy:                                                       {accuracy} % 
================================================================================================
\n
    """
    print(prompt)
    result += prompt

    if nb_images_tested == nb_images_total:
        filepath = os.path.join(outdir_intermediate, "test_info.log")

        with open(filepath, 'a', encoding="utf8") as f:
            f.write(result)
    else:
        return result


def generate_test_cases(model_input: str, dir_output: str) -> None:
    """Generates 10 different test cases for testing the attribute deid

    -model_input: is a DICOM file used as a base to generate new cases
    -dir_output: is the destination folder where new cases will be generated
    """
    input_file = os.listdir(model_input)
    if len(input_file) > 1 or len(input_file) == 0:
        raise ValueError(
            f"This test only takes 1 file in input, {len(input_file)} were given."
        )
    model_ds = pydicom.dcmread(os.path.join(
        model_input, input_file[0]), force=True)

    test_cases = []
    test_cases.append(gen_ui_case(model_ds.copy()))             # 0
    test_cases.append(gen_sq_case(model_ds.copy()))             # 1
    test_cases.append(gen_dadt_case(model_ds.copy()))           # 2
    test_cases.append(gen_shlo_case(model_ds.copy()))           # 3
    test_cases.append(gen_tm_case(model_ds.copy()))             # 4
    test_cases.append(gen_obuc_case(model_ds.copy()))           # 5
    test_cases.append(gen_other_case(model_ds.copy(), rm_tags))  # 6
    test_cases.append(gen_other_case(model_ds.copy(), kp_tags))  # 7
    test_cases.append(gen_other_case(model_ds.copy(), er_tags))  # 8

    case_number = 0
    for ds in test_cases:
        ds.save_as(os.path.join(dir_output, f"case_{case_number}.dcm"))
        case_number += 1


def gen_ui_case(ds: pydicom.Dataset) -> pydicom.Dataset:
    """Generates a test dataset with critical UI mock values"""
    for tag in ui_tags:
        ds.add_new(tag, 'UI', f"{DICOM_PREFIX_UID}{DICOM_SUFFIX_UID}")
    return ds


def gen_sq_case(ds: pydicom.Dataset) -> pydicom.Dataset:
    """Generates a test dataset with critical SQ mock values"""
    for tag in sq_tags:
        gen_dummy_sequence(ds, tag)
    return ds


def gen_dummy_sequence(ds: pydicom.Dataset, tag: str) -> None:
    """Generates a dummy sequence with 3 attributes"""
    ds.add_new(tag, 'SQ', [])
    ds[tag].value.append(pydicom.Dataset())
    ds[tag].value[0].add_new(
        '0x00080100',
        'SH',
        replace_with_dummy_str('SH')
    )
    ds[tag].value[0].add_new(
        '0x00080102',
        'SH',
        replace_with_dummy_str('SH')
    )
    ds[tag].value[0].add_new(
        '0x00080104',
        'LO',
        replace_with_dummy_str('LO')
    )
    return ds


def gen_obuc_case(ds: pydicom.Dataset) -> pydicom.Dataset:
    """Generates a test dataset with critical OB/UC mock values"""
    ds.add_new(
        '0x00340007',
        'OB',
        base64.b64encode(datetime.strptime(gen_dummy_date(),
                         '%Y%m%d').isoformat().encode('UTF-8'))
    )
    ds.add_new('0x00189367', 'UC', 'I am a personal information')
    for tag in ['0x00340002', '0x00340005']:
        ds.add_new(
            tag,
            'OB',
            base64.b64encode('I am a personal information'.encode('UTF-8'))
        )
    return ds


def gen_tm_case(ds: pydicom.Dataset) -> pydicom.Dataset:
    """Generates a test dataset with critical TM mock values"""
    for tag in tm_tags:
        ds.add_new(tag, 'TM', gen_dummy_hour())
    return ds


def gen_dummy_hour() -> str:
    """Generates a dummy hour formated (HHMMSS)"""
    hh = random.randint(0, 23)
    mm, ss = random.randint(0, 59), random.randint(0, 59)

    def add_zero(x):
        return str(x) if len(str(x)) > 1 else f"0{x}"
    tm = list(map(add_zero, [hh, mm, ss]))
    return f"{tm[0]}{tm[1]}{tm[2]}"


def gen_shlo_case(ds: pydicom.Dataset) -> pydicom.Dataset:
    """Generates a test dataset with critical SH/LO mock values"""
    for tag in shlo_tags:
        ds.add_new(tag, 'SH', replace_with_dummy_str('SH'))
    return ds


def gen_dadt_case(ds: pydicom.Dataset) -> pydicom.Dataset:
    """Generates a test dataset with critical DA/DT mock values"""
    for tag in dadt_tags:
        ds.add_new(tag, 'DA', gen_dummy_date())
    return ds


def gen_dummy_date() -> str:
    offset = random.randint(366, 700)
    d = datetime.strptime('20220101', '%Y%m%d') + timedelta(days=offset)
    return d.strftime('%Y%m%d')


def gen_other_case(ds: pydicom.Dataset, attributes: list) -> pydicom.Dataset:
    """Generates a test dataset with critical mock values to REMOVE"""
    for attr in attributes:
        vr = attr[1]
        if vr in ['DA', 'DT']:
            attrvalue = gen_dummy_date()
        elif vr == 'TM':
            attrvalue = gen_dummy_hour()
        elif vr == 'OB':
            attrvalue = gen_uuid128('')
        elif vr in ['SH', 'LO']:
            attrvalue = replace_with_dummy_str(vr)
        elif vr == 'UI':
            attrvalue = gen_dicom_uid('', '', '')
        elif vr == 'SQ':
            gen_dummy_sequence(ds, attr[0])
        elif vr == 'DS':
            attrvalue = float(random.randint(0, 999))
        elif vr == 'IS':
            attrvalue = random.randint(0, 999)
        elif vr == 'PN':
            attrvalue = "Dr. William MADIE"

        if vr != 'SQ':
            ds.add_new(attr[0], vr, attrvalue)
    return ds


def validate_deid_attributes(output: str) -> None:
    """Checks if the deidentification treats all the required attributes"""
    results = dict.fromkeys(
        ['rm', 'kp', 'er', 'ui', 'tm', 'dadt', 'sq', 'shlo', 'obuc'],
        True
    )

    for file in os.listdir(output):
        ds = pydicom.dcmread(os.path.join(output, file), force=True)
        ds_list = itertools.chain(ds.file_meta, ds)
        ds_tags = []
        tags2keep = list(map(lambda x: format_ds_tag(x[0]), kp_tags))
        tags2rm = list(map(lambda x: x[0], rm_tags))
        tags2er = list(map(lambda x: x[0], er_tags))
        for element in ds_list:
            ds_tags.append(str(element.tag))
            if element.tag in tags2rm:
                results['rm'] = False
            elif element.tag in tags2er and element.value != '':
                elements = str(element.value)

                def is_sq_deid(x):
                    return True if '' in elements else False
                res = list(map(is_sq_deid, elements))
                if False in res:
                    results['er'] = False

            if file == 'case_0.dcm':
                modify_ui(results, ui_tags, element)
            if file == 'case_1.dcm':
                modify_sq(results, sq_tags, element)
            if file == 'case_2.dcm':
                modify_dadt(results, dadt_tags, element)
            if file == 'case_3.dcm':
                modify_shlo(results, shlo_tags, element)
            if file == 'case_4.dcm':
                modify_tm(results, tm_tags, element)
            if file == 'case_5.dcm':
                modify_obuc(results, element)

        if file == 'case_7.dcm':
            modify_kp(results, ds_tags, tags2keep)

    show_results(results)


def modify_obuc(d: dict, element: pydicom.dataelem.DataElement) -> None:
    if element.tag == '0x00340007' and \
            base64.b64decode(element.value).decode('utf-8') != '2022-01-01T00:00:00':
        d['obuc'] = False
    elif element.tag in ['0x00340002', '0x00340005'] and \
        base64.b64decode(element.value).decode('utf-8') \
            == 'I am a personal information':
        d['obuc'] = False
    elif element.tag == '0x00189367' and \
            element.value == 'I am a personal information':
        d['obuc'] = False


def modify_shlo(results: dict, tags: list, element: pydicom.dataelem.DataElement) -> None:
    if element.tag in tags and len(element.value) not in [16, 64]:
        results['shlo'] = False


def modify_ui(results: dict, tags: list, element: pydicom.dataelem.DataElement) -> None:
    if element.tag in tags and len(element.value) != 57:
        results['ui'] = False


def modify_dadt(results: dict, tags: list, element: pydicom.dataelem.DataElement) -> None:
    if element.tag in tags and element.value[:4] == '2022':
        results['dadt'] = False


def modify_tm(results: dict, tags: list, element: pydicom.dataelem.DataElement) -> None:
    if element.tag in tags and element.value != '000000':
        print(element.tag, element.VR, element.value)
        results['tm'] = False


def modify_kp(results: dict, ds_tags: list, tags2keep: list) -> None:
    for tag in tags2keep:
        if tag in ds_tags and not set(tags2keep).issubset(set(ds_tags)):
            results['kp'] = False


def modify_sq(results: dict, seq_tags: list, element: pydicom.dataelem.DataElement) -> None:
    if format_ds_tag(str(element.tag)) in seq_tags:
        for ds in element.value:
            for subelement in ds:
                if subelement.tag == '0x00080102' and subelement.value != '':
                    results['sq'] = False
                elif subelement.tag == '0x00080100' and subelement.value != '':
                    if len(subelement.value) != 16:
                        results['sq'] = False


def show_results(results: dict) -> None:
    for k, v in results.items():
        k = k.upper()
        result = f"Test {k}: Passed" if v else f"Test {k}: Not Passed"
        print(result)


def run_test_deid_attributes(indir, outdir):
    tmp = os.path.join(outdir, 'intermediate')
    tmp_ds = os.path.join(outdir, 'ds')
    final_ds = os.path.join(outdir, 'final_ds')
    final = os.path.join(outdir, 'final')

    for folder in [tmp, tmp_ds, final_ds, final]:
        try:
            os.mkdir(folder)
        except FileExistsError:
            pass

    generate_test_cases(indir, tmp)
    write_all_ds(tmp, tmp_ds, True)
    df = deidentify_attributes(tmp, final, org_root=SAMPLE_ORG_ROOT)
    df2dicom(df, final, test=True)
    write_all_ds(final, final_ds, True)
    validate_deid_attributes(final)


if __name__ == "__main__":
    IMG_DIR = os.path.join('images', 'deid', 'test_deid_2')
    INPUT = os.path.join(IMG_DIR, 'input')
    INTERMEDIATE = os.path.join(IMG_DIR, 'intermediate')
    INTERMEDIATE4DS = os.path.join(IMG_DIR, 'ds')
    OUTPUT = os.path.join(IMG_DIR, 'output')
    OUTPUT4DS = os.path.join(IMG_DIR, 'final_ds')
    generate_test_cases(INPUT, INTERMEDIATE)
    write_all_ds(INTERMEDIATE, INTERMEDIATE4DS, True)
    deidentify_attributes(INTERMEDIATE, OUTPUT, OUTPUT4DS)
    df2dicom(INPUT, OUTPUT)
    validate_deid_attributes(OUTPUT)
