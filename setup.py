#!/usr/bin/env python
from setuptools import setup
import os


with open("./econlog/__version__.py") as version_file:
    version = version_file.read().split("\"")[1]


def read(fname):
    try:
        with open(os.path.join(os.path.dirname(__file__), fname)) as f:
            return f.read()
    except IOError:
        return ""


setup(
    name = 'econlog',
    version = version,
    author = 'Balint Kovacs',
    author_email = 'kovacsbalu@gmail.com',
    description = "Show electronic construction log entries.",
    url = 'https://github.com/kovacsbalu/econlog',
    download_url="https://github.com/kovacsbalu/econlog/tarball/" + version,
    license = 'GNU GPL v3',
    keywords = ['econlog', 'enaplo'],
    packages = ['econlog'],
    long_description = read('readme.md')
)
