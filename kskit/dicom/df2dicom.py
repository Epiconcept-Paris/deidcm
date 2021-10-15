import os
from numpy import dot, e, ndarray
from numpy.lib.function_base import append
import pydicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from matplotlib import pyplot
import base64
import pandas as pd
import json
import ast
import time

from pydicom import tag

def write_dicom(infiles):
  i = 0
  for infile in infiles:
    outfile = f"/home/fod/deleteme/dicom_{i}.png"
    ds = dcmread(infile)
    pixels = ds.pixel_array
    pyplot.imsave(outfile, pixels, cmap=pyplot.cm.bone)
    print(f"file {outfile} written")
    i = i +1

def read_dicom(infiles):
  for infile in infiles:
    ds = dcmread(infile)
    yield((infile, ds) )


def df2dicom(df, outdir):
  """
  Fill up a directory with DICOMs initially contained in a dataframe
  @param dataframe : data structure containing the information needed to
  reconstruct DICOMs
  @param outdir : output directory where the DICOMs will be generated
  """

  for index in range(len(df)):
    ds = build_dicom(df, index, parent_path = '')
    print(ds)
    print("\n\n\n")
  


def get_ds_attr(df, parent_path, attr):
  """Gets and returns a list of distinct @i extracted from the elements in the sequence"""
  #filters the columns names starting with parent_path and attr
  child_attr = [col.replace(parent_path + attr, '') for col in df.columns if col.startswith(parent_path + attr)] 
  #extract @i. and remove duplicates from the list
  child_attr = list(set([attr[:3] for attr in child_attr]))
  child_attr.sort()
  return child_attr
  
  
def build_seq(df, index, parent_path, seq_attr):
  seq = Sequence()
  
  for ds_attr in get_ds_attr(df, parent_path, seq_attr):
    seq.append(build_dicom(df, index, parent_path+seq_attr+ds_attr))
  return seq


def getSeq_attr(attrs):
  """Get and return a list of unique names of the sequence attributes without the @child_attribute"""
  nom_seq = set([attr.split('@')[0] for attr in attrs]) #extract the part before the @
  return list(nom_seq)    #keep only unique values
  

def getValue(df, index, parent_path, child_path):
  return df[parent_path+child_path][index]


def getVR(column_name):
  """Returns the type as it is defined in the pydicom definition"""
  return pydicom.sequence.Sequence if 'SQ' in column_name else '' 


def build_dicom(df, index, parent_path = ''):
  seq_attrs, nonseq_attrs = [], []
  child_attr = [col.replace(parent_path, '') for col in df.columns if col.startswith(parent_path)] #name of the column without the parent name
  #filters child_attr into two lists (sequences and not sequences)
  [seq_attrs.append(attr) if getVR(attr) == pydicom.sequence.Sequence else nonseq_attrs.append(attr) for attr in child_attr] 
  ds = Dataset()
  
  #NON-SEQUENCE ATTRIBUTES
  for attr in nonseq_attrs:
    if not pd.isna(getValue(df, index, parent_path, attr)):
      try:
        ds.add_new(attr.split('_')[1], attr.split('_')[2], getValue(df, index, parent_path, attr))
      except ValueError:
            #If the value is a multival (= list of values), it needs to be removed
            #from the string and properly cast as a multivalue compatible type
            ds.add_new(attr.split('_')[1], attr.split('_')[2], ast.literal_eval(getValue(df, index, parent_path, attr)))

  #SEQUENCE ATTRIBUTES
  for attr in getSeq_attr(seq_attrs):
    #If the sequence is present in the DICOM, test_sequence would take a value != NaN
    for test in child_attr:
      if attr in test:
        test_sequence = test
    
    #If test_sequence == NaN, the sequence does not appear in this DICOM.
    if not pd.isna(getValue(df, index, parent_path, test_sequence)):
      seq = build_seq(df, index, parent_path, attr)
      #If the sequence is not empty then we add the sequence to the ds
      if seq:
        ds.add_new(attr.split('_')[1], attr.split('_')[2], seq)
  return ds
  

def encode_unit(value, VR):
  if VR == 'OB':
    return base64.b64decode(value.encode("UTF-8"))
  else:
    return value;

