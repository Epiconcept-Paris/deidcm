import os
import pydicom
from matplotlib import pyplot
import base64
import pandas as pd

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


def dico_add(element, line, base = "", with_private = with_private, with_pixels = with_pixels, with_seqs = with_seqs):
  tag = f"{element.tag:#0{10}x}"
  name = element.keyword if element.keyword != '' else ''
  parent = "" if base = "" else f"{base}."
  dWith = "" if element.descriptionWidth == 35 else f"{element.descriptionWith}" 
  uLength = "1" if element.is_undefined_length else f"0" 
  mBytes = "" if element.maxBytesToDisplay == 16 else f"{element.maxBytesToDisplay}" 
  sVR = "" if element.showVR else f"0" 
  
  t = type(element.value)

  if t == pydicom.sequence.Sequence:
    for ds in element.value:
      for celem in ds:
        dico_add(celem, line, base = "{base}.{name}_{tag}_{element.VR}_{dWith}_{uLength}_{mBytes}_{sVR}", with_private = with_private, with_pixels = with_pixels, with_seqs = with_seqs)
  elif (t == list or t == pydicom.sequence.Sequence) and len(element.value) > 0:
    field_name = "{base}.{name}_{tag}_{element.VR}{element.value[0].VR}_{dWith}_{uLength}_{mBytes}_{sVR}"
    line[field_name] = json.dumps([encode_unit(e) for element.value])
  else:
    field_name = "{base}.{name}_{tag}_{element.VR}_{dWith}_{uLength}_{mBytes}_{sVR}"
    line[field_name] = encode_unit(element.value) 
    
  

def encode_unit(value):
  t = type(value)
  if t == int:
    return str(value)
  elif t == str: 
    return value
  elif t == bytes: 
    return base64.b64encode(element.value).decode("UTF-8")
  elif t == pydicom.uid.UID
    return str(value)
  elif t == pydicom.valuerep.DSfloat
    return str(value)
  elif t == pydicom.valuerep.IS
    return str(value)
  elif t == pydicom.valuerep.DT
    return str(value.timestamp())
  elif t ==  pydicom.valuerep.PersonName
    return str(value.timestamp())
  elif t == list and len(value)==0
    return '[]'
  else
    raise ValueError("cannot encode {t} as unit")

