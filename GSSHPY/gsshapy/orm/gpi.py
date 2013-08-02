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
           'GridPipeFile']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase
from gsshapy.lib import parsetools as pt

class GridPipeFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    classdocs
    '''
    __tablename__ = 'gpi_grid_pipe_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Relationship Properties
    gridPipeCells = relationship('GridPipeCell', back_populates='gridPipeFile')
    projectFile = relationship('ProjectFile', uselist=False, back_populates='gridPipeFile')
    
    # Value Columns
    pipeCells = Column(Integer, nullable=False)    
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
        
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
                    self._createGsshaPyObjects(result)

        
    def write(self, directory, session, filename):
        '''
        Grid Pipe File Write to File Method
        '''
        filePath = '%s%s' % (directory, filename)
        
        with open(filePath, 'w') as gpiFile:
            gpiFile.write('GRIDPIPEFILE\n')
            gpiFile.write('PIPECELLS %s\n' % self.pipeCells)
            
            for cell in self.gridPipeCells:
                gpiFile.write('CELLIJ    %s  %s\n' % (cell.cellI, cell.cellJ))
                gpiFile.write('NUMPIPES  %s\n' % cell.numPipes)
                
                for node in cell.gridPipeNodes:
                    gpiFile.write('SPIPE     %s  %s  %.6f\n' % (
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
    classdocs
    '''
    __tablename__ = 'gpi_grid_pipe_cells'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    gridPipeFileID = Column(Integer, ForeignKey('gpi_grid_pipe_files.id'))
    
    # Value Columns
    cellI = Column(Integer, nullable=False)
    cellJ = Column(Integer, nullable=False)
    numPipes = Column(Integer, nullable=False)
    
    
    # Relationship Properties
    gridPipeFile = relationship('GridPipeFile', back_populates='gridPipeCells')
    gridPipeNodes = relationship('GridPipeNode', back_populates='gridPipeCell')
    
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
    classdocs
    '''
    __tablename__ = 'gpi_grid_pipe_nodes'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    gridPipeCellID = Column(Integer, ForeignKey('gpi_grid_pipe_cells.id'))
    
    # Value Columns
    linkNumber = Column(Integer, nullable=False)
    nodeNumber = Column(Integer, nullable=False)
    fractPipeLength = Column(Float, nullable=False)
    
    # Relationship Properties
    gridPipeCell = relationship('GridPipeCell', back_populates='gridPipeNodes')
    
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
    