# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

setup(
    name='kskit',
    version='0.0.8',
    description='Cancer screening analysis module build on Python',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Francisco Orchard',
    author_email='f.orchard@epiconcept.fr',
    url='https://github.com/Epiconcept-Paris/kskit',
    license="MIT License",
    install_requires=[
      "pydicom",
      "Numpy",
      "matplotlib",
      "pynetdicom",
      "requests",
      "xmltodict", 
      "pandas",
      "pyarrow",
      "python-barcode[images]",
      "qrcode",
      "pyzbar[scripts]",
      "opencv-python",
      "pycryptodome"
    ],
    packages=find_packages(exclude=('tests', 'docs'))
)

