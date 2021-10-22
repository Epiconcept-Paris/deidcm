import dicom2df
import df2dicom
import os
import pydicom
import difflib

def prepare_dicom():
    #DICOM without transformation excluding removal of the attribute Pixel Data
    directory = "/home/williammadie/images/deid/dicom2df_test/other"
    dataset1 = [pydicom.dcmread(os.path.join(directory, file), force=True) for file in os.listdir(directory)]
    
    #DICOM with 2 transformations : dicom2df and df2dicom
    df = dicom2df.dicom2df(directory, with_private = False, with_pixels = True, with_seqs = True)
    df2dicom.df2dicom(df, "/home/williammadie/images/deid/df2dicom_test")
    
    dataset2 = [pydicom.dcmread(os.path.join("/home/williammadie/images/deid/df2dicom_test", file), force=True) for file in os.listdir("/home/williammadie/images/deid/df2dicom_test")]
    
    dataset1.extend(dataset2)
    # difflib compare functions require a list of lines, each terminated with
    # newline character massage the string representation of each dicom dataset
    # into this form:
    rep = []
    for ds in dataset1:
        lines = str(ds).split("\n")
        lines = [line + "\n" for line in lines] #add the newline to the end
        rep.append(lines)
    return rep


def test_comparison_btw_2_dicoms():
    diff = difflib.Differ()
    rep = prepare_dicom()
    for line in diff.compare(rep[0], rep[1]):
        print(line)
        if line[0] != "?":
            print(line)
    
if __name__ == "__main__":
    test_comparison_btw_2_dicoms()
