"""
********************************************************************************
* Name: WMSDataset
* Author: Nathan Swain
* Created On: July 8, 2014
* Copyright: (c) Brigham Young University 2014
* License: BSD 2-Clause
********************************************************************************
"""

__all__ = ['WMSDatasetFile']

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase
from gsshapy.lib import parsetools as pt, wms_dataset_chunk as wdc


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
    rasters = relationship('TimestampedRaster', back_populates='wmsDataset')  #: RELATIONSHIP

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

        # Dictionary of keywords/cards and parse function names
        KEYWORDS = {'DATASET': wdc.datasetHeaderChunk,
                    'TS': wdc.datasetTimeStepChunk}

        # Open file and read plain text into text field
        with open(path, 'r') as f:
            chunks = pt.chunk(KEYWORDS, f)

        datasetChunk = {'header': [],
                        'timesteps': []}

        for key, chunkList in chunks.iteritems():
            # Parse each chunk in the chunk list
            for chunk in chunkList:
                # Call chunk specific parsers for each chunk
                result = KEYWORDS[key](key, chunk)

                if key == 'DATASET':
                    datasetChunk['header'] = result

                elif key == 'TS':
                    tempTimeSteps = datasetChunk['timesteps']
                    tempTimeSteps.append(result)
                    datasetChunk['timesteps'] = tempTimeSteps

        self._createGsshaPyObjects(datasetChunk)

        # Add current file object to the session
        session.add(self)


    def _write(self, session, openFile):
        """
        WMS Dataset File Write to File Method
        """

    def _createGsshaPyObjects(self, datasetChunk):
        """
        Assemble the GSSHAPY Objects
        """
        self.name = datasetChunk['header']['name']
        self.numberCells = datasetChunk['header']['numberCells']
        self.numberData = datasetChunk['header']['numberData']
        self.objectID = datasetChunk['header']['objectID']

        if datasetChunk['header']['type'] == 'BEGSCL':
            self.objectType = datasetChunk['header']['objectType']
            self.type = self.SCALAR_TYPE

        elif datasetChunk['header']['type'] == 'BEGVEC':
            self.vectorType = datasetChunk
            self.type = self.VECTOR_TYPE


