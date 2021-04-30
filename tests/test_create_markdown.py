import pytest
import os.path
from jupyter_to_medium._publish_to_medium import Publish

@pytest.fixture
def file_name():
    path = os.path.dirname(__file__)
    yield os.path.join(path,'notebooks','latex_to_medium.ipynb')
    

def test_create_markdown(file_name):
    publish = Publish(filename=file_name)
    md, image_data_dict = publish.create_markdown()
    a = 1