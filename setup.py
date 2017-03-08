from setuptools import setup, find_packages

requires = [
    'affine',
    'mapkit>=1.2.0',
    'psycopg2',
    'rapidpy',
    'sqlalchemy',
    'timezonefinder',
    'utm',
    ]

setup(name='gsshapy',
      version='2.2.0',
      description='An SQLAlchemy ORM for GSSHA model files and a toolkit'
                  ' to convert gridded input into GSSHA input.',
      long_description='',
      author='Nathan Swain and Alan D. Snow',
      author_email='nathan.swain@byu.net',
      url='https://github.com/CI-WATER/gsshapy',
      license='BSD 3-Clause License',
      keywords='GSSHA, database, object relational model',
      packages=find_packages(),
      include_package_data=True,
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
