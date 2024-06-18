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

After that, you'll have to define an environment variable called `DP_HOME`. This
variable is used to locate your **data directory** where you'll:

* put your DICOM files for submitting them to the deidentifier tool
* find the output of the deidentifier tool (deidentified information)
* define referentials used by the package (`recipe.json`, `ocr_deid_words.txt`)

To define this **data directory**, run the following command:

```bash
export DP_HOME=/path/to/folder
```

!!! info
    You can set this folder wherever you want. However, keep in mind that this folder is essential for the package and you'll probably open it more than once. So, don't put it somewhere too complicated to access.

## Start working with deidcm

```py title="deidentify_image.py" linenums="1"
from deidcm.dicom.deid_mammogram import deidentify_image_png

deidentify_image_png(
    "/data/dicoms/1.3.6.1.4.1.9590.100.1.2.16146556.dcm",
    "/data/processed",
    "1.3.6.1.4.1.9590.100.1.2.16146556"
)

```