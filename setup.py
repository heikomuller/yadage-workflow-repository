#! /usr/bin/env python

from setuptools import setup

setup(
    name='yadagetemplates',
    version='0.0.1',
    description='Web API for Yadage workflow templates',
    keywords='workflows reproducibility ',
    author='Heiko Mueller',
    author_email='heiko.muller@gmail.com',
    url='https://github.com/heikomuller/yadage-workflow-template-repository',
    license='GPLv3',
    packages=['yadagetemplates'],
    package_data={'': ['LICENSE']},
    install_requires=[
        'flask>=0.10',
        'flask-cors>=3.0.2',
        'pyyaml',
        'jsonschema'
    ]
)
