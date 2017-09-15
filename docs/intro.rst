************
Introduction
************

**Last Updated:** April 10, 2017

GsshaPy is an object relational model (ORM) for the Gridded Surface Subsurface
Hydrologic Analysis (GSSHA) model and a toolkit to convert gridded input into
GSSHA input. The purpose of GsshaPy is to expose GSSHA files to a web
development environment by reading them into an SQL database. The files
can also be written back to file for model execution. GsshaPy is built on top of
the powerful SQLAlchemy ORM.

.. image:: https://zenodo.org/badge/26494532.svg
   :target: https://zenodo.org/badge/latestdoi/26494532

   
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

GSSHA Installation
==================
1. Download & Install GSSHA: http://www.gsshawiki.com/GSSHA_Download
2. Next, ensure that the GSSHA executable is on your PATH.

.. note::

   For Windows, add GSSHA executable to Path:

   1. Go to: "Control Panel\System and Security\System"
   2. Click "Advanced system settings"
   3. Click "Environmental variables ..."
   4. Edit the "Path" variable under "User variables" and add the path to the directory containing GSSHA (i.e. C:\\Program Files\\U.S. Army\\gssha70)

.. _gsshapy-installation:

GSSHApy Installation
====================

.. note::

  The spatial components of GsshaPy can rely heavily on the PostGIS spatial
  extension for the PostgreSQL database. To work with spatial data in GsshaPy
  you will need to use a PostgreSQL database with PostGIS 2.1 or greater enabled.


Linux/Mac
---------

Download Miniconda & Install Miniconda
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See: https://conda.io/miniconda.html

Install Miniconda
~~~~~~~~~~~~~~~~~

::

    $ bash miniconda.sh -b
    $ export PATH=$HOME/miniconda2/bin:$PATH
    $ conda update --yes conda python

Install gsshapy
~~~~~~~~~~~~~~~

::

    $ conda create --name gssha python=2
    $ source activate gssha
    (gssha)$ conda config --add channels conda-forge
    (gssha)$ conda install --yes gsshapy

Install gsshapy for development:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ git clone https://github.com/CI-WATER/gsshapy.git
    $ cd gsshapy
    $ conda env create -f conda_env.yml
    $ source activate gssha
    (gssha)$ conda config --add channels conda-forge
    (gssha)$ conda install --yes pynio
    (gssha)$ python setup.py develop


.. note:: When using a new terminal, always type *source activate gssha* before using GsshaPy.

Windows
-------

.. note:: pynio installation instructions are not provided for Windows, so :func:`~gridtogssha.hrrr_to_gssha.HRRRtoGSSHA` will not work.

Download & Install Miniconda
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Go to: http://conda.pydata.org/miniconda.html
-  Download and run Windows Python 2 version installer
-  Install at
   C:\\Users\\YOUR_USERNAME\\Miniconda2
   or wherever you want
-  During installation, make Miniconda the default python and export to path

Install gsshapy:
~~~~~~~~~~~~~~~~

Open up the CMD program. Then, enter each line separately.

::

    > conda update --yes conda python
    > conda create --name gssha python=2
    > activate gssha
    (gssha)> conda config --add channels conda-forge
    (gssha)> conda install --yes gsshapy

Install gsshapy for development:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Download the code for gsshapy from https://github.com/CI-WATER/gsshapy
or clone it using a git program.

Open up the CMD program. Then, enter each line separately.

::

    > cd gsshapy
    > conda env create -f conda_env.yml
    > activate gssha
    (gssha)> conda config --add channels conda-forge
    (gssha)> python setup.py develop

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

Nathan Swain, Alan D. Snow, and Scott D. Christensen.

NSF Grant
=========

GsshaPy was developed at Brigham Young University with support from the National
Science Foundation (NSF) under Grant No. 1135482. GsshaPy is part of a larger effort
known as CI-Water_. The purpose of CI-Water is to develop cyber infrastructure for
water resources decision support.

.. _CI-Water: http://ci-water.org/
