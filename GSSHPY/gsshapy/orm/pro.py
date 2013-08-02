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

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase

class ProjectionFile(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'pro_projection_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    projection = Column(String, nullable=False)
    
    # Relationship Properites
    projectFile = relationship('ProjectFile', uselist=False, back_populates='projectionFile')
    
    # Global Properties
    PATH = ''
    FILENAME = ''
    DIRECTORY = ''
    SESSION = None
    EXTENSION = ''
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        self.FILENAME = filename # e.g.: example.ext
        self.DIRECTORY = directory # e.g.: /path/to/my/example
        self.SESSION = session # SQL Alchemy Session object
        self.PATH = '%s%s' % (self.DIRECTORY, self.FILENAME) # e.g.: /path/to/my/example/example.ext
        self.EXTENSION = filename.split('.')[1]
        
    def __repr__(self):
        return '<ProjectionFile: Projection=%s>' % (self.projection)
    
    def read(self):
        '''
        Projection File Read from File Method
        '''
        
        # Open file and parse into a data structure
        with open(self.PATH, 'r') as f:
            self.projection = f.read()
        
    def write(self, directory, session, filename):
        '''
        Projection File Write to File Method
        '''
        # Initiate file
        filePath = '%s%s' % (directory, filename)

        # Open file and write
        with open(filePath, 'w') as mapFile:
            mapFile.write(self.projection)
