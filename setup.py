from setuptools import setup, find_packages

requires = [
    'affine',
    'appdirs',
    'mapkit>=1.2.0',
    'psycopg2',
    'rapidpy',
    'sqlalchemy',
    'timezonefinder',
    'utm',
    'pangaea',
    'pyyaml',
    'wrf-python',
]

setup(name='gsshapy',
      version='2.3.4',
      description='An SQLAlchemy ORM for GSSHA model files and a toolkit'
                  ' to convert gridded input into GSSHA input.',
      long_description='Documentation can be found at '
                       'http://gsshapy.readthedocs.io. \n\n'
                       '.. image:: https://zenodo.org/badge/26494532.svg \n'
                       '    :target: '
                       'https://zenodo.org/badge/latestdoi/26494532',
      author='Nathan Swain, Alan D. Snow, and Scott D. Christensen',
      author_email='nathan.swain@byu.net',
      url='https://github.com/CI-WATER/gsshapy',
      license='BSD 3-Clause License',
      keywords='GSSHA, database, object relational model',
      packages=find_packages(),
      package_data={'': ['grid/land_cover/*.txt']},
      classifiers=[
                'Intended Audience :: Developers',
                'Intended Audience :: Science/Research',
                'Operating System :: OS Independent',
                'Programming Language :: Python',
                'Programming Language :: Python :: 2',
                'Programming Language :: Python :: 2.7',
                'Programming Language :: Python :: 3',
                'Programming Language :: Python :: 3.5',
                ],
      install_requires=requires,
      extras_require={
        'tests': [
            'coveralls',
            'pytest',
            'pytest-cov',
        ],
        'docs': [
            'mock',
            'sphinx',
            'sphinx_rtd_theme',
            'sphinxcontrib-napoleon',
        ]
      },
      )
