import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()

requires = [
    'sqlalchemy>=0.7'
    ]

setup(name='gsshapy',
      version='0.1',
      description='An SQLAlchemy ORM GSSHA model files.',
      long_description=README,
      author='Nathan Swain',
      author_email='nathan.swain86@gmail.com',
      url='',
      keywords='gssha database model',
      packages=find_packages(),
      include_package_data=True,
      install_requires=requires,
      tests_require=requires,
      test_suite=''
      )

## TODO: Add test_suite function name e.g. gsshapy.tests.test_all
## See: http://pythonhosted.org/distribute/setuptools.html#test