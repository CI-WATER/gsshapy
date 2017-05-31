************************
Read Files to a Database
************************

**Last Updated:** July 30, 2014

This page will provide an example of how GsshaPy can be used to read single a GSSHA model file into an SQL database. We
will read in the project file from the Park City model that you downloaded on the previous page.

Initiate GsshaPy Database
=========================

The first step is to create a database and populate it with all of the GsshaPy tables. 
The database tools API for creating databases is located here: :doc:`../api/lib/db-tools`
   
For this tutorial you will need to create a new database in a PostgreSQL database and
enable the PostGIS extension. This can be done by following the instructions on the
PostGIS website: http://postgis.net/docs/manual-2.1/postgis_installation.html#create_new_db_extensions .

Create a database user with password and a PostGIS enabled database with the following credentials:

* Username: gsshapy
* Password: pass
* Database: gsshapy_tutorial

Open a Python console and execute the following commands to populate the database with GsshaPy tables::

    >>> from gsshapy.lib import db_tools as dbt
    >>> sqlalchemy_url = dbt.init_postgresql_db(username='gsshapy', host='localhost', database='gsshapy_tutorial', port='5432', password='pass')

This method returns an SQLAlchemy_ url. This url is used to create SQLAlchemy_ session objects for interacting with the
database. In the Python console::

    >>> session_maker = dbt.get_sessionmaker(sqlalchemy_url)
    >>> session = session_maker()

Create a GsshaPy Object
=======================

We need to create an instance of the GsshaPy **ProjectFile** file class to be able to read the project
file into the database. In the python console, import the **ProjectFile** file class and instantiate it
to create new **ProjectFile** object::

    >>> from gsshapy.orm import ProjectFile
    >>> projectFile = ProjectFile()

Read the File into the Database
===============================

Next, define a few variables that will define the directory where the files are located and the name of the project file.
Be sure to enter the path to where you unzipped the tutorial data as the directory variable. Invoke the ``read()`` method
on ``projectFile`` to read the contents of the file into the database::

    >>> readDirectory = '/path_to/tutorial-data'
    >>> filename = 'parkcity.prj'
    >>> projectFile.read(directory=readDirectory, filename=filename, session=session)

The contents of the project file has now been read into the database. The next tutorial will illustrate how you can
query the data in the database using the GsshaPy objects.

Inspect Supporting Objects
==========================

As was mentioned in the introduction, GsshaPy file objects are often supported by other supporting objects. In the case
of the project file, there is only one supporting object called :class:`gsshapy.orm.ProjectCard`. The project file
consists of a set of key value pairs called cards. Each card is stored using one of these project card objects. When you
executed the ``read()`` method, it created an instance of :class:`gsshapy.orm.ProjectCard` for each project card in the
project file. These project file objects are accessible via the ``projectCards`` property of the project file object. To
illustrate this concept, execute the following lines in the Python console::

    >>> projectCards = projectFile.projectCards
    >>> for card in projectCards:
    ...     print card
    ...

    <ProjectCard: Name=WMS, Value=WMS 9.1 (64-Bit)>
    <ProjectCard: Name=WATERSHED_MASK, Value="parkcity.msk">
    <ProjectCard: Name=PROJECT_PATH, Value="">
    <ProjectCard: Name=#LandSoil, Value="parkcity.lsf">
    <ProjectCard: Name=#PROJECTION_FILE, Value="parkcity_prj.pro">
    <ProjectCard: Name=NON_ORTHO_CHANNELS, Value=None>
    <ProjectCard: Name=FLINE, Value="parkcity.map">
    <ProjectCard: Name=METRIC, Value=None>
    <ProjectCard: Name=GRIDSIZE, Value=90.000000>
    <ProjectCard: Name=ROWS, Value=72>
    <ProjectCard: Name=COLS, Value=67>
    ...........

Each project card object is summarized similar to the sampling above. You can access the card name and value using the
properties of the project card::

    >>> for card in projectCards:
    ...     print card.name, card.value
    ...

    WMS WMS 9.1 (64-Bit)
    WATERSHED_MASK "parkcity.msk"
    PROJECT_PATH ""
    #LandSoil "parkcity.lsf"
    #PROJECTION_FILE "parkcity_prj.pro"
    NON_ORTHO_CHANNELS None
    FLINE "parkcity.map"
    METRIC None
    GRIDSIZE 90.000000
    ROWS 72
    COLS 67
    ..........

GsshaPy eliminates the need for you to manually parse the file. Instead, you can work with each file using an object
oriented approach. Behind the scenes, SQLAlchemy issues queries to the database tables to populate objects with data.
This will be illustrated more concretely in the next tutorial.

.. _SQLAlchemy: http://www.sqlalchemy.org/