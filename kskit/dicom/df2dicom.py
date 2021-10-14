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
  debug_list = []
  ds = pydicom.Dataset()
  nb_sequences = 0
  i = 0
  while i < len(attr_names):
    print("i réel : ", i)
    name = attr_names[i]

    #debug
    if name[1] in debug_list:
      print(name[1], name[2], name[0], attr_values[i][no_dicom])
      print("Déjà ajouté !")
      exit(1)

    print(name[1], name[2], name[0], attr_values[i][no_dicom])
    
    
    if (name[2] != 'SQ'):
      value = encode_unit(attr_values[i][no_dicom], name[2])
      try:
        ds.add_new(name[1], name[2], value)
      except ValueError:
        #If the value is a multival (= list of values), it needs to be removed
        #from the string and properly cast as a multivalue compatible type
        ds.add_new(name[1], name[2], ast.literal_eval(value))
      debug_list.append(name[1])
      i += 1

    else:
      nb_sequences += 1
      print(attr_values[i])
      (seq, l) = build_sequence(no_dicom, attr_names, attr_values, i)
      print(i, no_dicom)
      
      ds.add_new(name[1], name[2], Sequence(seq))
      ds.add_new("Columns", "US", 128)
      #with open("/home/williammadie/images/deid/df2dicom_test/ds.txt", "a") as f:
      #  f.write(f"\n\n\n\n{ds}\n\n\n\n")
      debug_list.append(name[1])
      i += (l-2)
      print("attr suivant : ", attr_names[i][1], attr_names[i][2], attr_names[i][0], attr_values[i][no_dicom])
      print("i suivant : ", i)
    
      """
      TODO : CONTINUE TO BUILD SEQUENCE
      - find how to name the sequence with the correct element (tag and name)
      - check why build_sequence() didn't build the full sequence in the test (it built only one Data Element)
      - try to make build_sequence() for one layer (= one level)
      """
   
  print(f"NB_SEQUENCE ====> {nb_sequences}")
  return ds



def build_sequence(no_dicom, attr_names, attr_values, i, nb_previous_parents = 0):
  #The sequence is a list of datasets
  sequence = []
  name = attr_names[i]
  """
  TODO: remove debug
  for i in range(i, i+30):
    print(attr_names[i])
  """
  
  #Determines the number of levels for recursive search of data elements
  nb_levels = -1
  #Levels is a list which contains tuples like (dic_key_tag_attr, tag_attr)
  #dic_key_tag_attr is the key associated to the tag_attr in the dic attr_names
  levels = []
  #Finds all the tag_attr in the name. If there are n tag_attr, then there are
  #n-1 levels
  for key, value in name.items():
    if '0x' in value:
      nb_levels += 1
      levels.append((key, value))
    if '@' in value:
      ind_in_sequence = int(value[1])
  #print("IND_IN_SEQ = ", ind_in_sequence)   
  print(nb_levels)
  #print("Levels :", levels)
  if nb_levels > 2:
    print("récursion requise")
    exit(1)
  nb_treated_levels = 1
  parent_tag = levels[len(levels)-1-nb_treated_levels][1]
  ind_level = levels[len(levels)-1-nb_treated_levels][0]

  #Browse through the list of attr_names of all dicom from the current attr
  #until it meets a new sequence or the current sequence ends
  ds = pydicom.Dataset()
  l = 1
  for i in range(i, len(attr_names)):
    name = attr_names[i]
    #print(f"Tour n°{l}\n")
    #print(attr_names[i])
    l += 1
    print(f"CHECK {attr_names[i][1]} <=> {parent_tag}")
    if attr_names[i][1] != parent_tag:
      print("Sequence suivante !")
      break
      
    for attribute in attr_names[i].values():
      if '@' in attribute:
        #print(attribute)
        current_ind_in_sequence = int(attribute[1])
    
    if current_ind_in_sequence != ind_in_sequence:
      #print(f"Fin de dataset {current_ind_in_sequence} != {ind_in_sequence}")
      #print("DS :\n", ds)
      sequence.append(ds)
      ds = pydicom.Dataset()
      ind_in_sequence += 1

    if nb_treated_levels == len(levels):
      break
    else:
      #print(i, no_dicom)
      print(name)
      print(name[ind_level+6], name[ind_level+6], attr_values[i][no_dicom])
      ds.add_new(name[ind_level+6], name[ind_level+6], attr_values[i][no_dicom])

  sequence.append(ds)
  return (sequence, l)



def encode_unit(value, VR):
  if VR == 'OB':
    return base64.b64decode(value.encode("UTF-8"))
  else:
    return value;

