import pytest
import jupyter_to_medium as jtm

class TestPost:

    def test_post(self):
        jtm.publish('tests/notebooks/Test Medium Blog Post.ipynb')


# def gistify_test_post():
#    p = publish('tests/notebooks/Test Medium Blog Post.ipynb', gistify=True)
#    return p
