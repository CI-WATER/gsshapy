************************************
Read and Write Entire GSSHA Projects
************************************

**Last Updated:** July 30, 2014

Each of the GSSHA model files can be read or written in the same manner that was illustrated with the project file. Each
has a ``read()`` and a ``write()`` method. However, the :class:`gsshapy.orm.ProjectFile` class has several additional
methods that can be used to read and write all or some of the GSSHA model files simultaneously. These methods are:

* readProject()
* readInput()
* readOutput()
* writeProject()
* writeInput()
* wrtieOutput()

The names are fairly self explanatory, but more detailed explanations are provided in the API documentation for the
:class:`gsshapy.orm.ProjectFile` class. In this tutorial we will learn how to read an entire project and write it
back to file.

Read All Files
==============

Create a new session for this part of the tutorial, but use the same database::

    >>> from gsshapy.lib import db_tools as dbt
    >>> sqlalchemy_url = dbt.sqlalchemy_url = dbt.init_postgresql_db(username='gsshapy', host='localhost', database='gsshapy_tutorial', port='5432', password='pass')
    >>> session_maker = dbt.get_sessionmaker(sqlalchemy_url)
    >>> all_session = session_maker()

Instantiate a new :class:`gsshapy.orm.ProjectFile` object::

    >>> from gsshapy.orm import ProjectFile
    >>> projectFileAll = ProjectFile()

Invoke the ``readProject()`` method to read all supported GSSHA input and output files into the 
database::

    >>> readDirectory = '/path_to/tutorial-data'
    >>> filename = 'parkcity.prj'
    >>> projectFileAll.readProject(directory=readDirectory, projectFileName=filename, session=all_session)

The process of reading all the files into the database takes a moment, so be patient. The ``readInput()`` and ``readOutput``
methods can be used to read only input files or output files, respectively. If the task you are using GsshaPy for is
related to pre-processing the input files, you may want to use the ``readInput()`` method to save a little time on
overhead. Similarly, if the task you are performing is related to post-processing the output files you may find the
``readOutput()`` method useful.

If you feel adventurous, you could use **psql** or PGAdminIII to investigate the database. Many of the tables will now
be populated with data.

Write All Files
===============

Now that all of the files have been read into the database, we can write them back out to file. Retrieve
the project file from the database and invoke the ``writeProject()`` method::

    >>> newProjectFileAll = all_session.query(ProjectFile).filter(ProjectFile.id == 2).one()
    >>> writeDirectory = '/path_to/tutorial-data/write'
    >>> name = 'mymodel'
    >>> newProjectFileAll.writeProject(session=all_session, directory=writeDirectory, name=name)

.. note::

    We filter our query using the project file id of 2, because this is the second project file we have read in during
    this set of tutorials. If you end up reading in several projects, you can easily change this to another id to
    retrieve the GSSHA project you desire.

All of the files that were read into the database should be written to file in the *write* directory of the tutorial
files. For the files that use the project name prefix as filename convention, the prefix has been changed to match the
name supplied by the user ('mymodel' if you followed the tutorial exactly). Like the read methods, there are two other
write methods that can be used to write only the input files or only the output files: ``writeInput()`` and
``writeOutput()``, respectively. Use ``writeInput()`` when you want to write the model out to execute a simulation.