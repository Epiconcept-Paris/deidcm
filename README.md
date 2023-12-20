## kskit module

Functionality for cancer screening data pipeline including DICOM image importing and processing.

Initially conceived for french breast cancer screening program during the execution of deep.pisre study

## Documentation

kskit documentation can be found at: [https://epiconcept-paris.github.io/kskit/](https://epiconcept-paris.github.io/kskit/)


## Run Tests

Run all tests
```py
pytest
```

Run a specific test file
```py
pytest test/test_df2dicom.py
```

Run all except OCR tests
```py
pytest --ignore=test/test_ocr_deidentification.py
```

Produce an HTML report with test coverage
(The report will be available in `htmlcov/index.html` )
```py
coverage run -m pytest
```

Show full error message
```py
pytest test/test_df2dicom.py --showlocals
```
