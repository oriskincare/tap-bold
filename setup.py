#!/usr/bin/env python
from setuptools import setup

setup(
    name="tap-bold",
    version="0.1.0",
    description="Singer.io tap for extracting data from Bold Recurring Orders Subscriptions API",
    author="Ori Ben Aharon",
    url="http://singer.io",
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
    keywords=['SINGER', 'TAP'],
    include_package_data=True,
    download_url='https://github.com/oriskincare/tap-bold/archive/v0.1.0.tar.gz',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'GNU GPLv3',  # Again, pick a license
        'Programming Language :: Python :: 3',  # Specify which pyhton versions that you want to support
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
