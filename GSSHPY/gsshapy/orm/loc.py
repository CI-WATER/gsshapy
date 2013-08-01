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

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase

class OutputLocationFile(DeclarativeBase):
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
        
    def read(self):
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
                    location = OutputLocation(linkNumber=sline[0],
                                              nodeNumber=sline[1])
                    
                    # Associate OutputLocation with OutputLocationFile
                    location.outputLocationFile = self
        
        
    def write(self, directory, session, filename):
        '''
        Generic Output Location Write to File Method
        '''
        # Initiate file
        filePath = '%s%s' % (directory, filename)
        
        # Retrieve output locations
        locations = self.outputLocations
        
        # Open file and write
        with open(filePath, 'w') as locFile:
            locFile.write('%s\n' % self.numLocations)
            
            for location in locations:
                locFile.write('%s %s\n' % (location.linkNumber,
                                           location.nodeNumber))
        
class OutputLocation(DeclarativeBase):
    '''
    classdocs
    '''
    
    __tablename__ = 'loc_output_locations'

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    outputLocationFileID = Column(Integer, ForeignKey('loc_output_location_files.id'))
    
    # Value Columns
    linkNumber = Column(Integer, nullable=False)
    nodeNumber = Column(Integer, nullable=False)
    
    # Relationship Properties
    outputLocationFile = relationship('OutputLocationFile', back_populates='outputLocations')
    
    def __init__(self, linkNumber, nodeNumber):
        self.linkNumber = linkNumber
        self.nodeNumber = nodeNumber
        
    def __repr__(self):
        return '<OutputLocation: LinkNumber=%s, NodeNumber=%s>' % (self.linkNumber, self.nodeNumber)
        
