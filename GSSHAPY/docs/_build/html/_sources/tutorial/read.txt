************************
Read Files to a Database
************************

**Last Updated:** August 23, 2013

This page will give an example of how GsshaPy can be used to read a GSSHA model file into an SQL 
database. We will read in the project file from the Park City model that you downloaded on the 
previous page.

Initiate GsshaPy Database
=========================

The first step is to create a database and populate it with all of the GsshaPy tables. For this
tutorial we will create an SQLite database. This can be done by using the ``init_sqlite_db()`` 
method. In a Python console execute the following commands::

	>>> from gsshapy.lib import db_tools as dbt
	>>> sqlalchemy_url = dbt.init_sqlite_db('/path/to/tutorial-data/db/gsshapy_parkcity.db')
	
This method creates the SQLite database  at the path specified and populates it with the GsshaPy 
tables returning an SQLAlchemy_ url. This url is used to create SQLAlchemy_ session objects for 
interacting with the database::
	
	>>> session = dbt.create_session(sqlalchemy_url)
	
Create a GsshaPy Object
=======================

We need to create an instance of the GsshaPy **ProjectFile** *file* class to be able to read the project
file into the database. Before we instantiate **ProjectFile** we need to define a few variables that 
will define our workspace. GsshaPy needs to know the directory and filename of the file that will 
be read into the database::
	
	>>> readDirectory = '/path/to/tutorial-data/directory'
	>>> filename = 'parkcity.prj'
	
Now we can create an instance of **ProjectFile**::

	>>> from gsshapy.orm import ProjectFile
	>>> projectFile = ProjectFile(directory=readDirectory, filename=filename, session=session)
	
Read the File into the Database
===============================

The newly created **ProjectFile** object, ``projectFile``, has all the necessary information it needs to find
the file, parse it, and read it into the database. This can be done by invoking the ``read()``
method on ``projectFile``::

	>>> projectFile.read()
	
.. _SQLAlchemy: http://www.sqlalchemy.org/