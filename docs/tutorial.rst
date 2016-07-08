***************
Getting Started
***************

**Last Updated:** July 30, 2014

This tutorial is provided to help you get started using GsshaPy. In this tutorial you will learn important GsshaPy
concepts and how to:

.. toctree::
	:maxdepth: 1
	
	tutorial/read
	tutorial/query
	tutorial/write
	tutorial/project
	tutorial/spatial

The full tutorial script can be downloaded here:
:download:`tutorial-script.py <tutorial/tutorial-data/tutorial-script.py>`

Requirements
============

Download the example GSSHA model files here:
:download:`tutorial-data.zip <tutorial/tutorial-data/tutorial-data.zip>`.

Unzip the contents of the file into a safe location. This file will become the working directory for the tutorial.
The *write* directory is purposely empty. The other files in this directory make up the input and output files for a
GSSHA model of the Park City, Utah watershed.

This tutorial makes use of a PostGIS enabled PostgreSQL database. GsshaPy uses the PostGIS to store spatial features
of the models and it uses several PostGIS database functions to generate the spatial visualizations. To learn how to
install PostGIS, visit their website: http://postgis.net/documentation . If you are using a Mac, an excellent option for
easily testing with PostGIS is the Postgres App: http://postgresapp.com/ .

After installing PostgreSQL with PostGIS, create a database called "gsshapy_tutorial" and enable the PostGIS extension
on the database. Refer to the documentation on the PostGIS docs for how this is to be done. Managing roles and databases
is made much simpler using the PGAdminIII graphical user interface for PostgreSQL. You can find PGAdminIII here:
http://www.pgadmin.org/ .

The tutorial also requires that you are using some version of Python 2.7. GsshaPy has not ported to Python 3 at this
time.

Summary of Requirements
-----------------------

* Tutorial Files: :download:`tutorial-data.zip <tutorial/tutorial-data/tutorial-data.zip>`
* GsshaPy 2.0+
* PostgreSQL 9.3+
* PostGIS 2.1+
* Python 2.7.x

Key Concepts
============

The key abstraction of GsshaPy are the GSSHA model files. Most GSSHA model files are text files and many of them use a
card system for assigning model parameters. Some of the files are GRASS ASCII maps and some of the data in other files
are spatial in nature (e.g.: Link node and WMS datasets).

File Objects
------------

Each file is represented in GsshaPy by an object. The file objects are defined by classes that inherit from the
:class:`gsshapy.base.file_base.GsshaPyFileObjectBase`. This class defines the ``read()`` and ``write()`` methods
that are used by all file objects to read the file into an SQL database and write them back out to file.

Supporting Objects
------------------

Most file objects are supported with several supporting objects. The purpose of these objects is to provide the contents
of the files at a higher level abstraction to make them easier to work with. For example, the precipitation file is
decomposed into three other objects including an object representing precipitation events, another representing the rain
gages, and another object representing each value in the precipitation time series. This makes modifying and working with
precipitation files easier than worrying about individual lines in the text file.

Mapping Objects to Database Tables
----------------------------------

Both the file classes and supporting object classes inherit from from the SQLAlchemy_ ``declarative_base`` class. The
``declarative_base`` class maps each class to a table in the database, among other things. The properties of the file
and supporting classes define the columns and relationships of the corresponding tables in the database. Instances of
these classes, then,  represent individual records in the tables.

In most cases, a majority of the information in each file is stored in the database tables associated with the
supporting classes. The file class ``read()`` and ``write()`` methods orchestrate the reading of data into the database
and writing it back out by using the supporting classes.

.. seealso::

	For an explanation of the SQLAlchemy ORM see http://docs.sqlalchemy.org/en/rel_0_9/orm/tutorial.html .
	If you are not familiar with SQLAlchemy_, it strongly recommended that you follow this tutorial 
	before you continue, because GsshaPy relies heavily on SQLAlchemy_ ORM concepts.

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _SQLite webpage: http://www.sqlite.org/




