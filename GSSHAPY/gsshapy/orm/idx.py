'''
********************************************************************************
* Name: IndexMapModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['IndexMap']

import os

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, Float
from sqlalchemy.orm import relationship

from mapkit.sqlatypes import Raster
from mapkit.RasterLoader import RasterLoader
from mapkit.RasterConverter import RasterConverter

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase
from gsshapy.orm.rast import RasterObject


class IndexMap(DeclarativeBase, GsshaPyFileObjectBase, RasterObject):
    """
    """
    __tablename__ = 'idx_index_maps'

    # Public Table Metadata
    tableName = __tablename__  #: Database tablename
    rasterColumnName = 'raster'
    defaultNoDataValue = -1

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    mapTableFileID = Column(Integer, ForeignKey('cmt_map_table_files.id'))  #: FK

    # Value Columns
    north = Column(Float)  #: FLOAT
    south = Column(Float)  #: FLOAT
    east = Column(Float)  #: FLOAT
    west = Column(Float)  #: FLOAT
    rows = Column(Integer)  #: INTEGER
    columns = Column(Integer)  #: INTEGER
    srid = Column(Integer)  #: SRID
    name = Column(String, nullable=False)  #: STRING
    filename = Column(String, nullable=False)  #: STRING
    rasterText = Column(String)  #: STRING
    raster = Column(Raster)  #: RASTER
    fileExtension = Column(String, default='idx')  #: STRING

    # Relationship Properties
    mapTableFile = relationship('MapTableFile', back_populates='indexMaps')  #: RELATIONSHIP
    mapTables = relationship('MapTable', back_populates='indexMap')  #: RELATIONSHIP
    indices = relationship('MTIndex', back_populates='indexMap')  #: RELATIONSHIP
    contaminants = relationship('MTContaminant', back_populates='indexMap')  #: RELATIONSHIP

    def __init__(self, name=None):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)
        self.name = name

    def __repr__(self):
        return '<IndexMap: Name=%s, Filename=%s, Raster=%s>' % (self.name, self.filename, self.raster)

    def __eq__(self, other):
        return (self.name == other.name and
                self.filename == other.filename and
                self.raster == other.raster)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, raster2pgsqlPath):
        """
        Index Map Read from File Method
        """
        # Set file extension property
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
            wkbRaster = RasterLoader.rasterToWKB(path, str(spatialReferenceID), '-1', raster2pgsqlPath)
            self.raster = wkbRaster
            self.srid = spatialReferenceID

        # Assign other properties
        self.filename = filename

    def write(self, directory, name=None, session=None):
        """
        Index Map Write to File Method
        """

        # Initiate file
        if name != None:
            filename = '%s.%s' % (name, self.fileExtension)
            filePath = os.path.join(directory, filename)
        else:
            filePath = os.path.join(directory, self.filename)

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
            with open(filePath, 'w') as mapFile:
                mapFile.write(grassAsciiGrid)

        else:
            # Open file and write, raster_text only
            with open(filePath, 'w') as mapFile:
                mapFile.write(self.rasterText)
