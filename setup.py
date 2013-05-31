__author__ = 'ragnar'

import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "Bixby",
    version = "0.0.1",
    author = "Ragnar",
    author_email = "ragnar@handpoint.com",
    description = ("API for Handpoint Bixby payment service"),
    license = "BSD",
    keywords = "e-commerce handpoint Bixby",
    url = "handpoint.com",
    packages=['api'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 1 - Alpha",
        "Topic :: e-commerce",
        "License :: OSI Approved :: BSD License",
        ],
    )
