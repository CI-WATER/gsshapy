import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
LICENSE = open(os.path.join(here, 'LICENSE.txt')).read()

requires = [
    'sqlalchemy>=0.7'
    ]

setup(name='gsshapy',
      version='0.0.1',
      description='An SQLAlchemy ORM GSSHA model files.',
      long_description=README,
      author='Nathan Swain',
      author_email='nathan.swain@byu.net',
      url='',
      license=LICENSE,
      keywords='gssha database model',
      packages=find_packages(),
      include_package_data=True,
      install_requires=requires,
      tests_require=requires,
      test_suite='gsshapy.lib.test_tools.all_tests'
      )