# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md', encoding="utf-8") as f:
    readme = f.read()

setup(
    name='deidcm',
    version='0.0.1',
    description='Reusable toolset for deidentifiying images and metadata contained inside DICOM files',
    long_description=readme,
    long_description_content_type='text/markdown',
    author=['Francisco Orchard', 'William Madié'],
    author_email=['f.orchard@epiconcept.fr', 'w.madie@epiconcept.fr'],
    url='https://github.com/Epiconcept-Paris/deidcm',
    license="MIT License",
    install_requires=[
        "easyocr",
        "opencv-python",
        "opencv-python-headless",
        "Numpy==1.26.4",
        "matplotlib",
        "pandas",
        "pillow",
        "pydicom"
    ],
    packages=find_packages(
        include=['deidcm', 'deidcm.dicom'],
        exclude=['tests', 'docs']
    ),
    extras_require={
        "quality-tools": [
            "pylint",
            "autopep8",
            "pytest",
            "coverage",
            "pytest-cov"
        ],
        "mkdocs": [
            "mkdocs",
            "mkdocs-material",
            "mkdocs-material-extensions",
            "mkdocstrings-python",
            "pymdown-extensions",
            "mkdocs-pymdownx-material-extras"
        ]
    }
)
