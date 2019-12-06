#!/usr/bin/env python

from setuptools import setup
from chargeamps import __version__


setup(
    name='chargeamps',
    version=__version__,
    description='Charge-Amps API bindings for Python',
    author='Jakob Schlyter',
    author_email='jakob@kirei.se',
    license='BSD',
    keywords='ev',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3 :: Only'
    ],
    url='https://github.com/kirei/python-chargeamps',
    packages=['chargeamps'],
    install_requires=[
        'aiohttp',
        'dataclasses-json',
        'marshmallow',
        'pyjwt',
        'setuptools',
    ],
    entry_points={
        "console_scripts": [
            "chargeamps = chargeamps.cli:main"
        ]
    }
)
