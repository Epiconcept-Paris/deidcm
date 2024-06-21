## Prerequisites

!!! note
    Optical Character Recognition (OCR) is an intensive resource-consuming process and it is recommended to have at least **4 GB of free RAM** for running deidcm functionalities related to image deidentification.


!!! info
    deidcm relies on `easyOCR` which uses `PyTorch`. If your system does not have a GPU, consider installing `PyTorch` CPU-only version ([more information here](https://pytorch.org/get-started/locally/#linux-installation){:target="_blank"}).

* For installing `PyTorch` and `PyTorch Vision` **CPU-only dependencies** on a Linux system, run the command below:

```bash
pip3 install torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu
```

* If you have a GPU on your system, please install the correct version of `PyTorch` and `PyTorch Vision` for your computer ([PyTorch Installation Guide](https://pytorch.org/get-started/locally/#start-locally){:target="_blank"}).

## Installation

For installing `deidcm` tools, run the following command:

```bash
pip install deidcm
```

## Start working with deidcm

You can start using `deidcm` by importing functions.

Here is an example with the `deidentify_image_png` function. This function takes 3 parameters: an input dicom file, the output directory and the name of the final png file. More details can be found [here][deidcm.dicom.deid_mammogram.deidentify_image_png].

```py title="deidentify_image.py" linenums="1"
from deidcm.config import Config
from deidcm.dicom.deid_mammogram import deidentify_image_png

# Default Configuration (inbuilt-recipe, all words on pixels 
# have to be erased)
Config()

deidentify_image_png(
    infile="/data/dicoms/1.3.6.1.4.1.9590.100.1.2.16146556.dcm",
    outdir="/data/processed",
    filename="1.3.6.1.4.1.9590.100.1.2.16146556"
)
```

!!! note
    If you want to use a custom recipe, use the [the Config object][deidcm.dicom.deid_mammogram.Config].