'''
********************************************************************************
* Name: Link Node Dataset Model
* Author: Nathan Swain
* Created On: August 1, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''
__all__ = ['LinkNodeDatasetFile',
           'TimeStep',
           'LinkNodeLine']

from datetime import datetime

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, DateTime
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

from gsshapy.lib import parsetools as pt

class LinkNodeDatasetFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    classdocs
    '''
    __tablename__ = 'lnd_link_node_dataset_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))
    
    # Value Columns
    fileExtension = Column(String, nullable=False)
    name = Column(String, nullable=False)
    numLinks = Column(Integer, nullable=False)
    timeStep = Column(Integer, nullable=False)
    numTimeSteps = Column(Integer, nullable=False)
    startTime= Column(String, nullable=False)
    
    # Relationship Properites
    projectFile = relationship('ProjectFile', back_populates='linkNodeDatasets')
    timeSteps = relationship('TimeStep', back_populates='linkNodeDataset')
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
    
    def read(self):
        '''
        Raster Map File Read from File Method
        '''
        # Assign file extension attribute to file object
        self.fileExtension = self.EXTENSION
        
        # Dictionary of keywords/cards and parse function names
        KEYWORDS = ('NUM_LINKS',
                    'TIME_STEP',
                    'NUM_TS',
                    'START_TIME',
                    'TS')
        
        # Parse file into chunks associated with keywords/cards
        with open(self.PATH, 'r') as f:
            self.name = f.readline().strip()
            chunks = pt.chunk(KEYWORDS, f)
            
        # Parse chunks associated with each key    
        for card, chunkList in chunks.iteritems():
            # Parse each chunk in the chunk list
            for chunk in chunkList:
                schunk = chunk[0].strip().split()
                
                # Cases
                if card == 'NUM_LINKS':
                    # NUM_LINKS handler
                    self.numLinks = schunk[1]
                                        
                elif card == 'TIME_STEP':
                    # TIME_STEP handler
                    self.timeStep = schunk[1]
                    
                elif card == 'NUM_TS':
                    # NUM_TS handler
                    self.numTimeSteps = schunk[1]
                    
                elif card == 'START_TIME':
                    # START_TIME handler
                    self.startTime = '%s  %s    %s  %s  %s  %s' % (
                                      schunk[1],
                                      schunk[2],
                                      schunk[3],
                                      schunk[4],
                                      schunk[5],
                                      schunk[6])
                    
                elif card == 'TS':
                    # TS handler
                    for line in chunk:
                        sline = line.strip().split()
                        token = sline[0]
                        
                        # Cases
                        if token == 'TS':
                            # Time Step line handler
                            timeStep = TimeStep(timeStep=sline[1])
                            timeStep.linkNodeDataset = self

                        else:
                            # LinkNodeLine handler
                            lnLine = LinkNodeLine(value=line.strip())
                            lnLine.timeStep = timeStep

                
        
    def write(self, directory, session, filename):
        '''
        Raster Map File Write to File Method
        '''
        # Initiate file
        filePath = '%s%s' % (directory, filename)
        
        # Retrieve TimeStep objects
        timeSteps = self.timeSteps

        # Open file and write
        with open(filePath, 'w') as lndFile:
            lndFile.write('%s\n' % self.name)
            lndFile.write('NUM_LINKS     %s\n' % self.numLinks)
            lndFile.write('TIME_STEP     %s\n' % self.timeStep)
            lndFile.write('NUM_TS        %s\n' % self.numTimeSteps)
            lndFile.write('START_TIME    %s\n' % self.startTime)
            
            for timeStep in timeSteps:
                lndFile.write('TS    %s\n' % timeStep.timeStep)
                
                # Retrieve LinkNodeLine objects
                lnLines = timeStep.linkNodeLines
                
                for lnLine in lnLines:
                    lndFile.write('%s\n' % lnLine.value)
                
                # Insert empty line between time steps 
                lndFile.write('\n')
            
class TimeStep(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'lnd_time_steps'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    linkNodeDatasetFileID = Column(Integer, ForeignKey('lnd_link_node_dataset_files.id'))
    
    # Value Columns
    timeStep = Column(Integer, nullable=False)
    
    # Relationship Properites
    linkNodeDataset = relationship('LinkNodeDatasetFile', back_populates='timeSteps')
    linkNodeLines = relationship('LinkNodeLine', back_populates='timeStep')
    
    def __init__(self, timeStep):
        self.timeStep = timeStep
        
    def __repr__(self):
        return '<TimeStep: %s>' % self.timeStep

class LinkNodeLine(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'lnd_link_node_lines'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    timeStepID = Column(Integer, ForeignKey('lnd_time_steps.id'))
    
    # Value Columns
    value = Column(String, nullable=False)
    
    # Relationship Properties
    timeStep = relationship('TimeStep', back_populates='linkNodeLines')
    
    def __init__(self, value):
        self.value = value
        
    def __repr__(self):
        return '<LinkNodeLine: %s>' % self.value
    
    