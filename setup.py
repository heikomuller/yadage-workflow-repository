#! /usr/bin/env python

from setuptools import setup

setup(
    name='yadagewfrepo',
    version='0.0.1',
    description='Web API for Adage workflow templates',
    keywords='workflows reproducibility ',
    author='Heiko Mueller',
    author_email='heiko.muller@gmail.com',
    url='https://github.com/heikomuller/yadage-workflow-repository',
    license='GPLv3',
    packages=['yadagewfrepo'],
    package_data={'': ['LICENSE']},
    install_requires=[
        'flask>=0.10',
        'flask-cors>=3.0.2',
        'pyyaml',
        'jsonschema'
    ]
)
