'''
********************************************************************************
* Name: RaserMapModel
* Author: Nathan Swain
* Created On: August 1, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['RasterMapFile']

import subprocess


import xml.etree.ElementTree as ET
import xml.dom.minidom

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from mapkit.sqlatypes import Raster
from mapkit.RasterLoader import RasterLoader

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

from mapkit.RasterConverter import RasterConverter

class RasterMapFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    '''
    __tablename__ = 'raster_maps'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id')) #: FK
    
    # Value Columns
    fileExtension = Column(String, nullable=False) #: STRING
    raster_text = Column(String) #: STRING
    raster = Column(Raster) #: RASTER
    
    # Relationship Properites
    projectFile = relationship('ProjectFile', back_populates='maps') #: RELATIONSHIP
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
        
    def __repr__(self):
        return '<RasterMap: FileExtension=%s>' % (self.fileExtension)
    
    def _read(self):
        '''
        Raster Map File Read from File Method
        '''
        # Assign file extension attribute to file object
        self.fileExtension = self.EXTENSION
        
        # Open file and read plain text into text field
        with open(self.PATH, 'r') as f:
            self.raster_text = f.read()
            
        if self.SPATIAL:
            # Get well known binary from the raster file using the MapKit RasterLoader
            wkbRaster = RasterLoader.rasterToWKB(self.PATH, str(self.SRID), '0', self.RASTER2PGSQL_PATH)
            self.raster = wkbRaster         
        
    def _write(self, session, openFile):
        '''
        Raster Map File Write to File Method
        '''
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
            
    def getAsKmlGrid(self, session, path, colorRamp=None, alpha=1.0):
        '''
        Get the raster in KML format
        '''
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
            
            with open(path, 'w') as f:
#                 pretty = xml.dom.minidom.parseString(kmlString)
#                 f.write(pretty.toprettyxml())
                f.write(kmlString)
            
            

