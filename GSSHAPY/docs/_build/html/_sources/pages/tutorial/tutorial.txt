***************
Getting Started
***************

**Last Updated:** August 15, 2013

This tutorial is provided to help you get started using GsshaPy. In this tutorial you will
learn important GsshaPy concepts and how to:

.. toctree::
	:maxdepth: 1
	
	read
	query
	write
	project
	
The full tutorial script can be downloaded here:
:download:`tutorial-script.py <tutorial-data/tutorial-script.py>`

Requirements
============

Download the example GSSHA model files here:
:download:`tutorial-data.zip <tutorial-data/tutorial-data.zip>`.

Unzip the contents of the file. This file will become the working directory 
for the tutorial. The *write* and *db* directories are purposely left empty.

The tutorial uses an SQLite database. Ensure that you have SQLite installed 
on your system. Visit the `SQLite webpage`_ for download and installation
instructions. Windows users ensure that the sqlite executable is added to
your path.

.. warning::

	GSSHAPY was only tested with SQLite3.

Key Concepts
============

The key abstraction of GsshaPy is the GSSHA model file. Most GSSHA model files are 
text files and many of them use a card system for assigning model parameters. Some 
of the files are GRASS ASCII maps and some of the data in other files is spatial
in nature (though not in a standard format like a shp file).

The files that are supported are represented represented in GsshaPy by classes. There
are two types of classes that have been defined in GsshaPy: *file* classes and 
*table* classes. All of the *file* classes inherit from a base *file* class called
``GsshaPyFileObjectBase``. This class defines the ``read()`` and ``write()`` methods 
that are used to read the file into an SQL database. 

Most *file* classes are supported with one or more *table* classes. Both the *file* 
classes and their supporting *table* classes inherit from the SQLAlchemy_ 
*declarative base* class. *Declarative base* maps each class to a table in the database,
among other things. The properties of the *file* and *table* classes define the columns 
and relationships of the tables in the database. Instances of these classes represent
records in these tables. 

In most cases, a mojority of the information in each file is stored in the database tables 
associated with the supporting *table* classes. The *file* class ``read()`` and ``write()``
methods orchastrate the reading and writing of data using the supporting *table* classes.

.. seealso::

	For an explanation of the SQLAlchemy ORM see http://docs.sqlalchemy.org/en/rel_0_8/orm/tutorial.html. 
	If you are not familiar with SQLAlchemy_, it strongly recommended that you follow this tutorial 
	before you continue, because GsshaPy relies heavily on SQLAlchemy_ ORM concepts.

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _SQLite webpage: http://www.sqlite.org/




