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

import os

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

class RasterMapFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    classdocs
    '''
    __tablename__ = 'raster_maps'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))
    
    # Value Columns
    fileExtension = Column(String, nullable=False)
    raster = Column(String, nullable=False)
    
    # Relationship Properites
    projectFile = relationship('ProjectFile', back_populates='maps')
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
        
    def __repr__(self):
        return '<RasterMap: FileExtension=%s, Raster=%s>' % (self.fileExtension, self.raster)
    
    def _readWithoutCommit(self):
        '''
        Raster Map File Read from File Method
        '''
        # Assign file extension attribute to file object
        self.fileExtension = self.EXTENSION
        
        # Open file and parse into a data structure
        with open(self.PATH, 'r') as f:
            self.raster = f.read()
        
    def _writeToOpenFile(self, session, openFile):
        '''
        Raster Map File Write to File Method
        '''
        # Write file
        openFile.write(self.raster)

