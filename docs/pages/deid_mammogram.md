::: deidcm.dicom.deid_mammogram
    options:
        show_root_full_path: true
        members: None

|          **Deidentification Functionalities**          |
|:------------------------------------------------------:|
|           Image Deidentification based on OCR          |
| Attributes/Metadata Deidentification based on a Recipe |

## Image Deidentification

::: deidcm.dicom.deid_mammogram.deidentify_image_png

::: deidcm.dicom.deid_mammogram.get_PIL_image

??? example
    ```py title="get_PIL_image.py" linenums="1"
    from deidcm_deid.dicom.deid_mammogram import get_PIL_image
    import pydicom

    ds = pydicom.read_file("my-mammogram.dcm")
    img = get_PIL_image(ds)
    img.show()
    ```

::: deidcm.dicom.deid_mammogram.get_text_areas

!!! info
    The list of available languages can be found [here](https://www.jaided.ai/easyocr/){:target="_blank"}.

::: deidcm.dicom.deid_mammogram.remove_authorized_words_from

!!! info
    For more information on how to define your own list of authorized words, go to [Customize Deidentification Tasks](#customize-deidentification-tasks)

::: deidcm.dicom.deid_mammogram.hide_text

## Attributes Deidentification

::: deidcm.dicom.deid_mammogram.deidentify_attributes

!!! info
    `org_root` refers to a prefix used for deidentifying DICOM UIDs. 
    This prefix has to be unique for your organization.
    
    For more information, see [NEMA DICOM Standards Documentation](https://dicom.nema.org/dicom/2013/output/chtml/part05/sect_9.2.html){:target="_blank"}.

??? example
    Let's test our recipe by adding one of its attribute into a pydicom dataset.
    The attribute in our recipe looks like this:
    ```json
    "0x00209161": [
        "ConcatenationUID",
        "UI",
        "PSEUDONYMISER"
    ],
    ``` 

    **Step n°1**: We add the new DICOM UID to our pydicom dataset
    ```py linenums="1"
    import pydicom

    ds = pydicom.read_file("my-mammogram.dcm")
    ds.add_new("0x00209161", "UI", "1.123.123.1234.123456.12345678")
    ds.save_as("my-modified-mammogram.dcm")
    ``` 
    
    It will then appear inside your pydicom dataset:
    ```bash
    (0020, 9161) Concatenation UID                   UI: 1.123.123.1234.123456.12345678
    ```

    **Step n°2**: We deidentify the folder containing our test mammogram
    ```py linenums="1"
    from deidcm_deid.dicom.deid_mammogram import deidentify_attributes

    df = deidentify_attributes("/path/to/mammogram/folder", "/path/to/outdir", org_root="9.9.9.9.9", erase_outdir=False)
    print(df.ConcatenationUID_0x00209161_UI_1____)
    ```
    ```bash
    9.9.9.9.9.474079559915109435636573090782
    ```

::: deidcm.dicom.deid_mammogram.get_general_rule

!!! note
    This function is implicitly called by [deidentify_attributes][deidcm.dicom.deid_mammogram.deidentify_attributes] each time
    it needs to take a deidentification action.

!!! warning
    This function takes a [zero trust approach](https://fr.wikipedia.org/wiki/Zero_trust){:target="_blank"} when encountering
    unknown tags and will always return RETIRER (= REMOVE) for all tags not found inside the recipe.

??? example
    **Example n°1**: Retrieve a rule for a tag inside the recipe
    
    ```py title="get_general_rule_for_known_tag.py" linenums="1"
    from deidcm_deid.dicom.deid_mammogram import load_recipe, get_general_rule

    recipe = load_recipe()
    rule = get_general_rule("0x00020000", recipe)
    ```
    ```bash
    CONSERVER
    ```

    **Example n°2**: Retrieve a rule for a tag that is not declared inside the recipe
    
    ```py title="get_general_rule_for_unknown_tag.py" linenums="1"
    from deidcm_deid.dicom.deid_mammogram import load_recipe, get_general_rule

    recipe = load_recipe()
    rule = get_general_rule("0x00026666", recipe)
    ```
    ```bash
    RETIRER
    ```

::: deidcm.dicom.deid_mammogram.get_specific_rule

## Customize Deidentification Tasks

::: deidcm.config.Config
    options:
        show_root_full_path: true
        members: None

::: deidcm.config.Config.__new__

??? example
    Default Configuration (inbuilt recipe, no authorized words)
    ```py title="default_config.py" linenums="1"
    from deidcm.config import Config

    config = Config()
    print(config.recipe)
    ```

    Custom Configuration
    ```py title="custom_config.py" linenums="1"
    from deidcm.config import Config

    config = Config(recipe_path="/path/to/custom-recipe.json", authorized_words_path="/path/to/authorized_words.txt")
    print(config.recipe)
    ```

::: deidcm.config.Config.load_recipe
    options:
        show_root_full_path: true

!!! note
    You don't have to call this function as it already implicitly when you instanciate [the Config object][deidcm.dicom.deid_mammogram.Config].

!!! tip
    This function can be called to check if your customized recipe is correctly
    detected by deidcm.

??? example
    ```py title="example_load_recipe.py" linenums="1"
    from deidcm.config import Config

    config = Config(recipe_path="/path/to/custom-recipe.json", authorized_words_path="/path/to/authorized_words.txt")
    print(config.recipe)
    ```

    ```py
    {'0x00020000': ['FileMetaInformationGroupLength', 'UL', 'CONSERVER'], '0x00020001': ['FileMetaInformationVersion', 'OB', 'CONSERVER']}
    ```

::: deidcm.config.Config.load_authorized_words
    options:
            show_root_full_path: true

!!! note
    You don't have to call this function as it already implicitly when you instanciate [the Config object][deidcm.dicom.deid_mammogram.Config].

!!! tip
    This function can be called to check if your customized list of authorized words is correctly
    detected by deidcm.

??? example
    ```py title="example_load_recipe.py" linenums="1"
    from deidcm.config import Config

    config = Config(recipe_path="/path/to/custom-recipe.json", authorized_words_path="/path/to/authorized_words.txt")
    print(config.authorized_words)
    ```

    ```py
    ['HELLO', 'ALTER', 'DSQLD', 'SHOCR']
    ```