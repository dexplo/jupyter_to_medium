import pytest
import jupyter_to_medium as jtm


def test_gistify_post():
    p = jtm.publish(
        'tests/notebooks/Test Medium Blog Post.ipynb', gistify=True)
    return p


class TestPost:

    def test_post(self):
        jtm.publish('tests/notebooks/Test Medium Blog Post.ipynb')
