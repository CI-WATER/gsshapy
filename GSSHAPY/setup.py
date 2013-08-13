import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
LICENSE = open(os.path.join(here, 'LICENSE.txt')).read()

requires = [
    'sqlalchemy>=0.7'
    ]

setup(name='gsshapy',
      version='1.0.0',
      description='An SQLAlchemy ORM for GSSHA model files.',
      long_description=README,
      author='Nathan Swain',
      author_email='nathan.swain@byu.net',
      url='https://bitbucket.org/swainn/gsshapy',
      license=LICENSE,
      keywords='gssha database model',
      packages=find_packages(),
      include_package_data=True,
      install_requires=requires,
      tests_require=requires,
      test_suite='gsshapy.tests.all_tests'
      )