from ._publish_to_medium import publish


class TestPost:
    def test_post(self):
        publish("tests/notebooks/Test Medium Blog Post.ipynb")

    def test_empty_matplotlib(self):
        publish("tests/notebooks/Test Empty Matplotlib Screenshot.ipynb")

    def test_image_creation(self):
        publish("tests/notebooks/Test Image Creation.ipynb")

    def test_gistify(self):
        publish("tests/notebooks/Test Gistify Markdown.ipynb")

    def test_latex(self):
        publish("tests/notebooks/Test Latex.ipynb")
