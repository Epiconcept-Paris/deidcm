import os
import pydicom
import difflib
from .dicom.df2dicom import df2dicom
from .dicom.dicom2df import dicom2df

def get_ds_lines(ds_list):
    """
    Takes a list of datasets and returns a list of list of lines (yes, you read
    correctly).
    """
    # difflib compare functions require a list of lines, each terminated with
    # newline character massage the string representation of each dicom dataset
    # into this form:
    rep = []
    for ds in ds_list:
        lines = str(ds).split("\n")
        lines = [line + "\n" for line in lines] #add the newline to the end
        rep.append(lines)
    return rep


def prepare_dicom(indir, tmp_dir):
    """
    Create two lists containing lists of lines. The first list contains all the lines
    from the datasets of the initial dicoms. The second list contains all the lines
    from the datasets of the rebuild dicoms. 
    @indir: directory where are located the dicoms
    @tmp_dir: directory where the rebuild dicoms will be placed 
    """
    #DICOM without transformation excluding removal of the attribute Pixel Data
    initial_ds = [pydicom.dcmread(os.path.join(indir, file), force=True) for file in os.listdir(indir)]
    
    #DICOM with 2 transformations : dicom2df and df2dicom
    df = dicom2df(indir, with_private = True, with_pixels = False, with_seqs = True)
    df2dicom(df, tmp_dir, False)
    
    modified_ds = [pydicom.dcmread(os.path.join(tmp_dir, file), force=True) for file in os.listdir(tmp_dir)]
    
    #inital_ds.extend(modified_ds)
    initial_dicoms, modified_dicoms = get_ds_lines(initial_ds), get_ds_lines(modified_ds)
    initial_dicoms.sort()
    modified_dicoms.sort()
    return initial_dicoms, modified_dicoms


def cleandir(dir2clean, rmdir = False):
    """Remove a directory full of files"""
    files = os.listdir(dir2clean)
    if len(files) != 0:
        [os.remove(os.path.join(dir2clean, file)) for file in files]
    os.rmdir(dir2clean) if rmdir else None 


def df2dicom_test(indir, tmp_dir):
    """
    Compare rebuild dicoms with their original version. Param :
    @indir : directory where are located the dicoms
    @tmp_dir : directory where the rebuild dicoms will be placed 
    (PLEASE, NOTE THAT ALL FILES IN tmp_dir WILL BE ERASED AT EVERY LAUNCH)
    """
   
    if not os.path.isdir(indir): raise FileNotFoundError 
    #Creates or cleans the tmp_dir
    os.makedirs(tmp_dir) if not os.path.isdir(tmp_dir) else cleandir(tmp_dir, False)

    diff = difflib.Differ()
    initial_dicoms, modified_dicoms = prepare_dicom(indir, tmp_dir)
    nb_diff = 0

    for dicom_i in range(len(initial_dicoms)):
        for line in diff.compare(initial_dicoms[dicom_i], modified_dicoms[dicom_i]):
            print(line)
            nb_diff = nb_diff + 1 if line[0] in ['?', '+', '-'] else nb_diff
                
        print(f"\n{nb_diff} difference(s) / {dicom_i+1} tested images\n")
    cleandir(tmp_dir, False)


if __name__ == "__main__":
    dir_initial_dcm = os.path.join('images', 'deid', 'mg_dcm4build_tests', 'usable')
    dir_modified_dcm = os.path.join('images', 'deid', 'df2dicom_test')
    df2dicom_test(dir_initial_dcm, dir_modified_dcm)
