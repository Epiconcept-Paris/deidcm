import dicom2df
import df2dicom
import os
import pydicom
import difflib

def get_ds_lines(ds_list):
    # difflib compare functions require a list of lines, each terminated with
    # newline character massage the string representation of each dicom dataset
    # into this form:
    rep = []
    for ds in ds_list:
        lines = str(ds).split("\n")
        lines = [line + "\n" for line in lines] #add the newline to the end
        rep.append(lines)
    return rep

def prepare_dicom():
    #DICOM without transformation excluding removal of the attribute Pixel Data
    dir_initial_dcm = os.path.join('/', 'home', 'williammadie', 'images', 'deid', 'dicom2df_test', 'other')
    dir_modified_dcm = os.path.join('/', 'home', 'williammadie', 'images', 'deid', 'df2dicom_test')
    initial_ds = [pydicom.dcmread(os.path.join(dir_initial_dcm, file), force=True) for file in os.listdir(dir_initial_dcm)]
    
    #DICOM with 2 transformations : dicom2df and df2dicom
    
    modified_ds = os.listdir(dir_modified_dcm)
    if len(modified_ds) != 0:
        print(os.path.join(dir_modified_dcm, 'coucou'))
        [os.remove(os.path.join(dir_modified_dcm, file)) for file in modified_ds]

    df = dicom2df.dicom2df(dir_initial_dcm, with_private = True, with_pixels = True, with_seqs = True)
    df2dicom.df2dicom(df, dir_modified_dcm)
    
    modified_ds = [pydicom.dcmread(os.path.join(dir_modified_dcm, file), force=True) for file in os.listdir("/home/williammadie/images/deid/df2dicom_test")]
    print(initial_ds)
    print(modified_ds)
    
    #inital_ds.extend(modified_ds)
    initial_dicoms, modified_dicoms = get_ds_lines(initial_ds), get_ds_lines(modified_ds)
    initial_dicoms.sort()
    modified_dicoms.sort()
    return initial_dicoms, modified_dicoms

    

def test_comparison_btw_2_dicoms():
    diff = difflib.Differ()
    initial_dicoms, modified_dicoms = prepare_dicom()
    nb_diff = 0
    print(initial_dicoms)

    for dicom_i in range(len(initial_dicoms)):
        for line in diff.compare(initial_dicoms[dicom_i], modified_dicoms[dicom_i]):
            print(line)
            
            if line[0] != "?":
                print(line)
            
            if line[0] in ['?', '+', '-']:
                nb_diff += 1
        print(f"\n{nb_diff} differences / {len(initial_dicoms)} tested images\n")
        if nb_diff != 0:
            exit()
        
    
if __name__ == "__main__":
    test_comparison_btw_2_dicoms()
