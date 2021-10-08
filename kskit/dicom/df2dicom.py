import os
from numpy import dot, e, ndarray
import pydicom
from pydicom.sequence import Sequence
from matplotlib import pyplot
import base64
import pandas as pd
import json
import ast

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


def df2dicom(dataframe, outdir):
  """
  Fill up a directory with DICOMs initially contained in a dataframe
  @param dataframe : data structure containing the information needed to
  reconstruct DICOMs
  @param outdir : output directory where the DICOMs will be generated
  """
  dico = dataframe.to_dict()
  build_dicoms(dico)


def build_dicoms(dico):
  """
  Gets all the attributes names and values and call for the build of each
  dicom.
  dico is the initial dataframe but cast in a dictionary type
  """
  attributes_names , attributes_values = [], []

  for element in dico:
    element_info = element.split("_")
    infos = {}
   
    for i in range(len(element_info)):
      infos[i] = element_info[i]
    
    attributes_names.append(infos)
    attributes_values.append(list(dico[element].values()))
  
  #TODO : create a loop that build the dicom from 0 to n
  no_dicom = 1
  ds = build_dicom(no_dicom, attributes_names, attributes_values)
  print(ds)


def build_dicom(no_dicom, attr_names, attr_values):
  """
  Builds a single DICOM's dataset and returns it.
  @param no_dicom : index of the dicom to build
  @param attr_names : list of dictionaries containing element info
  @param attr_values : list of lists containing values for each element of all the DICOMs
  """
  ds = pydicom.Dataset()

  for i in range(len(attr_names)):
    name = attr_names[i]
    print(name[1], name[2], attr_values[i][no_dicom])
    
    
    if (name[2] != 'SQ'):
      try:
        ds.add_new(name[1], name[2], attr_values[i][no_dicom])
      except ValueError:
        #If the value is a multival (= list of values), it needs to be removed
        #from the string and properly cast as a multivalue compatible type
        ds.add_new(name[1], name[2], ast.literal_eval(attr_values[i][no_dicom]))
        
     
      
    else:
      seq = build_sequence(no_dicom, attr_names, attr_values, i)
      beam = pydicom.Dataset()
      beam.BlockName = name[2]
      ds.BeamSequence = Sequence([beam])
      ds.BeamSequence[0].BlockSequence = Sequence(seq)
      ds.BeamSequence[0].NumberOfBlocks = len(seq)
      
      """
      TODO : CONTINUE TO BUILD SEQUENCE
      - find how to name the sequence with the correct element (tag and name)
      - check why build_sequence() didn't build the full sequence in the test (it built only one Data Element)
      - try to make build_sequence() for one layer (= one level)
      """
    i += 1
  return ds


def build_sequence(no_dicom, attr_names, attr_values, i, nb_previous_parents = 0):
  sequence = []
  ds = pydicom.Dataset()
  name = attr_names[i]
  print(name)
  nb_levels = -1
  levels = []
  for key, value in name.items():
    if '0x' in value:
      nb_levels += 1
      levels.append((key, value))
  print(nb_levels)
  print("Levels :", levels)
  
  nb_treated_levels = 1
  level = levels[len(levels)-1-nb_treated_levels][1]
  ind_level = levels[len(levels)-1-nb_treated_levels][0]

  for i in range(i, len(attr_names)):
    if nb_treated_levels == len(levels):
      return ds
    else:
      ds.add_new(name[ind_level+6], name[ind_level+6], attr_values[i][no_dicom])
  sequence.append(ds)
  return sequence


def encode_unit(value):
  t = type(value)
  if t == int:
    return str(value)
  elif t == str: 
    return value
  elif t == bytes: 
    return base64.b64encode(value).decode("UTF-8")
  elif t == pydicom.uid.UID:
    return str(value)
  elif t == pydicom.valuerep.DSfloat:
    return str(value)
  elif t == pydicom.valuerep.IS:
    return str(value)
  elif t == pydicom.valuerep.DT:
    return str(value.timestamp())
  elif t ==  pydicom.valuerep.PersonName:
    return str(value.timestamp())
  elif t == list and len(value)==0:
    return '[]'
  else:
    raise ValueError("cannot encode {t} as unit")

