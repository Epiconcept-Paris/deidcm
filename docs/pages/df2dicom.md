hide:
    - toc

## df2dicom Module

::: deidcm.dicom.df2dicom
    options:
        show_root_full_path: true
        members: None
        show_root_heading: false
        heading_level: 2


::: deidcm.dicom.df2dicom.df2dicom

??? example
    In the following example, we have a directory containing a single DICOM file. 
    ```py title="deidentify_attributes_and_pixels.py" linenums="1"
    from deidcm.dicom.df2dicom import df2dicom
    from deidcm.dicom.deid_mammogram import deidentify_attributes

    # First part of the deidentification process (Attribute deidentification)
    df = deidentify_attributes(indir='/path/to/indir', outdir='/path/to/outdir', org_root='15681.1344456.1444', erase_outdir=False)
    df.to_csv(os.path.join(outdir, 'meta.csv'))

    # Second part of the deidentification process (OCR deidentification)
    df2dicom(df, outdir='/path/to/outdir_folder', do_image_deidentification=True)
    ```

    Here is an overview of the resulting files in the output directory:
    ```txt
    outdir/
    ├── meta.csv
    └── 15681.1344456.1444.150859203650428010901213750509.png
    ```

??? example
    It is also possible to obtain only DICOM files:
    ```py title="only_dcm_files.py" linenums="1"
    ...
    df = deidentify_attributes(indir='/path/to/indir', outdir='/path/to/outdir', org_root='15681.1344456.1444', erase_outdir=False, output_file_formats = ["dcm"])
    ...
    ```

    Output directory:
    ```txt
    outdir/
    └── 15681.1344456.1444.150859203650428010901213750509.dcm
    ```

    it is also possible to obtain DICOM and PNG files:
    ```py title="only_dcm_files.py" linenums="1"
    ...
    df = deidentify_attributes(indir='/path/to/indir', outdir='/path/to/outdir', org_root='15681.1344456.1444', erase_outdir=False, output_file_formats = ["dcm", "png"])
    df.to_csv(os.path.join(outdir, 'meta.csv'))
    df2dicom(df, outdir='/path/to/outdir_folder', do_image_deidentification=True)
    ```

    Output directory:
    ```txt
    outdir/
    ├── meta.csv
    ├── 15681.1344456.1444.150859203650428010901213750509.png
    └── 15681.1344456.1444.150859203650428010901213750509.dcm
    ```