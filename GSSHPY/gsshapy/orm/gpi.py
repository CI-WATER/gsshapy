'''
********************************************************************************
* Name: StormDrainNetwork
* Author: Nathan Swain
* Created On: May 14, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

import os, sys
from datetime import datetime

__all__ = ['PipeGridCell',
           'GridPipeFile']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase

from gsshapy.lib import parsetools as pt

class GridPipeFile(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gpi_grid_pipe_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Relationship Properties
    pipeGridCells = relationship('PipeGridCell', back_populates='gridPipeFile')
    projectFile = relationship('ProjectFile', uselist=False, back_populates='gridPipeFile')
    
    # Value Columns
    pipeCells = Column(Integer, nullable=False)
    
    # Global Properties
    PATH = ''
    FILENAME = ''
    DIRECTORY = ''
    SESSION = None
    EXTENSION = 'gpi'
    
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        self.FILENAME = filename
        self.DIRECTORY = directory
        self.SESSION = session
        self.PATH = '%s%s' % (self.DIRECTORY, self.FILENAME)
        
    def read(self):
        '''
        Grid Pipe File Read from File Method
        '''
        # Keywords
        KEYWORDS = ('PIPECELLS',
                    'CELLIJ')
        
        # Parse file into chunks associated with keywords/cards
        with open(self.PATH, 'r') as f:
            chunks = pt.chunk(KEYWORDS, f)
        
        # Parse chunks associated with each key    
        for key, chunkList in chunks.iteritems():
            # Parse each chunk in the chunk list
            for chunk in chunkList:

                # Cases
                if key == 'PIPECELLS':
                    # PIPECELLS Handler
                    schunk = chunk[0].strip().split()
                    self.pipeCells = schunk[1]
                
                elif key == 'CELLIJ':
                    # CELLIJ Handler
                    # Parse CELLIJ Chunk
                    result = self._cellChunk(chunk)
                    
                    # Create GSSHAPY object
                    self._createCellObject(result)

        
    def write(self, directory, session, filePrefix):
        '''
        Grid Pipe File Write to File Method
        '''
        fullPath = '%s%s.%s' % (directory, filePrefix, self.EXTENSION)
        
        with open(fullPath, 'w') as gpiFile:
            gpiFile.write('GRIDPIPEFILE\n')
            gpiFile.write('PIPECELLS %s\n' % self.pipeCells)
            
            for cell in self.pipeGridCells:
                gpiFile.write('CELLIJ    %s  %s\n' % (cell.cellI, cell.cellJ))
                gpiFile.write('NUMPIPES  %s\n' % cell.numPipes)
                
                for node in cell.pipeGridNodes:
                    gpiFile.write('SPIPE     %s  %s  %.6f\n' % (
                                  node.linkNumber,
                                  node.nodeNumber,
                                  node.fractPipeLength))
        
    def _createCellObject(self, cell):
        '''
        Create GSSHAPY PipeGridCell and PipeGridNode Objects Method
        '''
        # Intialize GSSHAPY PipeGridCell object
        gridCell = PipeGridCell(cellI=cell['i'],
                            cellJ=cell['j'],
                            numPipes=cell['numPipes'])
        
        # Associate PipeGridCell with GridPipeFile
        gridCell.gridPipeFile = self
        
        for spipe in cell['spipes']:
            # Create GSSHAPY PipeGridNode object
            gridNode = PipeGridNode(linkNumber=spipe['linkNumber'],
                                    nodeNumber=spipe['nodeNumber'],
                                    fractPipeLength=spipe['fraction'])
            
            # Associate PipeGridNode with PipeGridCell
            gridNode.pipeGridCell = gridCell
        
        
        
    def _cellChunk(self, lines):
        '''
        Parse CELLIJ Chunk Method
        '''
        KEYWORDS = ('CELLIJ',
                    'NUMPIPES',
                    'SPIPE')
    
        result = {'i': None,
                  'j': None,
                  'numPipes': None,
                  'spipes': []}
        
        chunks = pt.chunk(KEYWORDS, lines)
        
        # Parse chunks associated with each key    
        for card, chunkList in chunks.iteritems():
            # Parse each chunk in the chunk list
            for chunk in chunkList:
                schunk = chunk[0].strip().split()
                
                # Cases
                if card == 'CELLIJ':
                    # CELLIJ handler
                    result['i'] = schunk[1]
                    result['j'] = schunk[2]
                
                elif card == 'NUMPIPES':
                    # NUMPIPES handler
                    result['numPipes'] = schunk[1]
                
                elif card == 'SPIPE':
                    # SPIPE handler
                    pipe = {'linkNumber': schunk[1],
                            'nodeNumber': schunk[2],
                            'fraction': schunk[3]}
                    
                    result['spipes'].append(pipe)
        
        return result
                
                
class PipeGridCell(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gpi_pipe_grid_cells'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    gridPipeFileID = Column(Integer, ForeignKey('gpi_grid_pipe_files.id'))
    
    # Value Columns
    cellI = Column(Integer, nullable=False)
    cellJ = Column(Integer, nullable=False)
    numPipes = Column(Integer, nullable=False)
    
    
    # Relationship Properties
    gridPipeFile = relationship('GridPipeFile', back_populates='pipeGridCells')
    pipeGridNodes = relationship('PipeGridNode', back_populates='pipeGridCell')
    
    def __init__(self, cellI, cellJ, numPipes):
        '''
        Constructor
        '''
        self.cellI = cellI
        self.cellJ = cellJ
        self.numPipes = numPipes
        

    def __repr__(self):
        return '<PipeGridCell: CellI=%s, CellJ=%s, NumPipes=%s>' % (
                self.cellI, 
                self.cellJ, 
                self.numPipes)
        
class PipeGridNode(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gpi_pipe_grid_nodes'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    pipeGridCellID = Column(Integer, ForeignKey('gpi_pipe_grid_cells.id'))
    
    # Value Columns
    linkNumber = Column(Integer, nullable=False)
    nodeNumber = Column(Integer, nullable=False)
    fractPipeLength = Column(Float, nullable=False)
    
    # Relationship Properties
    pipeGridCell = relationship('PipeGridCell', back_populates='pipeGridNodes')
    
    def __init__(self, linkNumber, nodeNumber, fractPipeLength):
        '''
        Constructor
        '''
        self.linkNumber = linkNumber
        self.nodeNumber = nodeNumber
        self.fractPipeLength = fractPipeLength

    def __repr__(self):
        return '<PipeGridNode: LinkNumber=%s, NodeNumber=%s, FractPipeLength=%s>' % (
                self.linkNumber,
                self.nodeNumber,
                self.fractPipeLength)
    