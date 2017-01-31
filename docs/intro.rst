************
Introduction
************

**Last Updated:** September 16, 2016

GsshaPy is an object relational model (ORM) for the Gridded Surface Subsurface
Hydrologic Analysis (GSSHA) model. The purpose of GsshaPy is to expose GSSHA files
to a web development environment by reading them into an SQL database. The files
can also be written back to file for model execution. GsshaPy is built on top of
the powerful SQLAlchemy ORM.


What is GSSHA?
==============

GSSHA is a physically-based, distributed hydrologic model. GSSHA is developed
and maintained by Coastal and Hydraulics Laboratory (CHL) which is
a member of the Engineer Research & Development Center of the United
States Army Corps of Engineers (USACE). GSSHA is used to predict soil
moisture as well as runoff and flooding on watersheds.

.. note::

	For more information about GSSHA please visit the the gsshawiki_ .

.. _gsshawiki: http://www.gsshawiki.com/Main_Page

Requirements
============

The spatial components of GsshaPy rely heavily on the PostGIS spatial extension for the PostgreSQL database. To work with
spatial data in GsshaPy you will need to use a PostgreSQL database with PostGIS 2.1 or greater enabled. In addition,
GsshaPy relies on a Python module called mapkit to generate visualizations. This will automatically be installed when
you install GsshaPy.

It is recommended to use Anaconda to install GsshaPy (See: https://www.continuum.io/downloads).

.. _gsshapy-installation:

Installation
============

Linux/Mac
---------

Prerequisites
~~~~~~~~~~~~~

Download Miniconda
^^^^^^^^^^^^^^^^^^

Linux
'''''

::

    $ wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh

Mac
'''

::

    $ curl -o miniconda.sh https://repo.continuum.io/miniconda/Miniconda2-latest-MacOSX-x86_64.sh


Install Miniconda
^^^^^^^^^^^^^^^^^

::

    $ chmod +x miniconda.sh
    $ ./miniconda.sh -b
    $ export PATH=$HOME/miniconda2/bin:$PATH
    $ conda update --yes conda python

Create gssha conda environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    $ git clone https://github.com/CI-WATER/gsshapy.git
    $ cd gsshapy

Option 1: From the gsshapy-conda-env.yml file
'''''''''''''''''''''''''''''''''''''''''''''

::

    $ conda env create -f conda-env.yml

Option 2: Step-by-step
''''''''''''''''''''''

::

    $ conda create --name gssha python=2
    $ source activate gssha
    $ conda config --add channels conda-forge
    (gssha)$ conda install --yes rapidpy pygrib psycopg2

Install gsshapy:
^^^^^^^^^^^^^^^^

Stable Release
''''''''''''''

::

    (gssha)$ pip install gsshapy

Latest version
''''''''''''''

::

    (gssha)$ python setup.py install


.. note:: When using a new terminal, always type *source activate gssha* before using GsshaPy.

Windows
-------

.. note:: pygrib instructions are not provided for Windows, so :func:`~gridtogssha.hrrr_to_gssha.HRRRtoGSSHA` will not work.

Download & Install Miniconda
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Go to: http://conda.pydata.org/miniconda.html
-  Download and run Windows Python 2 version installer
-  Install at
   C:\\Users\\YOUR_USERNAME\\Miniconda2
   or wherever you want
-  During installation, make Miniconda the default python and export to path

Create gssha conda environment:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open up the CMD program. Then, enter each line separately.

::

    > conda update --yes conda python
    > conda create --name gssha python=2
    > activate gssha
    (gssha)> conda config --add channels conda-forge
    (gssha)> conda install --yes rapidpy psycopg2
    (gssha)> deactivate

Install gsshapy:
~~~~~~~~~~~~~~~~

Stable Release
^^^^^^^^^^^^^^

::

    > activate gssha
    (gssha)> pip install gsshapy

Latest version
^^^^^^^^^^^^^^

Download the code for gsshapy from https://github.com/CI-WATER/gsshapy
or clone it using a git program.

Open up the CMD program. Then, enter each line separately.

::

    > cd gsshapy
    > activate gssha
    (gssha)> python setup.py install

.. note:: When using a new CMD terminal, always type *activate gssha* before using GsshaPy.


License
=======

GsshaPy is released under the `BSD 3-Clause license`_.

.. _BSD 3-Clause license: https://github.com/CI-WATER/gsshapy/blob/master/LICENSE.txt

.. raw:: html

	<div>
		<script src="https://github.com/CI-WATER/gsshapy/blob/master/LICENSE.txt?embed=t"></script>
	</div>

Source
======

The source code is available on GitHub: https://github.com/CI-WATER/gsshapy.git

Authors
=======

Nathan Swain & Alan D. Snow

NSF Grant
=========

GsshaPy was developed at Brigham Young University with support from the National
Science Foundation (NSF) under Grant No. 1135482. GsshaPy is part of a larger effort
known as CI-Water_. The purpose of CI-Water is to develop cyber infrastructure for
water resources decision support.

.. _CI-Water: http://ci-water.org/
