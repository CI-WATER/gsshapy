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
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase


class IndexMap(DeclarativeBase, GsshaPyFileObjectBase):
    """
    classdocs
    """
    __tablename__ = 'idx_index_maps'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    mapTableFileID = Column(Integer, ForeignKey('cmt_map_table_files.id'))
    
    # Value Columns
    name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    raster = Column(String)
    
    # Relationship Properties
    mapTableFile = relationship('MapTableFile', back_populates='indexMaps')
    mapTables = relationship('MapTable', back_populates='indexMap')
    indices = relationship('MTIndex', back_populates='indexMap')
    contaminants = relationship('MTContaminant', back_populates='indexMap')
    
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
    
    def _readWithoutCommit(self):
        '''
        Index Map Read from File Method
        '''
        # Open file and parse into a data structure
        with open(self.PATH, 'r') as f:
            self.raster = f.read()
        
#         print 'File Read:', self.filename
        
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

        # Open file and write
        with open(filePath, 'w') as mapFile:
            mapFile.write(self.raster)
            
#         print 'File Written:', self.filename
        
    

    
    
    
    
    
    