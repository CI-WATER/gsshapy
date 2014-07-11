"""
********************************************************************************
* Name: RaserMapModel
* Author: Nathan Swain
* Created On: August 1, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

__all__ = ['RasterMapFile']

from zipfile import ZipFile
import os

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, Float
from sqlalchemy.orm import relationship

from mapkit.sqlatypes import Raster
from mapkit.RasterLoader import RasterLoader

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

from mapkit.RasterConverter import RasterConverter


class RasterMapFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    """
    __tablename__ = 'raster_maps'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))  #: FK

    # Value Columns
    north = Column(Float)  #: FLOAT
    south = Column(Float)  #: FLOAT
    east = Column(Float)  #: FLOAT
    west = Column(Float)  #: FLOAT
    rows = Column(Integer)  #: INTEGER
    columns = Column(Integer)  #: INTEGER
    fileExtension = Column(String, default='txt')  #: STRING
    rasterText = Column(String)  #: STRING
    raster = Column(Raster)  #: RASTER

    # Relationship Properties
    projectFile = relationship('ProjectFile', back_populates='maps')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def __repr__(self):
        return '<RasterMap: FileExtension=%s>' % self.fileExtension

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, raster2pgsqlPath):
        """
        Raster Map File Read from File Method
        """
        # Assign file extension attribute to file object
        self.fileExtension = extension

        # Open file and read plain text into text field
        with open(path, 'r') as f:
            self.rasterText = f.read()

        # Retrieve metadata from header
        lines = self.rasterText.split('\n')
        for line in lines[0:6]:
            spline = line.split()

            if 'north' in spline[0].lower():
                self.north = float(spline[1])
            elif 'south' in spline[0].lower():
                self.south = float(spline[1])
            elif 'east' in spline[0].lower():
                self.east = float(spline[1])
            elif 'west' in spline[0].lower():
                self.west = float(spline[1])
            elif 'rows' in spline[0].lower():
                self.rows = int(spline[1])
            elif 'cols' in spline[0].lower():
                self.columns = int(spline[1])

        if spatial:
            # Get well known binary from the raster file using the MapKit RasterLoader
            wkbRaster = RasterLoader.rasterToWKB(path, str(spatialReferenceID), '0', raster2pgsqlPath)
            self.raster = wkbRaster

    def _write(self, session, openFile):
        """
        Raster Map File Write to File Method
        """
        # If the raster field is not empty, write from this field
        if type(self.raster) != type(None):
            # Configure RasterConverter
            converter = RasterConverter(session)

            # Use MapKit RasterConverter to retrieve the raster as a GRASS ASCII Grid
            grassAsciiGrid = converter.getAsGrassAsciiRaster(rasterFieldName='raster',
                                                             tableName=self.__tablename__,
                                                             rasterIdFieldName='id',
                                                             rasterId=self.id)
            # Write to file
            openFile.write(grassAsciiGrid)

        else:
            # Write file
            openFile.write(self.rasterText)

    def getAsKmlGrid(self, session, path=None, colorRamp=None, alpha=1.0):
        """
        Get the raster in KML format
        """
        if type(self.raster) != type(None):
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
                                               documentName=self.fileExtension,
                                               alpha=alpha)

            if path:
                with open(path, 'w') as f:
                    f.write(kmlString)

            return kmlString

    def getAsKmlClusters(self, session, path=None, colorRamp=None, alpha=1.0):
        """
        Get the raster in a clustered KML format
        """
        if type(self.raster) != type(None):
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
                                                   documentName=self.fileExtension,
                                                   alpha=alpha)

            if path:
                with open(path, 'w') as f:
                    f.write(kmlString)

            return kmlString

    def getAsKmlPng(self, session, path=None, colorRamp=None, alpha=1.0, drawOrder=0):
        """
        Get the raster in a PNG / KML format
        """
        if type(self.raster) != type(None):
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
                                                               documentName=self.fileExtension,
                                                               alpha=alpha,
                                                               drawOrder=drawOrder)

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
                                                   rasterId=self.id)

