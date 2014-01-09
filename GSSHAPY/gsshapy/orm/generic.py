'''
********************************************************************************
* Name: ProjectionFileModel
* Author: Nathan Swain
* Created On: August 2, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['GenericFile']

import os

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, Binary
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

class GenericFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    For storing generic files or files that are not yet supported
    by the ORM. The files are stored as text.
    '''
    __tablename__ = 'gen_generic_files'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id')) #: FK
    
    # Value Columns
    text = Column(String) #: STRING
    binary = Column(Binary) #: BINARY
    name = Column(String, nullable=False) #: STRING
    fileExtension = Column(String, nullable=False) #: STRING
    
    # Relationship Properites
    projectFile = relationship('ProjectFile', back_populates='genericFiles') #: RELATIONSHIP
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
        
    def __repr__(self):
        return '<GenericFile: Projection=%s>' % (self.projection)
    
    def _read(self):
        '''
        Generic File Read from File Method
        '''
        # Persist name and extension of file
        self.name = self.NAME
        self.fileExtension = self.EXTENSION
        
        # Open file and parse into a data structure
        with open(self.PATH, 'r') as f:
            self.text = f.read()
        
    def _write(self, session, openFile):
        '''
        Projection File Write to File Method
        '''
        # Write lines
        openFile.write(self.text)
