#!/usr/bin/env python
from setuptools import setup

setup(
    name="tap-bold",
    version="0.1.0",
    description="Singer.io tap for extracting data from Bold Recurring Orders Subscriptions API",
    author="Ori Ben Aharon",
    url="http://singer.io",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_bold"],
    install_requires=[
        "singer-python>=5.0.12",
        "requests",
    ],
    entry_points="""
    [console_scripts]
    tap-bold=tap_bold:main
    """,
    packages=["tap_bold"],
    package_data = {
        "schemas": ["tap_bold/schemas/*.json"]
    },
    include_package_data=True,
)
