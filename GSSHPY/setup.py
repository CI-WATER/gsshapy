import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'sqlalchemy'
    ]

setup(name='gsshapy',
      version='0.1',
      description='Data model for GSSHA Models',
      long_description=README + '\n\n' + CHANGES,
      author='',
      author_email='',
      url='',
      keywords='gssha database model',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite='',
      entry_points="""\
      [paste.app_factory]
      """,
      )
