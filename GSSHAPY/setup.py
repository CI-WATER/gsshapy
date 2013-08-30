import os

from setuptools import setup, find_packages

requires = [
    'sqlalchemy==0.7'
    ]

setup(name='gsshapy',
      version='1.0.1',
      description='An SQLAlchemy ORM for GSSHA model files.',
      long_description='',
      author='Nathan Swain',
      author_email='nathan.swain@byu.net',
      url='https://bitbucket.org/swainn/gsshapy',
      license='BSD 2-Clause License',
      keywords='gssha database model',
      packages=find_packages(),
      include_package_data=True,
      install_requires=requires,
      tests_require=requires,
      test_suite='gsshapy.tests.all_tests'
      )