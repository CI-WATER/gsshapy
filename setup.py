from setuptools import setup, find_packages

requires = [
    'sqlalchemy>=0.7',
    'mapkit>=1.1.0',
    'python-dateutil',
    'requests',
    'psycopg2',
    'futures',
    ]

setup(name='gsshapy',
      version='2.1.0',
      description='An SQLAlchemy ORM for GSSHA model files and a toolkit to convert gridded input into GSSHA input.',
      long_description='',
      author='Nathan Swain and Alan D. Snow',
      author_email='nathan.swain@byu.net',
      url='https://github.com/CI-WATER/gsshapy',
      license='BSD 3-Clause License',
      keywords='GSSHA, database, object relational model',
      packages=['gridtogssha'] + find_packages(),
      include_package_data=True,
      install_requires=requires,
      )
