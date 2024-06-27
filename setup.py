# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md', encoding="utf-8") as f:
    readme = f.read()

setup(
    name='deidcm',
    version='0.0.3',
    python_requires='>=3.6',
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
        "Numpy>=1.21.6",
        "matplotlib",
        "pandas",
        "pillow",
        "pydicom"
    ],
    packages=find_packages(),

    # Include non-code file in distribution
    include_package_data=True,

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
    },
    classifiers=[
        "License:: OSI Approved:: MIT License",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience:: Healthcare Industry",
        "Topic:: Scientific/Engineering:: Image Processing",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.10",
    ]
)
