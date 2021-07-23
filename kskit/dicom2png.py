from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut
import skimage
import pydicom
import numpy as np
from PIL import Image
import warnings

def dicom2png(infile, outfile):
  pixels = dicom2narray(infile)
  img = Image.fromarray(pixels[0])
  img.save(outfile + ".png")
  print(f"file {outfile} written")




def dicom2narray(path, voi_lut = False, fix_monochrome = True):
    """
    Converts a DICOM into a NUMPY array and returns this array and 
    its corresponding dataset.
    """
    dicom = pydicom.read_file(path)

    # VOI LUT (if available by DICOM device) is used to transform raw DICOM data
    # to "human-friendly" view 
    if voi_lut:
        # If the modality is CT (Scanner Image) we have to convert the values of 
        # the image first with apply_modality
        # It uses the values of RescaleSlope and RescaleIntercept to convert the 
        # values or the attribute LUT Sequence
        if dicom.Modality == "CT":
            data = apply_modality_lut(dicom.pixel_array, dicom)
            data = apply_voi_lut(data, dicom)
        else:
            data = apply_voi_lut(dicom.pixel_array, dicom)
    else:
        data = dicom.pixel_array

    # depending on this value, X-ray may look inverted - fix that:
    if fix_monochrome and dicom.PhotometricInterpretation == "MONOCHROME1":
        data = np.amax(data) - data

    #If the DICOM are not in one of these two formats, it can bring new problems.
    if dicom.PhotometricInterpretation != "MONOCHROME2" and \
        dicom.PhotometricInterpretation != "MONOCHROME1":
        warnings.warn("PhotometricInterpretation " + 
        dicom.PhotometricInterpretation + " can cause unexpected behaviors.\n" +
        "File concerned : " + path)
        
    data = data - np.min(data)
    data = data / np.max(data)
    data = (data * 255).astype(np.uint8)
    
    return (data, dicom)




def narray2dicom(pixels, dataset, outfile):
    """Converts a NUMPY array into a DICOM and returns this DICOM."""
    # If the modality equals 'CT'. The conversion will be incorrect because it 
    # needs a Rescaling operation.

    if dataset.Modality in ['CT','DX','MR']:
        raise TypeError("""
Conversion from NUMPY array to DICOM with Modality {} is not supported by this module.
File concerned : {}
""".format(dataset.Modality, outfile))
    
    # Some sets of DICOM can be in 8 bits
    # We have to adapt the array depending on whether it's 8 or 16 bits
    
    if dataset.BitsAllocated == 8:
        dataset.PixelData = pixels.astype(np.uint8).tobytes()
    elif dataset.BitsAllocated == 16:  
        dataset.PixelData = pixels.astype(np.uint16).tobytes()
    else:
        raise ValueError("Unsupported Bits format in dataset : BitsAllocated = " + 
        str(dataset.BitsAllocated))
    dataset.save_as(outfile)


def narray2png(pixels, output_path):
    """Saves a Numpy array in PNG format"""
    img = Image.fromarray(pixels)
    img.save(output_path + ".png")