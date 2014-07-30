***************************
Write Files from a Database
***************************

**Last Updated:** July 30, 2014

Reading GSSHA files is only half the story. GsshaPy is also able read a GsshaPy database and write the data back to the
proper file formats. It is necessary to write the data back to the original file format to be able to execute the GSSHA
simulation after modifying some input file in the database.

Retrieve Object from Database
=============================

Like reading to the database, we need and instance of a :class:`gsshapy.orm.ProjectFile` class to call the ``write()``
method on. When writing, the **ProjectFile** instance is created by querying the database for the project file we wish
to write. Issue the following command in the Python prompt::

	>>> newProjectFile = session.query(ProjectFile).first()
	
The query instantiates the new project file object with the data from the database query.

Write to File
=============

Now we call the ``write()`` method on the new instance of :class:`gsshapy.orm.ProjectFile`, ``newProjectFile``. This
method requires three arguments: an SQLAlchemy session object, a directory to write to, and the name you wish the file
to be saved as. Define these attributes and call the write method as follows::

	>>> writeDirectory = '/path_to/tutorial-data/write'
	>>> name = 'mymodel'
	>>> newProjectFile.write(session=session, directory=writeDirectory, name=name)
	
.. _SQLAlchemy: http://www.sqlalchemy.org/

If all has gone well, you will find a copy of the project file in the **write** directory. If you compare the
file with the original you will notice some differences. Notice that most of the path prefixes have been changed
to match the name of the project file. This is a GSSHA convention that is preserved by GsshaPy. If you change only the
project file using GsshaPy, be sure it is written out with the same name as the original. Paths are stored as relative
in the GsshaPy database. Consequently, all the paths will be written out again as relative paths.

.. tip::

    If you need to prepend a directory to the paths in the project file, use the ``appendDirectory()`` method of a
    :class:`gsshapy.orm.ProjectFile` object.