"""
********************************************************************************
* Name: IndexMapModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from __future__ import unicode_literals

__all__ = ['IndexMap']

import os

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, Float
from sqlalchemy.orm import relationship
from mapkit.sqlatypes import Raster
from mapkit.RasterLoader import RasterLoader
from mapkit.RasterConverter import RasterConverter

from . import DeclarativeBase
from ..base.file_base import GsshaPyFileObjectBase
from ..base.rast import RasterObjectBase


class IndexMap(DeclarativeBase, GsshaPyFileObjectBase, RasterObjectBase):
    """
    Object interface for Index Map Files.

    GSSHA uses GRASS ASCII rasters to store spatially distributed parameters. Index maps are stored using a different
    object than other raster maps, because they are closely tied to the mapping table file objects and they are stored
    with different metadata than the other raster maps. Index maps are declared in the mapping table file.

    The values for each cell in an index map are integer indices that correspond with the indexes of the mapping tables
    that reference the index map. Many different hydrological parameters are distributed spatially in this manner. The
    result is that far fewer maps are needed to parametrize a GSSHA model.

    If the spatial option is enabled when the rasters are read in, the rasters will be read in as PostGIS raster
    objects. There are no supporting objects for index map file objects.

    This object inherits several methods from the :class:`gsshapy.orm.RasterObjectBase` base class for generating raster
    visualizations.

    See: http://www.gsshawiki.com/Mapping_Table:Index_Maps
    """
    __tablename__ = 'idx_index_maps'

    # Public Table Metadata
    tableName = __tablename__  #: Database tablename
    rasterColumnName = 'raster'  #: Raster column name
    defaultNoDataValue = -1  #: Default no data value
    discreet = True  #: Index maps should be discreet

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
    name = Column(String)  #: STRING
    filename = Column(String)  #: STRING
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
        self.rasterText = None

    def __repr__(self):
        return '<IndexMap: Name=%s, Filename=%s, Raster=%s>' % (self.name, self.filename, self.raster)

    def __eq__(self, other):
        return (self.name == other.name and
                self.filename == other.filename and
                self.raster == other.raster)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
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
            wkbRaster = RasterLoader.grassAsciiRasterToWKB(session=session,
                                                           grassRasterPath=path,
                                                           srid=str(spatialReferenceID),
                                                           noData='-1')
            self.raster = wkbRaster
            self.srid = spatialReferenceID

        # Assign other properties
        self.filename = filename

    def write(self, directory, name=None, session=None, replaceParamFile=None):
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
            if self.rasterText is not None:
                # Open file and write, raster_text only
                with open(filePath, 'w') as mapFile:
                    mapFile.write(self.rasterText)
