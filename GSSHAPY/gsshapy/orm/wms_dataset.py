"""
********************************************************************************
* Name: WMSDataset
* Author: Nathan Swain
* Created On: July 8, 2014
* Copyright: (c) Brigham Young University 2014
* License: BSD 2-Clause
********************************************************************************
"""

__all__ = ['WMSDatasetFile', 'WMSDatasetRaster']

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, Float
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase
from gsshapy.lib import parsetools as pt, wms_dataset_chunk as wdc

from mapkit.RasterLoader import RasterLoader
from mapkit.sqlatypes import Raster


class WMSDatasetFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    File object for interfacing with WMS Gridded and Vector Datasets
    """
    __tablename__ = 'wms_dataset_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))  #: FK

    # Value Columns
    type = Column(Integer)  #: INTEGER
    fileExtension = Column(String, default='txt')  #: STRING
    objectType = Column(String)  #: STRING
    vectorType = Column(String)  #: STRING
    objectID = Column(Integer)  #: INTEGER
    numberData = Column(Integer)  #: INTEGER
    numberCells = Column(Integer)  #: INTEGER
    name = Column(String)  #: STRING

    # Relationship Properties
    projectFile = relationship('ProjectFile', back_populates='wmsDatasets')  #: RELATIONSHIP
    rasters = relationship('WMSDatasetRaster', back_populates='wmsDataset')  #: RELATIONSHIP

    # File Properties
    SCALAR_TYPE = 1
    VECTOR_TYPE = 0
    VALID_DATASET_TYPES = (VECTOR_TYPE, SCALAR_TYPE)

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def __repr__(self):
        if self.type == self.SCALAR_TYPE:
            return '<WMSDatasetFile: Name=%s, Type=%s, objectType=%s, objectID=%s, numberData=%s, numberCells=%s, FileExtension=%s>' % (
                self.name,
                'scalar',
                self.objectType,
                self.objectID,
                self.numberData,
                self.numberCells,
                self.fileExtension)

        elif self.type == self.VECTOR_TYPE:
            return '<WMSDatasetFile: Name=%s, Type=%s, vectorType=%s, objectID=%s, numberData=%s, numberCells=%s, FileExtension=%s>' % (
                self.name,
                'vector',
                self.vectorType,
                self.objectID,
                self.numberData,
                self.numberCells,
                self.fileExtension)
        else:
            return '<WMSDatasetFile: Name=%s, Type=%s, objectType=%s, vectorType=%s, objectID=%s, numberData=%s, numberCells=%s, FileExtension=%s>' % (
                self.name,
                self.type,
                self.objectType,
                self.vectorType,
                self.objectID,
                self.numberData,
                self.numberCells,
                self.fileExtension)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, raster2pgsqlPath):
        """
        WMS Dataset File Read from File Method
        """
        # Assign file extension attribute to file object
        self.fileExtension = extension

        # Vars from project file
        columns = 67
        rows = 72
        gridsize = 90.0000

        # Vars from the mask map (a raster that will always be in a GSSHA project)
        west = 454318.29
        north = 4501028.97

        # Dictionary of keywords/cards and parse function names
        KEYWORDS = {'DATASET': wdc.datasetHeaderChunk,
                    'TS': wdc.datasetScalarTimeStepChunk}

        # Open file and read plain text into text field
        with open(path, 'r') as f:
            chunks = pt.chunk(KEYWORDS, f)

        # Parse header chunk first
        header = wdc.datasetHeaderChunk('DATASET', chunks['DATASET'][0])

        # Parse each time step chunk and aggregate
        timeStepRasters = []

        for chunk in chunks['TS']:
            timeStepRasters.append(wdc.datasetScalarTimeStepChunk(chunk, columns, header['numberData'], header['numberCells']))

        # Set WMS dataset file properties
        self.name = header['name']
        self.numberCells = header['numberCells']
        self.numberData = header['numberData']
        self.objectID = header['objectID']

        if header['type'] == 'BEGSCL':
            self.objectType = header['objectType']
            self.type = self.SCALAR_TYPE

        elif header['type'] == 'BEGVEC':
            self.vectorType = header['objectType']
            self.type = self.VECTOR_TYPE

        # Create WMS raster dataset files for each raster
        for timeStep, timeStepRaster in enumerate(timeStepRasters):
            # Create new WMS raster dataset file object
            wmsRasterDatasetFile = WMSDatasetRaster()

            # Set the wms dataset for this WMS raster dataset file
            wmsRasterDatasetFile.wmsDataset = self

            # Set the time step and timestamp and other properties
            wmsRasterDatasetFile.iStatus = timeStepRaster['iStatus']
            wmsRasterDatasetFile.timestamp = timeStepRaster['timestamp']
            wmsRasterDatasetFile.timeStep = timeStep + 1

            # If spatial is enabled create PostGIS rasters
            if spatial:
                # Process the values/cell array
                wmsRasterDatasetFile.valueRaster = RasterLoader.makeSingleBandWKBRaster(session, columns, rows, west, north, gridsize, gridsize, 0, 0, spatialReferenceID, timeStepRaster['cellArray'])

                # Only process the status arrays if not empty
                if timeStepRaster['dataArray'] is not None:
                    wmsRasterDatasetFile.statusRaster = RasterLoader.makeSingleBandWKBRaster(session, columns, rows, west, north, gridsize, gridsize, 0, 0, spatialReferenceID, timeStepRaster['dataArray'])

            # Otherwise, set the raster text properties
            else:
                wmsRasterDatasetFile.statusRasterText = ''
                wmsRasterDatasetFile.valueRasterText = ''


        # Add current file object to the session
        session.add(self)

    def _write(self, session, openFile):
        """
        WMS Dataset File Write to File Method
        """


class WMSDatasetRaster(DeclarativeBase):
    """
    File object for interfacing with WMS Gridded and Vector Datasets
    """
    __tablename__ = 'wms_dataset_rasters'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    datasetFileID = Column(Integer, ForeignKey('wms_dataset_files.id'))

    # Value Columns
    timeStep = Column(Integer)  #: INTEGER
    timestamp = Column(Float)  #: FLOAT
    iStatus = Column(Integer)  #: INTEGER
    statusRasterText = Column(String)  #: STRING
    valueRasterText = Column(String)  #: STRING
    statusRaster = Column(Raster)  #: RASTER
    valueRaster = Column(Raster)  #: RASTER

    # Relationship Properties
    wmsDataset = relationship('WMSDatasetFile', back_populates='rasters')

    def __init__(self):
        """
        Constructor
        """

    def __repr__(self):
        return '<TimestampedRaster: TimeStep=%s, Timestamp=%s>' % (
            self.timeStep,
            self.timestamp)