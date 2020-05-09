import setuptools
import re

with open("README.md", "r") as fh:
    long_description = fh.read()

pat = r'!\[gif\]\('
repl = r'![gif](https://raw.githubusercontent.com/dexplo/jupyter_to_medium/master/'
long_description = re.sub(pat, repl, long_description)

setuptools.setup(
    name="jupyter_to_medium",
    version="0.0.2",
    author="Ted Petrou",
    author_email="petrou.theodore@gmail.com",
    description="Publish a Jupyter Notebook as a Medium blogpost",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="Jupyter Notebook Medium Blog",
    url="https://github.com/dexplo/jupyter_to_medium",
    packages=setuptools.find_packages(),
    license='MIT',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    # install_requires=["dataframe_image>=0.4"],
    python_requires='>=3.6',
    include_package_data=True
)