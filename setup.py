from setuptools import setup, find_packages

requires = [
    'sqlalchemy>=0.7',
    'mapkit>=1.1.0'
    ]

setup(name='gsshapy',
      version='2.0.0',
      description='An SQLAlchemy ORM for GSSHA model files.',
      long_description='',
      author='Nathan Swain',
      author_email='nathan.swain@byu.net',
      url='https://bitbucket.org/swainn/gsshapy',
      license='BSD 2-Clause License',
      keywords='GSSHA, database, object relational model',
      packages=['gsshapy', 'lsmtogssha'],
      include_package_data=True,
      install_requires=requires,
      tests_require=requires,
      test_suite='gsshapy.tests.all_tests'
      )