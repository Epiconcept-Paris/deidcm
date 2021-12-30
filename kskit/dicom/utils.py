from collections import Counter
import os
import pydicom

def write_all_ds(indir: str, outdir: str, silent: bool=False) -> None:
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
    with open(os.path.join(outdir, f"{os.path.basename(file)[:-4]}.txt"),'w') as f:
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


if __name__ == '__main__':
    print(format_ds_tag('0x00080033'))