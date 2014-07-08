"""
********************************************************************************
* Name: TimestampedRaster
* Author: Nathan Swain
* Created On: July 8, 2014
* Copyright: (c) Brigham Young University 2014
* License: BSD 2-Clause
********************************************************************************
"""

__all__ = ['TimestampedRaster']

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, Float
from sqlalchemy.orm import relationship

from mapkit.sqlatypes import Raster
from mapkit.RasterLoader import RasterLoader

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

from mapkit.RasterConverter import RasterConverter


class TimestampedRaster(DeclarativeBase, GsshaPyFileObjectBase):
    """
    File object for interfacing with WMS Gridded and Vector Datasets
    """
    __tablename__ = 'timestamped_rasters'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    datasetFileID = Column(Integer, ForeignKey('wms_dataset_files.id'))

    # Value Columns
    timeStep = Column(Integer)  #: INTEGER
    timestamp = Column(Float)  #: FLOAT
    rasterText = Column(String)  #: STRING
    raster = Column(Raster)  #: RASTER
    wmsRasterType = Column(Integer)  #: STRING

    # Relationship Properties
    wmsDataset = relationship('WMSDatasetFile', back_populates='rasters')

    # File Properties
    WMS_STATUS_TYPE = 0
    WMS_VALUE_TYPE = 1
    VALID_WMS_RASTER_TYPES = (WMS_STATUS_TYPE, WMS_VALUE_TYPE)

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def __repr__(self):
        if self.wmsRasterType == self.WMS_STATUS_TYPE:
            return '<TimestampedRaster: TimeStep=%s, Timestamp=%s, WMSRasterType=%s>' % (
                self.timeStep,
                self.timestamp,
                'status')

        elif self.wmsRasterType == self.WMS_VALUE_TYPE:
            return '<TimestampedRaster: TimeStep=%s, Timestamp=%s, WMSRasterType=%s>' % (
                self.timeStep,
                self.timestamp,
                'value')

        else:
            return '<TimestampedRaster: TimeStep=%s, Timestamp=%s, WMSRasterType=%s>' % (
                self.timeStep,
                self.timestamp,
                self.wmsRasterType)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, raster2pgsqlPath):
        """
        Raster Map File Read from File Method
        """
        # Assign file extension attribute to file object
        self.fileExtension = extension

        # Open file and read plain text into text field
        with open(path, 'r') as f:
            self.raster_text = f.read()

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
            openFile.write(self.raster_text)