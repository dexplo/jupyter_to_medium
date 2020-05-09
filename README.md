# Jupyter to Medium

Publish your Jupyter Notebooks as Medium blog posts with the help of jupyter_to_medium.

## Installation

`pip install jupyter_to_medium`

## Usage

```python
>>> import jupyter_to_medium as jtm
>>> jtm.post('My Awesome Jupyter Notebook.ipynb',
             pub_name='Dunder Data',
             publish_status='draft',
             dataframe_iamge=True)
```

If successful, JSON data will be returned with the URL. 

## Dependencies

This package relies on [dataframe_image] to convert your notebooks to markdown with dataframes
as images