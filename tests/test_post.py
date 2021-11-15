import jupyter_to_medium as jtm


class TestPost:
    def test_post(self):
        jtm.publish("tests/notebooks/Test Medium Blog Post.ipynb")

    def test_empty_matplotlib(self):
        jtm.publish("tests/notebooks/Test Empty Matplotlib Screenshot.ipynb")

    def test_image_creation(self):
        jtm.publish("tests/notebooks/Test Image Creation.ipynb")

    def test_gistify(self):
        jtm.publish("tests/notebooks/Test Gistify Markdown.ipynb")

    def test_latex(self):
        jtm.publish("tests/notebooks/Test Latex.ipynb")
