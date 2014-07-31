**********************
Work with Spatial Data
**********************

**Last Updated:** July 31, 2014

Up to this point in the tutorial, you have not been using the spatial functionality in GsshaPy. This is where most of the
progress occurred in version 2.0. In this tutorial you will learn how to read a project using spatial database objects.
This means that instead of storing the points, lines, polygons, and rasters as plain text, they will be stored using the
spatial field types provided by PostGIS (raster and geometry). Once stored in PostGIS spatial fields, the data is exposed
to over 1000 spatial database functions that can be used in queries to convert the data to different formats (e.g.: KML,
WKT, GeoJSON, PNG), transform the coordinate reference system, and perform geoprocessing tasks (e.g.: buffer, intersect,
union).

Spatial Project Read
====================

To read the GSSHA files into spatial fields in the database we setup as we did before, creating a session and an
instance of the :class:`gsshapy.orm.ProjectFile` class::

    >>> from gsshapy.lib import db_tools as dbt
    >>> sqlalchemy_url = dbt.sqlalchemy_url = dbt.init_postgresql_db(username='gsshapy', host='localhost', database='gsshapy_tutorial', port='5432', password='pass')
    >>> spatial_session = dbt.create_session(sqlalchemy_url)
    >>> from gsshapy.orm import ProjectFile
    >>> spatialProjectFile = ProjectFile()

Then we call the ``readProject()`` method on the project file object, this time with a few new arguments. We
enable spatial objects by setting the ``spatial`` argument to ``True``. Then we define the spatial reference system
for the model by giving it the spatial reference ID (see: http://spatialreference.org). For Park City this is 26912,
determined based on the projection file. Finally, we pass in the path to the ``raster2pgsql`` commandline program that
ships with PostGIS. Invoking the ``readProject()`` method looks like this::

    >>> readDirectory = '/path_to/tutorial-data'
    >>> filename = 'parkcity.prj'
    >>> spatial = True
    >>> srid = 26912
    >>> raster2pgsql_path = '/path_to/raster2pgsql'
    >>> spatialProjectFile.readProject(directory=readDirectory, projectFileName=filename, session=spatial_session, spatial=spatial, spatialReferenceID=srid, raster2pgsqlPath=raster2pgsql_path)

You should notice that reading the project into the database using spatial objects takes a little more time than when
reading it without spatial objects. This delay is caused primarily by the conversion of the native GSSHA spatial formats
to the PostGIS spatial formats. For example, GSSHA stores raster files in GRASS ASCII format while PostGIS stores rasters
in the binary version of the Well Known Text format (Well Known Binary).

Spatial Read for Individual Files
---------------------------------

You can also apply the spatial read methodology to individual files. Instantiate the file object for the file you wish
to read into the database with spatial objects and call the ``read()`` method with the same spatial arguments as
illustrated above. For example, let's read in the mask map file. The file object that is used to read in the mask map is
the :class:`gsshapy.orm.RasterMapFile` object (use the :doc:`Supported Files <../support>` page to determine what objects
are used for what files). Create a new instance of this object and invoke the ``read()`` method with the same
arguments as above, but pointing it instead at the mask map file (:file:`parkcity.msk`)::

    >>> from gsshapy.orm import RasterMapFile
    >>> maskMap = RasterMapFile()
    >>> filename = 'parkcity.msk'
    >>> maskMap.read(directory=readDirectory, filename=filename, session=spatial_session, spatial=spatial, spatialReferenceID=srid, raster2pgsqlPath=raster2pgsql_path)

.. Note::
    Not all files have spatial data, so passing in the spatial arguments to the read methods of these objects has no
    effect on the reading process. Refer to the :doc:`API Documentation <../api>` for a file object to determine if
    it supports spatial objects.

Spatial Project Write
=====================

There is no change needed to write a project that has been read in spatially. Use the same write methods as illustrated
in the previous tutorial. This will not be demonstrated here.

Spatial Visualizations
======================

After a project or file object has been read into the database with spatial objects, it is exposed to a number of spatial
methods that can be used to generate visualizations of the data in various formats.

To demonstrate how these methods can be used to generate spatial visualizations, we will use the ``getModelSummaryAsKml()``
method of the :class:`gsshapy.orm.ProjectFile`. This method uses the mask map and the stream network to generate a
summary visualization of the GSSHA model. Define the path where you want to write the kml file to. Then, query the
database for the project file that was read in as part of the spatial reading (id = 3 if you have been following the
tutorial) and invoke the ``getModelSummaryAsKml()`` method on it::

    >>> from gsshapy.orm import ProjectFile
    >>> import os
    >>> kml_path = os.path.join(writeDirectory, 'model_summary.kml')
    >>> newSpatialProjectFile = spatial_session.query(ProjectFile).filter(ProjectFile.id == 3).one()
    >>> newSpatialProjectFile.getModelSummaryAsKml(session=spatial_session, path=kml_path)

You will find the :file:`model_summary.kml` file in your **write** directory. If you have the
`Google Earth Desktop <http://www.google.com/earth/explore/products/desktop.html>`_ application, you can view the
visualization. KML can also be loaded into the Google Maps and Google Earth web viewers to embed it in a website.
You can experiment with the other spatial methods to understand how they work. Refer to the :doc:`API Documentation <../api>`
for details in how to use each method.

Spatial Methods Available
-------------------------

File objects that include spatial methods include:

:class:`gsshapy.orm.WMSDatasetFile`:

* getAsKmlGridAnimation()
* getAsKmlPngAnimation()


:class:`gsshapy.orm.ChannelInputFile`:

* streamNetworkAsKml()
* streamNetworkAsWkt()
* streamNetworkAsGeoJson()

:class:`gsshapy.orm.LinkNodeDatasetFile`:

* getAsKmlAnimation()

:class:`gsshapy.orm.ProjectFile`:

* getModelSummaryAsKml()
* getModelSummaryAsWkt()
* getModelSummaryAsGeoJson()

The :class:`gsshapy.base.GeometricObjectBase` offers several general purpose methods for objects that inherit from
it:

* getAsKml()
* getAsWkt()
* getAsGeoJson()
* getSpatialReferenceId()

The :class:`gsshapy.base.RasterObjectBase` offers several general purpose methods for objects that inherit from it:

* getAsKmlGrid()
* getAsKmlClusters()
* getAsKmlPng()
* getAsGrassAsciiGrid()