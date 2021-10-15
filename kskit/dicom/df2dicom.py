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
    build_dicom(df, index, parent_path = '')
  
  """
  dico = dataframe.to_dict()
  print(dico)
  exit(1)
  build_dicoms(dico)
  """



"""
def get_ds_attr(df, parent_path, attr):
  #filtrer noms colonnes commençant par parent_path et attr
  #extraire le numéro @i. et enlever les doublons
  

def build_seq(df, index, parent_path, seq_attr):
  seq = Sequence()
  for ds_attr in get_ds_attr(df, parent_path, seq_attr):
    seq.append(build_dicom(df, index, parent_path+seq_attr+ds_attr@.))
"""

def getSeq_attr(attrs):
  nom_seq = set([attr.split('@')[0] for attr in attrs]) #extract the part before the @
  return list(nom_seq)    #keep only unique values
  

def getValue(df, index, parent_path, child_path):
  print(df[parent_path+child_path][index])
  return df[parent_path+child_path][index]


def getVR(column_name):
  """Returns the type as it is defined in the pydicom definition"""
  return pydicom.sequence.Sequence if 'SQ' in column_name else '' 


def build_dicom(df, index, parent_path = ''):
  seq_attrs, nonseq_attrs = [], []
  child_attr = [col for col in df.columns if col.startswith(parent_path)] #noms de toutes les colonnes commençant par parent_path en retirant le parent_path (startsWith)
  [seq_attrs.append(attr) if getVR(attr) == pydicom.sequence.Sequence else nonseq_attrs.append(attr) for attr in child_attr ] #filtrer child_attr pour ceux qui getVR(child)!= pydicom.sequence.Sequence
  ds = Dataset()
  
  for attr in nonseq_attrs:
    if not pd.isna(getValue(df, index, parent_path, attr)):
      try:
        ds.add_new(attr.split('_')[1], attr.split('_')[2], getValue(df, index, parent_path, attr))
      except ValueError:
            #If the value is a multival (= list of values), it needs to be removed
            #from the string and properly cast as a multivalue compatible type
            ds.add_new(attr.split('_')[1], attr.split('_')[2], ast.literal_eval(getValue(df, index, parent_path, attr)))
  
  for attr in getSeq_attr(seq_attrs):
    #getHex(attr) ?
    ds.add_new(attr.split('_')[1], attr.split('_')[2], build_seq(df, index, parent_path, attr))
  
  return ds
  


def encode_unit(value, VR):
  if VR == 'OB':
    return base64.b64decode(value.encode("UTF-8"))
  else:
    return value;

