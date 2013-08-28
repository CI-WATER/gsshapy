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

import os

from datetime import datetime

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

from gsshapy.lib import parsetools as pt

class LinkNodeDatasetFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    '''
    __tablename__ = 'lnd_link_node_dataset_files'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id')) #: FK
    
    # Value Columns
    fileExtension = Column(String, nullable=False) #: STRING
    name = Column(String, nullable=False) #: STRING
    numLinks = Column(Integer, nullable=False) #: INTEGER
    timeStep = Column(Integer, nullable=False) #: INTEGER
    numTimeSteps = Column(Integer, nullable=False) #: INTEGER
    startTime= Column(String, nullable=False) #: STRING
    
    # Relationship Properites
    projectFile = relationship('ProjectFile', back_populates='linkNodeDatasets') #: RELATIONSHIP
    timeSteps = relationship('TimeStep', back_populates='linkNodeDataset') #: RELATIONSHIP
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
    
    def _read(self):
        '''
        Link Node Dataset File Read from File Method
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

                
        
    def _write(self, session, openFile):
        '''
        Link Node Dataset File Write to File Method
        '''
        # Retrieve TimeStep objects
        timeSteps = self.timeSteps

        # Write Lines
        openFile.write('%s\n' % self.name)
        openFile.write('NUM_LINKS     %s\n' % self.numLinks)
        openFile.write('TIME_STEP     %s\n' % self.timeStep)
        openFile.write('NUM_TS        %s\n' % self.numTimeSteps)
        openFile.write('START_TIME    %s\n' % self.startTime)
        
        for timeStep in timeSteps:
            openFile.write('TS    %s\n' % timeStep.timeStep)
            
            # Retrieve LinkNodeLine objects
            lnLines = timeStep.linkNodeLines
            
            for lnLine in lnLines:
                openFile.write('%s\n' % lnLine.value)
            
            # Insert empty line between time steps 
            openFile.write('\n')
            
class TimeStep(DeclarativeBase):
    '''
    '''
    __tablename__ = 'lnd_time_steps'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    linkNodeDatasetFileID = Column(Integer, ForeignKey('lnd_link_node_dataset_files.id')) #: FK
    
    # Value Columns
    timeStep = Column(Integer, nullable=False) #: INTEGER
    
    # Relationship Properites
    linkNodeDataset = relationship('LinkNodeDatasetFile', back_populates='timeSteps') #: RELATIONSHIP
    linkNodeLines = relationship('LinkNodeLine', back_populates='timeStep') #: RELATIONSHIP
    
    def __init__(self, timeStep):
        self.timeStep = timeStep
        
    def __repr__(self):
        return '<TimeStep: %s>' % self.timeStep

class LinkNodeLine(DeclarativeBase):
    '''
    '''
    __tablename__ = 'lnd_link_node_lines'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    timeStepID = Column(Integer, ForeignKey('lnd_time_steps.id')) #: FK
    
    # Value Columns
    value = Column(String, nullable=False) #: STRING
    
    # Relationship Properties
    timeStep = relationship('TimeStep', back_populates='linkNodeLines') #: RELATIONSHIP
    
    def __init__(self, value):
        self.value = value
        
    def __repr__(self):
        return '<LinkNodeLine: %s>' % self.value
    
    