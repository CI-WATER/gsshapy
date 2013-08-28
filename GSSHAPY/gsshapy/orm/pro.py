'''
********************************************************************************
* Name: ProjectionFileModel
* Author: Nathan Swain
* Created On: August 2, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['ProjectionFile']

import os

from sqlalchemy import Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

class ProjectionFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    '''
    __tablename__ = 'pro_projection_files'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    
    # Value Columns
    projection = Column(String, nullable=False) #: STRING
    
    # Relationship Properites
    projectFile = relationship('ProjectFile', uselist=False, back_populates='projectionFile') #: RELATIONSHIP
    
    # File Properties
    EXTENSION = 'pro'
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
        
    def __repr__(self):
        return '<ProjectionFile: Projection=%s>' % (self.projection)
    
    def _read(self):
        '''
        Projection File Read from File Method
        '''
        
        # Open file and parse into a data structure
        with open(self.PATH, 'r') as f:
            self.projection = f.read()
        
    def _write(self, session, openFile):
        '''
        Projection File Write to File Method
        '''
        # Write lines
        openFile.write(self.projection)
        
    def _namePreprocessor(self, name):
        '''
        Preprocess Name Method
        '''
        if '_prj' not in name:
            name += '_prj'
        
        return name
