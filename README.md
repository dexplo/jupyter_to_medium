# Jupyter to Medium

Publish Jupyter Notebooks as Medium blog posts with the help of jupyter_to_medium.

## Installation

`pip install jupyter_to_medium`

## Usage

Pass the `publish` function the location of the Jupyter Notebook you would like to publish as a Medium blog post

```python
>>> import jupyter_to_medium as jtm
>>> jtm.publish('My Awesome Jupyter Notebook.ipynb',
                integration_token=None,
                pub_name=None,
                dataframe_image=True,
                title=None,
                tags=None,
                publish_status='draft',
                notify_followers=False,
                license='all-rights-reserved',
                canonical_url=None)
```

If successful, JSON data will be returned with the URL.

## Dependencies

This package relies on [dataframe_image](https://github.com/dexplo/dataframe_image) to convert your notebooks to markdown with dataframes
as images.