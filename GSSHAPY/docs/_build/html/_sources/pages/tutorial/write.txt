***************************
Write Files from a Database
***************************

**Last Updated:** August 15, 2013

Reading GSSHA files is only half the story. GsshaPy is also able to read a GsshaPy database and export the
data back to the proper file format. 

Retrieve Object from Database
=============================

Like reading to the database, we need and instance of a **ProjectFile**
class to call the ``write()`` method on. When writing, the **ProjectFile** instance is created by querying
the database for the project file we wish to write::

	>>> projectFile1 = session.query(ProjectFile).filter(ProjectFile.id == 1).one()
	
The query instantiates **ProjectFile** with the data from the database.

Write to File
=============

Now we call the ``write()`` method on the new instance of **ProjectFile**, ``projectFile1``. This method 
requires three arguments: an SQLAlchemy session object, a directory to write to, and the name you wish
the project to be saved as. Define these attributes and call the write method as follows::

	>>> writeDirectory = '/path/to/tutorial-data/directory/write'
	>>> name = 'mymodel'
	>>> projectFile1.write(session=session, directory=writeDirectory, name=name)
	
.. _SQLAlchemy: http://www.sqlalchemy.org/

If all has gone well, you will find a copy of the project file in the *write* directory. If you compare the 
file with the original you will notice some differences. Notice that most of the path prefixes have been changed
to match the name of the project file. This is a GSSHA convention. If you change the only project file using 
GsshaPy, be sure it is written out with the same name as the original. The **ProjectFile** ``read()`` method 
stores paths as relative paths in the database. Thus, all the paths will be written out again as relative paths.