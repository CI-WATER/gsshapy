"""
********************************************************************************
* Name: RaserMapModel
* Author: Nathan Swain
* Created On: August 1, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from __future__ import unicode_literals

__all__ = ['RasterMapFile']

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, Float
from sqlalchemy.orm import relationship
from mapkit.sqlatypes import Raster
from mapkit.RasterLoader import RasterLoader
from mapkit.RasterConverter import RasterConverter

from . import DeclarativeBase
from ..base.file_base import GsshaPyFileObjectBase
from ..base.rast import RasterObjectBase


class RasterMapFile(DeclarativeBase, GsshaPyFileObjectBase, RasterObjectBase):
    """
    Object interface for Raster Map type files.

    GSSHA uses GRASS ASCII rasters to store spatially distributed parameters. Rasters that are not index maps are stored
    using this object. Index maps are stored separately, because they are closely tied to the mapping table file objects
    and they are stored with different metadata than the other raster maps.

    Raster maps are declared in the project file. Examples of cards that require raster maps are ELEVATION, ROUGHNESS
    WATERSHED_MASK, WATER_TABLE, and MOISTURE. Many of these map inputs are mutually exclusive with the mapping tables
    for the same variable.

    If the spatial option is enabled when the rasters are read in, the rasters will be read in as PostGIS raster
    objects. There are no supporting objects for raster map file objects.

    This object inherits several methods from the :class:`gsshapy.orm.RasterObjectBase` base class for generating raster
    visualizations.

    See: http://www.gsshawiki.com/Project_File:Project_File
    """
    __tablename__ = 'raster_maps'

    # Public Table Metadata
    tableName = __tablename__  #: Database tablename
    rasterColumnName = 'raster'  #: Raster column name
    defaultNoDataValue = 0  #: Default no data value

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
    filename = Column(String)  #: STRING

    # Relationship Properties
    projectFile = relationship('ProjectFile', back_populates='maps')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def __repr__(self):
        return '<RasterMap: FileExtension=%s>' % self.fileExtension

    def _delete_existing(self, project_file, session):
        """
        This will delete existing instances with the same extension
        """
        # remove existing grid if exists
        existing_elev = session.query(RasterMapFile).\
                                      filter(RasterMapFile.projectFile == project_file).\
                                      filter(RasterMapFile.fileExtension == self.fileExtension).\
                                      all()
        if existing_elev:
            session.delete(existing_elev)
            session.commit()

    def _load_raster_text(self, raster_path):
        """
        Loads grass ASCII to object
        """
        # Open file and read plain text into text field
        with open(raster_path, 'r') as f:
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

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
        """
        Raster Map File Read from File Method
        """
        # Assign file extension attribute to file object
        self.fileExtension = extension
        self.filename = filename

        self._load_raster_text(path)
        
        if spatial:
            # Get well known binary from the raster file using the MapKit RasterLoader
            wkbRaster = RasterLoader.grassAsciiRasterToWKB(session=session,
                                                           grassRasterPath=path,
                                                           srid=str(spatialReferenceID),
                                                           noData='0')
            self.raster = wkbRaster

    def _write(self, session, openFile, replaceParamFile):
        """
        Raster Map File Write to File Method
        """
        # If the raster field is not empty, write from this field
        if self.raster is not None:
            # Configure RasterConverter
            converter = RasterConverter(session)

            # Use MapKit RasterConverter to retrieve the raster as a GRASS ASCII Grid
            grassAsciiGrid = converter.getAsGrassAsciiRaster(rasterFieldName='raster',
                                                             tableName=self.__tablename__,
                                                             rasterIdFieldName='id',
                                                             rasterId=self.id)
            # Write to file
            openFile.write(grassAsciiGrid)

        elif self.rasterText is not None:
            # Write file
            openFile.write(self.rasterText)

    def write(self, session, directory, name, replaceParamFile=None, **kwargs):
        """
        Wrapper for GsshaPyFileObjectBase write method 
        """
        if self.raster is not None or self.rasterText is not None:
            super(RasterMapFile, self).write(session, directory, name, replaceParamFile, **kwargs)