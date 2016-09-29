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


Installation
============

Prerequisites
-------------

Linux/Mac
^^^^^^^^^

See: https://github.com/CI-WATER/gsshapy/blob/master/.travis.yml

Download & Install Miniconda
''''''''''''''''''''''''''''

Linux
     

::

    $ wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh

Mac
   

::

    $ curl -o miniconda.sh https://repo.continuum.io/miniconda/Miniconda2-latest-MacOSX-x86_64.sh

Install Python packages with all dependencies
'''''''''''''''''''''''''''''''''''''''''''''

::

    $ chmod +x miniconda.sh
    $ ./miniconda.sh -b
    $ export PATH=$HOME/miniconda2/bin:$PATH
    $ conda update --yes conda python
    $ conda create --name gssha python=2
    $ source activate gssha
    $ conda install --yes nose numpy netCDF4 gdal pyproj
    $ source deactivate gssha
    $ source activate gssha



Install GRIB-API
''''''''''''''''
.. warning:: The GRIB-API installation is optional. Only install if you need :func:`~gridtogssha.hrrr_to_gssha.HRRRtoGSSHA`.

See: https://software.ecmwf.int/wiki/display/GRIB/GRIB+API+installation

::

    $ cd $HOME 
    $ mkdir ../installz
    $ cd ../installz
    $ wget -O grib_api-1.17.0-Source.tar.gz https://software.ecmwf.int/wiki/download/attachments/3473437/grib_api-1.17.0-Source.tar.gz?api=v2
    $ tar xf grib_api-1.17.0-Source.tar.gz
    $ mkdir grib_api-build
    $ mkdir grib_api-install
    $ cd grib_api-build
    $ cmake ../grib_api-1.17.0-Source -DCMAKE_INSTALL_PREFIX=$HOME/installz/grib_api-install
    $ make
    $ make install
    
    
Install pygrib
''''''''''''''
.. warning:: The pygrib installation is optional. Only install if you need :func:`~gridtogssha.hrrr_to_gssha.HRRRtoGSSHA`.

See: https://github.com/jswhit/pygrib

::

    $ cd .. 
    $ git clone https://github.com/jswhit/pygrib.git
    $ cd pygrib
    $ echo "[directories]" > setup.cfg
    $ echo "grib_api_dir = $HOME/installz/grib_api-install" >> setup.cfg
    $ source activate gssha
    (gssha)$ python setup.py build
    (gssha)$ python setup.py install


Windows
^^^^^^^

Download & Install Miniconda
''''''''''''''''''''''''''''

-  Go to: http://conda.pydata.org/miniconda.html
-  Download and run Windows Python 2 version installer
-  Install at
   C:\\Users\\YOUR_USERNAME\\Miniconda2
   or wherever you want
-  Make default python and export to path

Install all dependencies
''''''''''''''''''''''''

.. note:: pygrib is currently not available on Windows, so HRRRtoGSSHA will not work.

Open CMD terminal:

::

    > conda update --yes conda python
    > conda create --name rapid python=2
    > activate gssha
    (gssha)> conda install --yes nose numpy netCDF4 gdal pyproj python-dateutil psycopg2
    (gssha)> deactivate 
    > activate gssha




Main Installation
-----------------

To install GsshaPy use ``easy_install`` as follows::
	
	$ easy_install gsshapy
	
Alternatively, the source code is available on GitHub and can be 
downloaded and installed as follows::

	$ git clone https://github.com/CI-WATER/gsshapy.git
	$ cd gsshapy
     $ source activate gssha  
	(gssha)$ python setup.py install
	

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
