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

import xml.etree.ElementTree as ET
import xml.dom.minidom

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from mapkit.sqlatypes import Raster
from mapkit.RasterLoader import RasterLoader
from mapkit.RasterConverter import RasterConverter

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

class IndexMap(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    '''
    __tablename__ = 'idx_index_maps'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    mapTableFileID = Column(Integer, ForeignKey('cmt_map_table_files.id')) #: FK
    
    # Value Columns
    srid = Column(Integer) #: SRID
    name = Column(String, nullable=False) #: STRING
    filename = Column(String, nullable=False) #: STRING
    raster_text = Column(String) #: STRING
    raster = Column(Raster) #: RASTER
    
    # Relationship Properties
    mapTableFile = relationship('MapTableFile', back_populates='indexMaps') #: RELATIONSHIP
    mapTables = relationship('MapTable', back_populates='indexMap') #: RELATIONSHIP
    indices = relationship('MTIndex', back_populates='indexMap') #: RELATIONSHIP
    contaminants = relationship('MTContaminant', back_populates='indexMap') #: RELATIONSHIP
    
    # File Properties
    EXTENSION = 'idx'
    
    def __init__(self, directory, filename, session, name=None):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
        self.name = name
        self.filename = filename
        
    def __repr__(self):
        return '<IndexMap: Name=%s, Filename=%s, Raster=%s>' % (self.name, self.filename, self.raster)
    
    def __eq__(self, other):
        return (self.name == other.name and
                self.filename == other.filename and
                self.raster == other.raster)
    
    def _read(self):
        '''
        Index Map Read from File Method
        '''
        # Open file and read plain raster_text into raster_text field
        with open(self.PATH, 'r') as f:
            self.raster_text = f.read()
                
        if self.SPATIAL:
            # Assign file extension attribute to file object
            self.fileExtension = self.EXTENSION
            
            # Get well known binary from the raster file using the MapKit RasterLoader
            wkbRaster = RasterLoader.rasterToWKB(self.PATH, str(self.SRID), '-1', self.RASTER2PGSQL_PATH)
            self.raster = wkbRaster
        
    def write(self, directory, name=None, session=None):
        '''
        Index Map Write to File Method
        '''
        
        # Initiate file
        if name !=None:
            filename = '%s.%s' % (name, self.EXTENSION)
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
                mapFile.write(self.raster_text)

    def getAsKmlGrid(self, session, path, colorRamp=None, alpha=1.0):
        '''
        Get the raster in KML format
        '''
          
        if type(self.raster) != type(None):
            # Make sure the raster field is valid
            converter = RasterConverter(sqlAlchemySession=session)
            
            # Configure color ramp
            converter.setColorRamp(colorRamp)
            
            kmlString = converter.getAsKmlGrid(tableName=self.tableName,
                                               rasterId=self.id,
                                               rasterIdFieldName='id',
                                               documentName=self.filename,
                                               alpha=alpha)
            
            with open(path, 'w') as f:
#                 pretty = xml.dom.minidom.parseString(kmlString)
#                 f.write(pretty.toprettyxml())
                f.write(kmlString)
                
            

    

    
    
    
    
    
    