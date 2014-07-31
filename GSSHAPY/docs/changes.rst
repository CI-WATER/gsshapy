**********************
Changes in Version 2.0
**********************

**Last Updated:** July 30, 2014

The release of GsshaPy 2.0.0 constitutes many changes which will be summarized here. Changes vary from minor bug fixes
to completely new file objects for files not previously supported. Several non-reverse compatible changes were also made
to make using GsshaPy more convenient. The following list covers the major changes:


New File Objects
================

GsshaPy now includes a file object for WMS Dataset files. WMS Dataset files are used to output timeseries raster data.
Adding support for this file means that GsshaPy now supports almost all of the available outputs.


New Base Objects
================

Two new base objects are now included in GsshaPy including the :class:`gsshapy.base.RasterObjectBase` and the
:class:`gsshapy.base.GeometricObjectBase`. These objects provide methods for generating visualizations for objects
that have either a raster or geometry field. For example, the :class:`gsshapy.orm.IndexMap` and
:class:`gsshapy.orm.RasterMapFile` objects now inherit from :class:`gsshapy.base.RasterObjectBase` to provide their
visualization methods.

.. Note::
    The "getAsKml" methods have been moved from the :class:`gsshapy.orm.IndexMap` and :class:`gsshapy.orm.RasterMapFile`
    to the :class:`gsshapy.base.RasterObjectBase` to avoid duplicating code in multiple places. Both map classes now
    inherit these KML visualization methods from the :class:`gsshapy.base.RasterObjectBase`.


Improved Visualization Methods
==============================

The ``getAsKmlPng()`` method was improved to include a methodology for resampling the raster prior to image generation.
This allows you to generate images that have a higher resolution than the GSSHA model grid. This results in a clean
polished look as opposed to the fuzzy look that was typical of these types of visualizations. See the documentation for
the :class:`gsshapy.base.RasterObjectBase` for an explanation of this new functionality.


New Spatial Methods
===================

GsshaPy 2.0.0 introduces many new methods for generating KML visualizations including animations for times series
spatial datasets. Several method are also included for extracting geometry in Well Known Text and GeoJSON formats. See
the API documentation for each object to learn how to use each method.

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


Changes to How Files are Read
=============================

The biggest non-reverse compatible change that was made involves the way that files are read into the database. In 2.0.0,
it is no longer necessary (or possible) to pass the read parameters into the constructor for the file object. Instead,
these parameters are passed into the ``read()`` method when it is called. See the illustration below:

**Prior to 2.0.0**::

    >>> projectFile = ProjectFile(directory=readDirectory, filename=filename, session=session)
    >>> projectFile.read()

**After 2.0.0**::

    >>> projectFile = ProjectFile()
    >>> projectFile.read(directory=readDirectory, filename=filename, session=session)

This change makes it easier to work with the file objects and is more consistent with how the ``write()`` method works.


Other Non-Reverse Compatible Changes
====================================

There were other fine tuning changes that were made that may break your code. Not all changes will be listed but here is
what to watch out for:

* A limited number of method argument names were changed (e.g.: in the :class:`gsshapy.orm.ProjectFile` ``readProject()`` method the ``filename`` parameter was changed to ``projectFileName``).
* The order of the arguments in some existing methods were rearranged.


Bug Fixes
=========

Several bugs were addressed during the development of GsshaPy 2.0.0. Several examples are listed here, though not all:

* The spatial reference ID was not being persisted in the database as intended, now it is.
* GsshaPy would throw an error during reading when it encountered a file listed in the project file that did not exist in the GSSHA project files. GsshaPy will now skip the file and issue a warning, but it will not crash. The same issue was addressed for the file write phase.
* An error would occur during writing of the map table file, because it's file extension property was named 'extension' instead of 'fileExtension'. All file extension properties were reviewed and renamed 'fileExtension' and the problem was eliminated.


Expanded Documentation
======================

The documentation was reviewed and updated for the new version. This included a revamp of the API documentation (which was
fairly useless before). Now API documentation includes in-depth explanations of all public methods and shows the
inheritance. This also includes a short explanation of each class.

The tutorial was updated and expanded to show more examples of working with GsshaPy and the new spatial methods. Finally,
and quite obviously, a new section was added to document the changes that were made in version 2.0.0.

Enjoy!








