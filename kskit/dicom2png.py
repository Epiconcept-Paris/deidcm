import warnings
from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut
import pydicom
import numpy as np
from PIL import Image


def dicom2png(infile, outfile):
    pixels = dicom2narray(infile)
    img = Image.fromarray(pixels[0])
    img.save(outfile + ".png")
    print(f"file {outfile} written")


def dicom2narray(path, voi_lut=False, fix_monochrome=True):
    """
    Converts a DICOM into a NUMPY array and returns this array and 
    its corresponding dataset.
    """
    ds = pydicom.read_file(path)

    # VOI LUT (if available by DICOM device) is used to transform raw DICOM data
    # to "human-friendly" view
    if voi_lut:
        # If the modality is CT (Scanner Image) we have to convert the values of
        # the image first with apply_modality
        # It uses the values of RescaleSlope and RescaleIntercept to convert the
        # values or the attribute LUT Sequence
        if ds.Modality == "CT":
            data = apply_modality_lut(ds.pixel_array, ds)
            data = apply_voi_lut(data, ds)
        else:
            data = apply_voi_lut(ds.pixel_array, ds)
    else:
        data = ds.pixel_array

    # depending on this value, X-ray may look inverted - fix that:
    if fix_monochrome and ds.PhotometricInterpretation == "MONOCHROME1":
        data = np.amax(data) - data

    # If the DICOM are not in one of these two formats, it can bring new problems.
    if ds.PhotometricInterpretation not in ["MONOCHROME2", "MONOCHROME1"]:
        warnings.warn(
            f"PhotometricInterpretation {ds.PhotometricInterpretation} \
            can cause unexpected behaviors. File concerned: {path}")

    data = data - np.min(data)
    data = data / np.max(data)
    data = (data * 255).astype(np.uint8)

    return (data, ds)


def narray2dicom(pixels, ds, outfile):
    """Converts a NUMPY array into a DICOM and returns this DICOM."""
    # If the modality equals 'CT'. The conversion will be incorrect because it
    # needs a Rescaling operation.

    if ds.Modality in ['CT', 'DX', 'MR']:
        raise TypeError(
            f"Conversion from NUMPY array to DICOM with Modality \
            {ds.Modality} is not supported by this module.\
            File concerned : {outfile}")

    # Some sets of DICOM can be in 8 bits
    # We have to adapt the array depending on whether it's 8 or 16 bit
    if ds.BitsAllocated == 8:
        ds.PixelData = pixels.astype(np.uint8).tobytes()
    elif ds.BitsAllocated == 16:
        ds.PixelData = pixels.astype(np.uint16).tobytes()
    else:
        raise ValueError(
            f"Unsupported Bits format in ds : BitsAllocated = {ds.BitsAllocated}")
    ds.save_as(outfile)


def narray2png(pixels, output_path):
    """Saves a Numpy array in PNG format"""
    img = Image.fromarray(pixels)
    img.save(output_path + ".png")
