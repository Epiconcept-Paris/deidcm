hide:
    - toc

## dicom2df Module

::: deidcm.dicom.dicom2df
    options:
        show_root_full_path: true
        members: None
        show_root_heading: false
        heading_level: 2


::: deidcm.dicom.dicom2df.dicom2df

??? example
    In the following example, we have a directory containing a single DICOM file. 
    ```py title="dicom2df_single_file.py" linenums="1"
    from deidcm.dicom.dicom2df import dicom2df

    dicom2df(search_dir='/path/to/dcm-dir')
    ```

    In the output of the command, we can see the number of files that have been read correctly and then the dataframe containing all DICOM files information.
    ```txt
    06-26-2024 15:10:18 Successfully retrieved file(s): 1
    06-26-2024 15:10:18 Unreadable file(s): 0
    FileMetaInformationGroupLength_0x00020000_UL_1____  ...      FilePath
    0                                                208  ...  ./cmmd-1.dcm

    [1 rows x 101 columns]
    ```