#!/usr/bin/env python

from os import path

from setuptools import setup

from chargeamps import __version__

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="chargeamps",
    version=__version__,
    description="Charge-Amps API bindings for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Jakob Schlyter",
    author_email="jakob@kirei.se",
    license="BSD",
    keywords="ev",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    url="https://github.com/kirei/python-chargeamps",
    python_requires=">=3.6.1",
    packages=["chargeamps"],
    install_requires=[
        "aiohttp",
        'dataclasses;python_version<"3.7"',
        "dataclasses-json",
        "isodate",
        "marshmallow",
        "pyjwt",
        "setuptools",
    ],
    entry_points={"console_scripts": ["chargeamps = chargeamps.cli:main"]},
)
