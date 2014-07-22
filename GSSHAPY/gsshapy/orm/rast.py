"""
********************************************************************************
* Name: RasterObject
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


class RasterObject:
    """
    Abstract base class for raster objects
    """

    # These properties must be defined in the class that implements this ABC
    tableName = None           # Name of the table to which the raster column belongs
    id = None                  # ID of the record containing the raster column
    rasterColumnName = None    # Name of the raster column
    filename = None            # Default name given to KML document
    raster = None              # Raster column
    defaultNoDataValue = 0     # Set the default no data value

    def getAsKmlGrid(self, session, path=None, colorRamp=ColorRampEnum.COLOR_RAMP_HUE, documentName=None,
                     alpha=1.0, noDataValue=None):
        """
        Get the raster in KML format
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
                                               noDataValue=noDataValue)

            if path:
                with open(path, 'w') as f:
                    f.write(kmlString)

            return kmlString

    def getAsKmlClusters(self, session, path=None, colorRamp=ColorRampEnum.COLOR_RAMP_HUE, documentName = None,
                         alpha=1.0, noDataValue=None):
        """
        Get the raster in a clustered KML format
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
                                                   noDataValue=noDataValue)

            if path:
                with open(path, 'w') as f:
                    f.write(kmlString)

            return kmlString

    def getAsKmlPng(self, session, path=None, colorRamp=ColorRampEnum.COLOR_RAMP_HUE, documentName=None, alpha=1.0,
                    drawOrder=0, noDataValue=None, cellSize=None, resampleMethod='NearestNeighbour'):
        """
        Get the raster in a PNG / KML format
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
                                                               resampleMethod=resampleMethod)

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
        Get the raster in the Grass Ascii Grid format
        """
        if type(self.raster) != type(None):
            # Make sure the raster field is valid
            converter = RasterConverter(sqlAlchemyEngineOrSession=session)

            return converter.getAsGrassAsciiRaster(tableName=self.tableName,
                                                   rasterIdFieldName='id',
                                                   rasterId=self.id,
                                                   rasterFieldName=self.rasterColumnName)