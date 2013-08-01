'''
********************************************************************************
* Name: IndexMapModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['IndexMap',
           'Maps']

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase


class IndexMap(DeclarativeBase):
    """
    classdocs
    """
    __tablename__ = 'idx_index_maps'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    rasterMapID = Column(Integer, ForeignKey('raster_maps.id'))
    
    # Value Columns
    name = Column(String, nullable=False)
    
    # Relationship Properties
    mapTables = relationship('MapTable', back_populates='indexMap')
    indices = relationship('MTIndex', back_populates='indexMap')
    contaminants = relationship('MTContaminant', back_populates='indexMap')
    rasterMap = relationship('RasterMap', back_populates='indexMap')
    
    def __init__(self, name):
        '''
        Constructor
        '''
        self.name = name
        
    def __repr__(self):
        return '<IndexMap: Name=%s>' % (self.name)
    
class RasterMap(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'raster_maps'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    fileExtention = Column(String, nullable=False)
    raster = Column(String, nullable=False)
    
    # Relationship Properites
    indexMap = relationship('IndexMap', uselist=False, back_populates='rasterMap')
    
    def __init__(self, fileExtension, raster):
        self.fileExtention = fileExtension
        self.raster = raster
        
    def __repr__(self):
        return '<RasterMap: FileExtension=%s, Raster=%s>' % (self.fileExtention, self.raster)
    
    
    
    
    
    