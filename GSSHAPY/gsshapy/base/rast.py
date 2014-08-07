"""
********************************************************************************
* Name: RasterObjectBase
* Author: Nathan Swain
* Created On: July 22, 2014
* Copyright: (c) Brigham Young University 2014
* License: BSD 2-Clause
********************************************************************************
"""

import os
from zipfile import ZipFile

from mapkit.ColorRampGenerator import ColorRampEnum
from mapkit.RasterConverter import RasterConverter

__all__ = ['RasterObjectBase']

class RasterObjectBase:
    """
    Abstract base class for raster objects.
    """

    # These properties must be defined in the class that implements this ABC
    tableName = None           # Name of the table to which the raster column belongs
    id = None                  # ID of the record containing the raster column
    rasterColumnName = None    # Name of the raster column
    filename = None            # Default name given to KML document
    raster = None              # Raster column
    defaultNoDataValue = 0     # Set the default no data value
    discreet = False           # Whether rasters typically have discreet values or not

    def getAsKmlGrid(self, session, path=None, documentName=None, colorRamp=ColorRampEnum.COLOR_RAMP_HUE, alpha=1.0,
                     noDataValue=None):
        """
        Retrieve the raster as a KML document with each cell of the raster represented as a vector polygon. The result
        is a vector grid of raster cells. Cells with the no data value are excluded.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database.
            path (str, optional): Path to file where KML file will be written. Defaults to None.
            documentName (str, optional): Name of the KML document. This will be the name that appears in the legend.
                Defaults to 'Stream Network'.
            colorRamp (:mod:`mapkit.ColorRampGenerator.ColorRampEnum` or dict, optional): Use ColorRampEnum to select a
                default color ramp or a dictionary with keys 'colors' and 'interpolatedPoints' to specify a custom color
                ramp. The 'colors' key must be a list of RGB integer tuples (e.g.: (255, 0, 0)) and the
                'interpolatedPoints' must be an integer representing the number of points to interpolate between each
                color given in the colors list.
            alpha (float, optional): Set transparency of visualization. Value between 0.0 and 1.0 where 1.0 is 100%
                opaque and 0.0 is 100% transparent. Defaults to 1.0.
            noDataValue (float, optional): The value to treat as no data when generating visualizations of rasters.
                Defaults to 0.0.

        Returns:
            str: KML string
        """
        if type(self.raster) != type(None):
            # Set Document Name
            if documentName is None:
                try:
                    documentName = self.filename
                except AttributeError:
                    documentName = 'default'

            # Set no data value to default
            if noDataValue is None:
                noDataValue = self.defaultNoDataValue

            # Make sure the raster field is valid
            converter = RasterConverter(sqlAlchemyEngineOrSession=session)

            # Configure color ramp
            if isinstance(colorRamp, dict):
                converter.setCustomColorRamp(colorRamp['colors'], colorRamp['interpolatedPoints'])
            else:
                converter.setDefaultColorRamp(colorRamp)

            kmlString = converter.getAsKmlGrid(tableName=self.tableName,
                                               rasterId=self.id,
                                               rasterIdFieldName='id',
                                               rasterFieldName=self.rasterColumnName,
                                               documentName=documentName,
                                               alpha=alpha,
                                               noDataValue=noDataValue,
                                               discreet=self.discreet)

            if path:
                with open(path, 'w') as f:
                    f.write(kmlString)

            return kmlString

    def getAsKmlClusters(self, session, path=None, documentName=None, colorRamp=ColorRampEnum.COLOR_RAMP_HUE, alpha=1.0,
                         noDataValue=None):
        """
        Retrieve the raster as a KML document with adjacent cells with the same value aggregated into vector polygons.
        The result is a vector representation cells clustered together. Cells with the no data value are excluded.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database.
            path (str, optional): Path to file where KML file will be written. Defaults to None.
            documentName (str, optional): Name of the KML document. This will be the name that appears in the legend.
                Defaults to 'Stream Network'.
            colorRamp (:mod:`mapkit.ColorRampGenerator.ColorRampEnum` or dict, optional): Use ColorRampEnum to select a
                default color ramp or a dictionary with keys 'colors' and 'interpolatedPoints' to specify a custom color
                ramp. The 'colors' key must be a list of RGB integer tuples (e.g.: (255, 0, 0)) and the
                'interpolatedPoints' must be an integer representing the number of points to interpolate between each
                color given in the colors list.
            alpha (float, optional): Set transparency of visualization. Value between 0.0 and 1.0 where 1.0 is 100%
                opaque and 0.0 is 100% transparent. Defaults to 1.0.
            noDataValue (float, optional): The value to treat as no data when generating visualizations of rasters.
                Defaults to 0.0.

        Returns:
            str: KML string
        """
        if type(self.raster) != type(None):
            # Set Document Name
            if documentName is None:
                try:
                    documentName = self.filename
                except AttributeError:
                    documentName = 'default'

            # Set no data value to default
            if noDataValue is None:
                noDataValue = self.defaultNoDataValue

            # Make sure the raster field is valid
            converter = RasterConverter(sqlAlchemyEngineOrSession=session)

            # Configure color ramp
            if isinstance(colorRamp, dict):
                converter.setCustomColorRamp(colorRamp['colors'], colorRamp['interpolatedPoints'])
            else:
                converter.setDefaultColorRamp(colorRamp)

            kmlString = converter.getAsKmlClusters(tableName=self.tableName,
                                                   rasterId=self.id,
                                                   rasterIdFieldName='id',
                                                   rasterFieldName=self.rasterColumnName,
                                                   documentName=documentName,
                                                   alpha=alpha,
                                                   noDataValue=noDataValue,
                                                   discreet=self.discreet)

            if path:
                with open(path, 'w') as f:
                    f.write(kmlString)

            return kmlString

    def getAsKmlPng(self, session, path=None, documentName=None, colorRamp=ColorRampEnum.COLOR_RAMP_HUE, alpha=1.0,
                    noDataValue=None, drawOrder=0, cellSize=None, resampleMethod='NearestNeighbour'):
        """
        Retrieve the raster as a PNG image ground overlay KML format. Coarse grid resolutions must be resampled to
        smaller cell/pixel sizes to avoid a "fuzzy" look. Cells with the no data value are excluded.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database.
            path (str, optional): Path to file where KML file will be written. Defaults to None.
            documentName (str, optional): Name of the KML document. This will be the name that appears in the legend.
                Defaults to 'Stream Network'.
            colorRamp (:mod:`mapkit.ColorRampGenerator.ColorRampEnum` or dict, optional): Use ColorRampEnum to select a
                default color ramp or a dictionary with keys 'colors' and 'interpolatedPoints' to specify a custom color
                ramp. The 'colors' key must be a list of RGB integer tuples (e.g.: (255, 0, 0)) and the
                'interpolatedPoints' must be an integer representing the number of points to interpolate between each
                color given in the colors list.
            alpha (float, optional): Set transparency of visualization. Value between 0.0 and 1.0 where 1.0 is 100%
                opaque and 0.0 is 100% transparent. Defaults to 1.0.
            noDataValue (float, optional): The value to treat as no data when generating visualizations of rasters.
                Defaults to 0.0.
            drawOrder (int, optional): Set the draw order of the images. Defaults to 0.
            cellSize (float, optional): Define the cell size in the units of the project projection at which to resample
                the raster to generate the PNG. Defaults to None which will cause the PNG to be generated with the
                original raster cell size. It is generally better to set this to a size smaller than the original cell
                size to obtain a higher resolution image. However, computation time increases exponentially as the cell
                size is decreased.
            resampleMethod (str, optional): If cellSize is set, this method will be used to resample the raster. Valid
                values include: NearestNeighbour, Bilinear, Cubic, CubicSpline, and Lanczos. Defaults to
                NearestNeighbour.

        Returns:
            (str, list): Returns a KML string and a list of binary strings that are the PNG images.
        """
        if type(self.raster) != type(None):
            # Set Document Name
            if documentName is None:
                try:
                    documentName = self.filename
                except AttributeError:
                    documentName = 'default'

            # Set no data value to default
            if noDataValue is None:
                noDataValue = self.defaultNoDataValue

            # Make sure the raster field is valid
            converter = RasterConverter(sqlAlchemyEngineOrSession=session)

            # Configure color ramp
            if isinstance(colorRamp, dict):
                converter.setCustomColorRamp(colorRamp['colors'], colorRamp['interpolatedPoints'])
            else:
                converter.setDefaultColorRamp(colorRamp)

            kmlString, binaryPngString = converter.getAsKmlPng(tableName=self.tableName,
                                                               rasterId=self.id,
                                                               rasterIdFieldName='id',
                                                               rasterFieldName=self.rasterColumnName,
                                                               documentName=documentName,
                                                               alpha=alpha,
                                                               drawOrder=drawOrder,
                                                               noDataValue=noDataValue,
                                                               cellSize=cellSize,
                                                               resampleMethod=resampleMethod,
                                                               discreet=self.discreet)
            if path:
                directory = os.path.dirname(path)
                archiveName = (os.path.split(path)[1]).split('.')[0]
                kmzPath = os.path.join(directory, (archiveName + '.kmz'))

                with ZipFile(kmzPath, 'w') as kmz:
                    kmz.writestr(archiveName + '.kml', kmlString)
                    kmz.writestr('raster.png', binaryPngString)

            return kmlString, binaryPngString

    def getAsGrassAsciiGrid(self, session):
        """
        Retrieve the raster in the GRASS ASCII Grid format.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database.

        Returns:
            str: GRASS ASCII string.
        """
        if type(self.raster) != type(None):
            # Make sure the raster field is valid
            converter = RasterConverter(sqlAlchemyEngineOrSession=session)

            return converter.getAsGrassAsciiRaster(tableName=self.tableName,
                                                   rasterIdFieldName='id',
                                                   rasterId=self.id,
                                                   rasterFieldName=self.rasterColumnName)