************
Introduction
************

**Last Updated:** July 30, 2014

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
	
	For more information about GSSHA please visit the `GSSHA website`_ 
	and the gsshawiki_ .

.. _GSSHA website: http://chl.erdc.usace.army.mil/gssha	
.. _gsshawiki: http://www.gsshawiki.com/Main_Page

Requirements
============

The spatial components of GsshaPy rely heavily on the PostGIS spatial extension for the PostgreSQL database. To work with
spatial data in GsshaPy you will need to use a PostgreSQL database with PostGIS 2.1 or greater enabled. In addition,
GsshaPy relies on a Python module called mapkit to generate visualizations. This will automatically be installed when
you install GsshaPy.

Installation
============

To install GsshaPy use ``easy_install`` as follows::
	
	$ easy_install gsshapy
	
Alternatively, the source code is available on bit bucket and can be 
downloaded and installed as follows::

	$ git clone git@bitbucket.org:swainn/gsshapy.git
	$ cd gsshapy/GSSHAPY
	$ python setup.py install
	
For Windows users, a Windows installer has been created. It can be
downloaded here_.

.. _here: https://bitbucket.org/swainn/gsshapy/src/48944590dcc5957d6e97bd80a95f03e0857a734f/GSSHAPY/dist/gsshapy-1.0.0.win-amd64.exe?at=master
	

License
=======

GsshaPy is released under the `BSD 2-Clause license`_.

.. _BSD 2-Clause license: https://bitbucket.org/swainn/gsshapy/raw/48944590dcc5957d6e97bd80a95f03e0857a734f/GSSHAPY/LICENSE.txt

.. raw:: html
	
	<div>
		<script src="https://bitbucket.org/swainn/gsshapy/src/48944590dcc5957d6e97bd80a95f03e0857a734f/GSSHAPY/LICENSE.txt?embed=t"></script>
	</div>
	
Source
======

The source code is available on bitbucket::
	
	$ git clone git@bitbucket.org:swainn/gsshapy.git

Author
======

Nathan Swain

NSF Grant
=========

GsshaPy was developed at Brigham Young University with support from the National 
Science Foundation (NSF) under Grant No. 1135482. GsshaPy is part of a larger effort
known as CI-Water_. The purpose of CI-Water is to develop cyber infrastructure for 
water resources decision support.

.. _CI-Water: http://ci-water.org/
