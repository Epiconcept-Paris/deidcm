## kskit module

Functionality for cancer screening data pipeline including DICOM image importing and processing.

Initially conceived for french breast cancer screening program during the execution of deep.piste study

## Documentation

kskit documentation can be found at: [https://epiconcept-paris.github.io/kskit/](https://epiconcept-paris.github.io/kskit/)

### Installation

```bash
pip install kskit
```

### Installation for contributors

1. Download source code

```bash
git clone https://github.com/Epiconcept-Paris/kskit.git
cd kskit
```

2. Create and activate a virtual environment

```bash
python3 -m venv env
. env/bin/activate
```

3. Install kskit

```bash
pip install -e .
```

### Checking installation

Open a python interpreter and try to deidentify a dicom file:
```python
from kskit.dicom.deid_mammogram import deidentify_image_png

deidentify_image_png(
    "/path/to/mammogram.dcm",
    "/path/to/processed/output-folder",
    "output-filename"
)
```
## Tools for developers

## Installation

```bash
pip install -e .[quality-tools]
```

## Usage

Format your files with `python3 -m autopep8 --in-place file/to/format`

Lint your files with `python3 -m pylint file/to/lint`
