import pydicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
import base64
import pandas as pd
import json

def df2dicom(df, outdir):
  """
  Fill up a directory with DICOMs initially contained in a dataframe
  @param dataframe : data structure containing the information needed to
  reconstruct DICOMs
  @param outdir : output directory where the DICOMs will be generated
  """

  nb_file = 0
  for index in range(len(df)):
    #print(f"dicom n°{nb_file} has been rebuilt")
    ds = build_dicom(df, index, parent_path = '')
    ds.save_as(f"{outdir}/dicom_{nb_file}.dcm", write_like_original=False)
    nb_file += 1


def get_ds_attr(df, parent_path, attr):
  """Gets and returns a list of distinct @i extracted from the elements in the sequence"""
  #filters the columns names starting with parent_path and attr
  child_attr = [col.replace(parent_path + attr, '') for col in df.columns if col.startswith(parent_path + attr)] 
  #extract @i. and remove duplicates from the list
  child_attr = list(set([attr[:3] for attr in child_attr]))
  child_attr.sort()
  return child_attr
  
  
def build_seq(df, index, parent_path, seq_attr):
  """
  Builds and returns a pydicom sequence and : 0 for a basic sequence | 1 for an
  empty sequence that needs to be represented even if it is empty.
  """
  seq = Sequence()
  
  for ds_attr in get_ds_attr(df, parent_path, seq_attr):
    ds = build_dicom(df, index, parent_path+seq_attr+ds_attr)
    if ds != None:
      seq.append(ds)
    else:
      return [], 1
  return seq, 0


def getSeq_attr(attrs):
  """Gets and returns a list of unique names of the sequence attributes without the @child_attribute"""
  nom_seq = set([attr.split('@')[0] for attr in attrs]) #extract the part before the @
  return list(nom_seq)    #keep only unique values
  

def getValue(df, index, parent_path, child_path):
  """Gets and returns the value of a given attribute name"""
  return df[parent_path+child_path][index]


def getVR(column_name):
  """Returns the type as it is defined in the pydicom definition"""
  return pydicom.sequence.Sequence if 'SQ' in column_name else '' 


def add_file_meta(df, ds, meta_attrs, index, parent_path):
  """Creates and returns a dataset containing the meta-information of the dicom file"""
  ds.file_meta = Dataset()
  for attr in meta_attrs:
    if not pd.isna(getValue(df, index, parent_path, attr)):
      attr_tag, attr_VR, attr_VM = attr.split('_')[1], attr.split('_')[2], attr.split('_')[3]
      attr_value = decode_unit(getValue(df, index, parent_path, attr), attr_VR, attr_VM)
      ds.file_meta.add_new(attr_tag, attr_VR, attr_value)

      #Fills 2 ds.properties needed in order to save the dicom file
      if '0x00020010' in attr_tag:
        if '1.2.840.10008.1.2.1' in attr_value:
          ds.is_little_endian, ds.is_implicit_VR = True, False       
        elif ('1.2.840.10008.1.2.2' in attr_value) or ('1.2.840.10008.1.2.99' in attr_value):
          ds.is_little_endian, ds.is_implicit_VR = False, False       
        else:
          ds.is_little_endian, ds.is_implicit_VR = True, True    
  return ds


def build_dicom(df, index, parent_path = ''):
  """Builds one DICOM file from the dataframe information"""
  seq_attrs, nonseq_attrs, meta_attrs = [], [], []
  child_attr = [col.replace(parent_path, '') for col in df.columns if col.startswith(parent_path)] #name of the column without the parent name
  #filters child_attr into two lists (sequences and not sequences)
  [seq_attrs.append(attr) if getVR(attr) == pydicom.sequence.Sequence else nonseq_attrs.append(attr) for attr in child_attr] 

  ds = Dataset()

  #NON-SEQUENCE ATTRIBUTES
  for attr in nonseq_attrs:
    if not pd.isna(getValue(df, index, parent_path, attr)):
      if attr != 'empty':
        attr_tag, attr_VR, attr_VM = attr.split('_')[1], attr.split('_')[2], attr.split('_')[3]
        if '0x0002' in attr_tag:
          meta_attrs.append(attr)
        else:
          ds.add_new(attr_tag, attr_VR, decode_unit(getValue(df, index, parent_path, attr), attr_VR, attr_VM))
      else:
        return None
        
  #SEQUENCE ATTRIBUTES
  for attr in getSeq_attr(seq_attrs):
    #If the sequence is present in the DICOM, test_sequence would take a value != NaN
    for test in child_attr:
      if attr in test:
        test_sequence = test
    
    #If test_sequence == NaN, the sequence does not appear in this DICOM.
    if not pd.isna(getValue(df, index, parent_path, test_sequence)):
      seq, empty_but_present = build_seq(df, index, parent_path, attr)
      
      if not empty_but_present:
        #If the sequence is not empty then we add the sequence to the ds
        if seq:
          ds.add_new(attr.split('_')[1], attr.split('_')[2], seq)
      #create an empty sequence (if the initial dicom had an empty sequence it has
      #to rebuild it
      else:
        ds.add_new(attr.split('_')[1], attr.split('_')[2], None)
        
  #META-FILE ATTRIBUTES
  ds = add_file_meta(df, ds, meta_attrs, index, parent_path)
  return ds
  

def decode_unit(value, VR, VM):
  #if the value is None : no need to decode
  if value == str(None):
    return None
  else:
    integer_types = ['IS','SS','SL','US','UL']
    known_encodings = ['CS', 'DS', 'FD', 'UN']
    if VM != '1':
      if (VR in integer_types or VR in known_encodings) and VM != '0':
        return [decode_unit(e, VR, '1') for e in json.loads(value)]
    else:
      if VR == 'OB' or VR == 'OW' or VR == 'UN':
        return value.encode('utf8')
      elif VR in integer_types:
        return int(value)
      elif VR == 'FD':
        return float(value)
    return value
