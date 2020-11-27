# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='kskit',
    version='0.0.1',
    description='Cancer screening analysis module build on Python',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Francisco Orchard',
    author_email='f.orchard@epiconcept.fr',
    url='https://github.com/Epiconcept-Paris/kskit',
    license=license,
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
      "pycrypto"
    ],
    packages=find_packages(exclude=('tests', 'docs'))
)

