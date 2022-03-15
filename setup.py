# -*- coding: utf-8 -*-

# Learn more: https://github.com/ErwingForeroXpert/Presupuesto

from setuptools import setup, find_packages

with open('README') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='Presupuesto',
    version='0.1.0',
    description='Project for manage budget',
    long_description=readme,
    author='Erwing Forero',
    author_email='erwing.forero@xpertgroup.co',
    url='https://github.com/ErwingForeroXpert/Presupuesto',
    license=license,
    packages=find_packages(exclude=('test','docs'))
)