from pydicom.dataset import Dataset
from collections import Counter
from datetime import datetime
from typing import Union
import os
import sys
import pydicom
from PIL import Image


def write_all_ds(indir: str, outdir: str, silent: bool = False) -> None:
    """Writes the ds of all the dicom in a folder"""
    nb_files = len(os.listdir(indir))
    counter = 0
    for _ in map(lambda x: write1ds(os.path.join(indir, x), outdir), os.listdir(indir)):
        counter += 1
    if not silent:
        print(f"{counter} / {nb_files} datasets have been written")


def write1ds(file: str, outdir: str) -> None:
    """Writes the ds of a given dicom file"""
    ds = pydicom.dcmread(file)
    with open(os.path.join(outdir, f"{os.path.basename(file)[:-4]}.txt"), 'w') as f:
        f.write(str(ds))


def format_ds_tag(tag: str) -> str:
    """format a tag from (XXXX, YYYY) to 0xXXXXYYYY or vice versa"""
    if tag.startswith('0x'):
        return f"({tag[2:6]}, {tag[6:10]})"
    else:
        return "0x" + "".join(filter(str.isdigit, tag[1:-1]))


def show_series(indir: str, tag: str) -> None:
    """
    Takes a directory full of dicom files and shows which one belongs to
    the same series 
    """
    series = []
    files = {}
    for file in os.listdir(indir):
        ds = pydicom.dcmread(os.path.join(indir, file))
        for element in ds:
            if element.tag == tag:
                series.append(element.value)
                try:
                    files[element.value].append(file)
                except Exception:
                    files[element.value] = [file]

    for key, value in dict(Counter(series)).items():
        print(f"{key} appears {value} time(s)")
        if value == 1:
            print(f"[{files[key][0]}]\n")
            files.pop(key)
        else:
            result = ""
            for i in range(4):
                result += f"[{files[key][i]}]"
            print("[", result, "]\n")
    print(f"total : {len(series)}")


def d() -> str:
    now = datetime.now().strftime('%m-%d-%Y %H:%M:%S')
    return f'{now}'


def log(txt: Union[str, list], logtype: int = 0) -> None:
    if logtype == 1:
        logtype = ' (WARNING) '
    elif logtype == 2:
        logtype = ' (ERROR) '
    else:
        logtype = ' '
    if type(txt) == str:
        print(f'{d()}{logtype}{txt}')
    else:
        def f(x): return print(f'{d()}{logtype}{x}')
        list(map(f, txt))
    sys.stdout.flush()


def reduce_PIL_img_size(im: Image, reduce_factor: int, verbose: bool) -> Image:
    """Reduce the size of an image by dividing with the given factor"""
    width, height = im.size
    print(f"Size before reducing: {im.size}") if verbose else None
    im.thumbnail((width/reduce_factor, height/reduce_factor),
                 Image.Resampling.LANCZOS)
    print(f"Size after reducing: {im.size}") if verbose else None
    return im


def compare_dicom_datasets(ds1: Dataset, ds2: Dataset) -> bool:
    # Check if both datasets have the same number of elements
    if len(ds1) != len(ds2):
        return False
    # Iterate over all elements in the first dataset
    for elem in ds1:
        tag = elem.tag
        # Check if the tag exists in the second dataset
        if tag not in ds2:
            print(f"Tag {tag} not found in second dataset.")
            return False
        # Check if the values are equal
        value1 = elem.value
        value2 = ds2[tag].value
        if isinstance(value1, Dataset) and isinstance(value2, Dataset):
            # Recursively compare nested datasets
            if not compare_dicom_datasets(value1, value2):
                return False
        elif value1 != value2:
            print(f"Values for tag {tag} do not match: {value1} != {value2}")
            return False
    return True
