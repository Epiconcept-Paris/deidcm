# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md', encoding="utf-8") as f:
    readme = f.read()

setup(
    name='kskit',
    version='0.0.9',
    description='Cancer screening analysis module build on Python',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Francisco Orchard',
    author_email='f.orchard@epiconcept.fr',
    url='https://github.com/Epiconcept-Paris/kskit',
    license="MIT License",
    install_requires=[
        "paramiko",
        "fabric",
        "easyocr",
        "cryptography",
        "easyocr==1.4.1",
       # "torch==1.11.0",
       # "torchvision==0.12.0"
        "opencv-python==4.5.1.48",
        "opencv-python-headless==4.5.1.48",
        "pynetdicom",#==1.5.7",
        "Numpy",
        "matplotlib",
        "requests",
        "xmltodict",
        "pandas",
        "pyarrow",
        "python-barcode[images]",
        "qrcode",
        "pyzbar[scripts]",
        "opencv-python",
        "pycryptodome",
        "H5py",
        "imageio",
        "tqdm",
        "pillow",
        "gdcm"
    ],
    packages=find_packages(exclude=('tests', 'docs')),
    extras_require={
        "quality-tools": [
            "pylint",
            "autopep8",
            "pytest",
            "coverage"
        ]
    }
)
