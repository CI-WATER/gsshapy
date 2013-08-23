************************************
Read and Write Entire GSSHA Projects
************************************

**Last Updated:** August 16, 2013

Each of the GSSHA model files can be read or written in the same manner that was illustrated. 
The **ProjectFile** class also has methods that can be used to read and write an entire 
GSSHA project.

Read All Files
==============

Create a new database and session for this part of the tutorial::

	>>> from gsshapy.lib import db_tools as dbt
	>>> sqlalchemy_url = dbt.init_sqlite_db('/path/to/tutorial-data/db/gsshapy_parkcity_all.db')
	>>> all_session = dbt.create_session(sqlalchemy_url)
	
Instantiate a new **ProjectFile** object::

	>>> from gsshapy.orm import ProjectFile
	>>> readDirectory = '/path/to/tutorial-data/directory'
	>>> filename = 'parkcity.prj'
	>>> projectFileAll = ProjectFile(directory=readDirectory, filename=filename, session=all_session)
	
Invoke the ``readProject()`` method to read all supported GSSHA input and output files into the 
database::

	>>> projectFileAll.readProject()
	
There **ProjectFile** has two other methods that can be used to read only input files or only output
files: ``readInput()`` and ``readOutput``, respectively.


Write All Files
===============

Now that all of the files have been read into the database, we can write them back out to file. Retrieve
the project file from the database and invoke the ``writeProject()`` method::

	>>> projectFileAll1 = all_session.query(ProjectFile).filter(ProjectFile.id == 1).one()
	>>> writeDirectory = '/path/to/tutorial-data/directory/write'
	>>> name = 'mymodel'
	>>> projectFileAll1.writeProject(session=all_session, directory=writeDirectory, newName=name)
	
All of the files that were read into the database should be written to file in the *write* directory
of the tutorial files. For the files that use the project name prefix as filename convention, the prefix
has been changed to match the name supplied by the user. Like the read methods, there are two other write
methods that can be used to write only the input files or only the output files: ``writeInput()`` and 
``writeOutput()``, respectively.

.. warning::
	
	Not all GSSHA files are supported in GsshaPy. Unsupported files may need to be added manually to the 
	write directory for the GSSHA model to execute properly. In this case the name parameter of the write
	method must be the same as the orignial project name. Refer to :doc:`../support` for a list of all the 
	GSSHA files that are supported with this release of GsshaPy. 