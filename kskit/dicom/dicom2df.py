import os
import pydicom
from matplotlib import pyplot
import base64
import pandas as pd
import json
import itertools


def write_dicom(infiles):
  i = 0
  for infile in infiles:
    outfile = f"/home/fod/deleteme/dicom_{i}.png"
    ds = dcmread(infile)
    pixels = ds.pixel_array
    pyplot.imsave(outfile, pixels, cmap=pyplot.cm.bone)
    print(f"file {outfile} written")
    i = i +1

def dicom2df(search_dir, with_private = False, with_pixels = False, with_seqs = True):
  files = search_dicom(search_dir)
  dicos = map(
    lambda f: flat_dicom(f, with_private = with_private, with_pixels = with_pixels, with_seqs = with_seqs),
    files
  )
  return pd.DataFrame(dicos)

def search_dicom(search_dir) :
  for root, dirs, files in os.walk(search_dir):
    for file in files:
      yield os.path.join(root, file)

def flat_dicom(dicom_file, with_private = False, with_pixels = False, with_seqs = True):
  ds = pydicom.dcmread(dicom_file, force=True)
  line = {}
  for element in itertools.chain(ds.file_meta, ds):
    if ((with_pixels or element.tag != 0x7FE00010) and 
       (with_private or not element.is_private) and
       (with_seqs or element.VR != "SQ")):
      dico_add(element, line = line, with_private = with_private, with_pixels = with_pixels, with_seqs = with_seqs)
  return line;
  
def dico_add(element, line, base = "", with_private = False, with_pixels = False, with_seqs = True):
  tag = f"{element.tag:#0{10}x}"
  name = f"{element.keyword}_" if element.keyword != '' else ''
  parent = "" if base == "" else f"{base}."
  dWith = "" if element.descripWidth == 35 else f"{element.descripWith}" 
  uLength = "" if not element.is_undefined_length else f"1" 
  mBytes = "" if element.maxBytesToDisplay == 16 else f"{element.maxBytesToDisplay}" 
  sVR = "" if element.showVR else f"0" 
  
  t = type(element.value)

  if t == pydicom.sequence.Sequence:
    i = 0
    for ds in element.value:
      i = i + 1
      for celem in ds:
        dico_add(celem, line, base = f"{parent}{name}{tag}_{element.VR}_{dWith}_{uLength}_{mBytes}_{sVR}@{i}", with_private = with_private, with_pixels = with_pixels, with_seqs = with_seqs)
  elif (t == list or t == pydicom.multival.MultiValue) and len(element.value) > 0:
    field_name = f"{parent}{name}{tag}_{element.VR}_{dWith}_{uLength}_{mBytes}_{sVR}"
    line[field_name] = json.dumps([encode_unit(e) for e in element.value])
  else:
    field_name = f"{parent}{name}{tag}_{element.VR}_{dWith}_{uLength}_{mBytes}_{sVR}"
    line[field_name] = encode_unit(element.value) 
    
  

def encode_unit(value):
  t = type(value)
  if t == int:
    return str(value)
  if t == float:
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
    return str(value)
  elif t == list and len(value)==0:
    return '[]'
  else:
    raise ValueError(f"cannot encode {t} as unit")

