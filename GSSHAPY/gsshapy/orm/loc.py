'''
********************************************************************************
* Name: OutputLocationModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['OutputLocationFile',
           'OutputLocation']

import os

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

class OutputLocationFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    classdocs
    '''
    
    __tablename__ = 'loc_output_location_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))
    
    # Value Columns
    fileExtension = Column(String, nullable=False)
    numLocations = Column(Integer, nullable=False)
    
    # Relationship Properties
    projectFile = relationship('ProjectFile', back_populates='outputLocationFiles')
    outputLocations = relationship('OutputLocation', back_populates='outputLocationFile')
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
        
    def _readWithoutCommit(self):
        '''
        Generic Output Location Read from File Method
        '''
        # Assign file extension attribute to file object
        self.fileExtension = self.EXTENSION
        
        # Open file and parse into a data structure
        with open(self.PATH, 'r') as f:
            for line in f:
                sline = line.strip().split()
                
                if len(sline) == 1:
                    self.numLocations = sline[0]
                else:
                    # Create GSSAHPY OutputLocation object
                    location = OutputLocation(linkOrCellI=sline[0],
                                              nodeOrCellJ=sline[1])
                    
                    # Associate OutputLocation with OutputLocationFile
                    location.outputLocationFile = self
        
        
    def _writeToOpenFile(self, directory, session, name, openFile):
        '''
        Generic Output Location Write to File Method
        '''        
        # Retrieve output locations
        locations = self.outputLocations
        
        # Write lines
        openFile.write('%s\n' % self.numLocations)
        
        for location in locations:
            openFile.write('%s %s\n' % (location.linkOrCellI,
                                        location.nodeOrCellJ))
        
class OutputLocation(DeclarativeBase):
    '''
    classdocs
    '''
    
    __tablename__ = 'loc_output_locations'

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    outputLocationFileID = Column(Integer, ForeignKey('loc_output_location_files.id'))
    
    # Value Columns
    linkOrCellI = Column(Integer, nullable=False)
    nodeOrCellJ = Column(Integer, nullable=False)
    
    # Relationship Properties
    outputLocationFile = relationship('OutputLocationFile', back_populates='outputLocations')
    
    def __init__(self, linkOrCellI, nodeOrCellJ):
        self.linkOrCellI = linkOrCellI
        self.nodeOrCellJ = nodeOrCellJ
        
    def __repr__(self):
        return '<OutputLocation: LinkOrCellI=%s, NodeOrCellJ=%s>' % (self.linkNumber, self.nodeNumber)
        
