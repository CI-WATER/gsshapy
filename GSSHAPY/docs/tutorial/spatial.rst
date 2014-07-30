**********************
Work with Spatial Data
**********************

**Last Updated:** July 31, 2014

Up to this point in the tutorial, we have not been using the spatial functionality in GsshaPy. This is where most of the
progress occurred in version 2.0. In this tutorial we will learn how to read in a project using spatial database objects.
Then we will use several methods of GsshaPy to generate KML visualizations from these spatially enabled attributes.

Spatial Project Read
====================

To read the GSSHA files into spatial fields in the database we setup as we did before, creating a session and an
instance of the :class:`gsshapy.orm.ProjectFile` class::

    >>> from gsshapy.lib import db_tools as dbt
    >>> sqlalchemy_url = dbt.sqlalchemy_url = dbt.init_postgresql_db(username='gsshapy', host='localhost', database='gsshapy_tutorial', port='5432', password='pass')
    >>> spatial_session = dbt.create_session(sqlalchemy_url)
    >>> from gsshapy.orm import ProjectFile
    >>> spatialProjectFile = ProjectFile()

Then we call the ``readProject()`` method on the project file instance, this time with a few new arguments. First, we
enable spatial objects by setting the ``spatial`` argument to ``True``. Then we define the spatial reference system
for the model by giving it the spatial reference ID (see: http://spatialreference.org). For Park City this is 26912,
determined based on the projection file. Finally, pass in the path to the ``raster2pgsql`` commandline program that
ships with PostGIS. Invoking the ``readProject()`` method looks like this::

    >>> readDirectory = '/path_to/tutorial-data'
    >>> filename = 'parkcity.prj'
    >>> spatial = True
    >>> srid = 26912
    >>> raster2pgsql_path = '/path_to/raster2pgsql'
    >>> projectFileAll.readProject(directory=readDirectory, projectFileName=filename, session=all_session, spatial=spatial, spatialReferenceID=srid, raster2pgsqlPath=raster2pgsql_path)

You should notice that reading the project into the database using spatial objects takes a little more time than when
reading it without spatial objects. This delay is caused primarily by the conversion of the rasters from GRASS ASCII
rasters that are GSSHA's default raster format to PostGIS raster format. This is done by the ``raster2pgsql`` program
which GsshaPy makes use of.

This same process applies to reading individual files in with spatial attributes. Instantiate the file object for the file
and call the ``read()`` method with the same spatial arguments as illustrated above.

.. Note::
    Not all files have spatial data, so passing in the spatial arguments to the read methods of these objects has no
    effect on the reading process.

Spatial Project Write
=====================

There is no change needed to write a project that has been read in spatially. Use the same write methods as illustrated
in the previous tutorial. These will not be demonstrated here.

Spatial Visualizations
======================

