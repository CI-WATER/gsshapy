'''
********************************************************************************
* Name: StormDrainNetworkModel
* Author: Nathan Swain
* Created On: May 14, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['GridPipeCell',
           'GridPipeFile',
           'GridPipeNode']

import os

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase
from gsshapy.lib import parsetools as pt

class GridPipeFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    '''
    __tablename__ = 'gpi_grid_pipe_files'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    
    # Relationship Properties
    gridPipeCells = relationship('GridPipeCell', back_populates='gridPipeFile') #: RELATIONSHIP
    projectFile = relationship('ProjectFile', uselist=False, back_populates='gridPipeFile') #: RELATIONSHIP
    
    # Value Columns
    pipeCells = Column(Integer, nullable=False) #: INTEGER
    
    # File Properties
    EXTENSION = 'gpi'    
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
    
    def _read(self):
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
                    self._createGsshaPyObjects(result)

        
    def _write(self, session, openFile):
        '''
        Grid Pipe File Write to File Method
        '''
        # Write Lines
        openFile.write('GRIDPIPEFILE\n')
        openFile.write('PIPECELLS %s\n' % self.pipeCells)
        
        for cell in self.gridPipeCells:
            openFile.write('CELLIJ    %s  %s\n' % (cell.cellI, cell.cellJ))
            openFile.write('NUMPIPES  %s\n' % cell.numPipes)
            
            for node in cell.gridPipeNodes:
                openFile.write('SPIPE     %s  %s  %.6f\n' % (
                              node.linkNumber,
                              node.nodeNumber,
                              node.fractPipeLength))
        
    def _createGsshaPyObjects(self, cell):
        '''
        Create GSSHAPY GridPipeCell and GridPipeNode Objects Method
        '''
        # Intialize GSSHAPY GridPipeCell object
        gridCell = GridPipeCell(cellI=cell['i'],
                            cellJ=cell['j'],
                            numPipes=cell['numPipes'])
        
        # Associate GridPipeCell with GridPipeFile
        gridCell.gridPipeFile = self
        
        for spipe in cell['spipes']:
            # Create GSSHAPY GridPipeNode object
            gridNode = GridPipeNode(linkNumber=spipe['linkNumber'],
                                    nodeNumber=spipe['nodeNumber'],
                                    fractPipeLength=spipe['fraction'])
            
            # Associate GridPipeNode with GridPipeCell
            gridNode.gridPipeCell = gridCell
        
        
        
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
                
                
class GridPipeCell(DeclarativeBase):
    '''
    '''
    __tablename__ = 'gpi_grid_pipe_cells'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    gridPipeFileID = Column(Integer, ForeignKey('gpi_grid_pipe_files.id')) #: FK
    
    # Value Columns
    cellI = Column(Integer, nullable=False) #: INTEGER
    cellJ = Column(Integer, nullable=False) #: INTEGER
    numPipes = Column(Integer, nullable=False) #: INTEGER
    
    
    # Relationship Properties
    gridPipeFile = relationship('GridPipeFile', back_populates='gridPipeCells') #: RELATIONSHIP
    gridPipeNodes = relationship('GridPipeNode', back_populates='gridPipeCell') #: RELATIONSHIP
    
    def __init__(self, cellI, cellJ, numPipes):
        '''
        Constructor
        '''
        self.cellI = cellI
        self.cellJ = cellJ
        self.numPipes = numPipes
        

    def __repr__(self):
        return '<GridPipeCell: CellI=%s, CellJ=%s, NumPipes=%s>' % (
                self.cellI, 
                self.cellJ, 
                self.numPipes)
        
class GridPipeNode(DeclarativeBase):
    '''
    '''
    __tablename__ = 'gpi_grid_pipe_nodes'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    gridPipeCellID = Column(Integer, ForeignKey('gpi_grid_pipe_cells.id')) #: FK
    
    # Value Columns
    linkNumber = Column(Integer, nullable=False) #: INTEGER
    nodeNumber = Column(Integer, nullable=False) #: INTEGER
    fractPipeLength = Column(Float, nullable=False) #: FLOAT
    
    # Relationship Properties
    gridPipeCell = relationship('GridPipeCell', back_populates='gridPipeNodes') #: RELATIONSHIP
    
    def __init__(self, linkNumber, nodeNumber, fractPipeLength):
        '''
        Constructor
        '''
        self.linkNumber = linkNumber
        self.nodeNumber = nodeNumber
        self.fractPipeLength = fractPipeLength

    def __repr__(self):
        return '<GridPipeNode: LinkNumber=%s, NodeNumber=%s, FractPipeLength=%s>' % (
                self.linkNumber,
                self.nodeNumber,
                self.fractPipeLength)
    