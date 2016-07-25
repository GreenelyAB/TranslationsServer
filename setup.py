# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="TranslationsServer",
    version="0.1.0",
    description="The translations service server",
    long_description=long_description,
    url="https://github.com/GreenelyAB/TranslationsServer",
    author="GreenelyAB",
    author_email="info@greenely.com",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Communications",
        "Topic :: Software Development :: Internationalization",
        "Topic :: Software Development :: Localization",
        "Topic :: Text Processing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
    ],
    keywords=(
        "store manage translation translations server internationalization"),
    packages=find_packages("src", exclude=["tests"]),
    package_dir = {"": "src"},
    install_requires=["pyzmq>=15.2.0", "psycopg2>=2.6.1", "DBQuery>=0.3.1"],
    extras_require={
    },
)
