from setuptools import setup, find_packages

setup(
    name="maximal-empty-rectangles",
    version="0.1.0",
    url="https://github.com/danoneata/maximal-empty-rectangles",
    author="Dan Oneață",
    author_email="dan.oneata@gmail.com",
    description="Finds maximum empty rectangles given a list of axis-aligned rectangular obstacles",
    packages=find_packages(),
    install_requires=["toolz", "portion"],
)
