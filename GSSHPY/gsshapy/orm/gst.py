'''
********************************************************************************
* Name: GridToStreamModel
* Author: Nathan Swain
* Created On: May 14, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''
from gsshapy.lib import parsetools as pt

__all__ = ['GridStreamFile',
           'GridStreamCell',
           'GridStreamNode']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

class GridStreamFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    classdocs
    '''
    __tablename__ = 'gst_grid_stream_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Relationship Properties
    gridStreamCells = relationship('GridStreamCell', back_populates='gridStreamFile')
    projectFile = relationship('ProjectFile', uselist=False, back_populates='gridStreamFile')
    
    # Value Columns
    streamCells = Column(Integer, nullable=False)
    
    # File Properties
    EXTENSION = 'gst'
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
        
    def _readWithoutCommit(self):
        '''
        Grid Stream File Read from File Method
        '''
        # Keywords
        KEYWORDS = ('STREAMCELLS',
                    'CELLIJ')
        
        # Parse file into chunks associated with keywords/cards
        with open(self.PATH, 'r') as f:
            chunks = pt.chunk(KEYWORDS, f)
        
        # Parse chunks associated with each key    
        for key, chunkList in chunks.iteritems():
            # Parse each chunk in the chunk list
            for chunk in chunkList:

                # Cases
                if key == 'STREAMCELLS':
                    # PIPECELLS Handler
                    schunk = chunk[0].strip().split()
                    self.streamCells = schunk[1]
                
                elif key == 'CELLIJ':
                    # CELLIJ Handler
                    # Parse CELLIJ Chunk
                    result = self._cellChunk(chunk)
                    
                    # Create GSSHAPY object
                    self._createGsshaPyObjects(result)

        
    def write(self, directory, session, name):
        '''
        Grid Stream File Write to File Method
        '''
        filePath = '%s%s.%s' % (directory, name, self.EXTENSION)
        
        with open(filePath, 'w') as gpiFile:
            gpiFile.write('GRIDSTREAMFILE\n')
            gpiFile.write('STREAMCELLS %s\n' % self.streamCells)
            
            for cell in self.gridStreamCells:
                gpiFile.write('CELLIJ    %s  %s\n' % (cell.cellI, cell.cellJ))
                gpiFile.write('NUMNODES  %s\n' % cell.numNodes)
                
                for node in cell.gridStreamNodes:
                    gpiFile.write('LINKNODE  %s  %s  %.6f\n' % (
                                  node.linkNumber,
                                  node.nodeNumber,
                                  node.nodePercentGrid))
                    
    def _createGsshaPyObjects(self, cell):
        '''
        Create GSSHAPY PipeGridCell and PipeGridNode Objects Method
        '''
        # Intialize GSSHAPY PipeGridCell object
        gridCell = GridStreamCell(cellI=cell['i'],
                                  cellJ=cell['j'],
                                  numNodes=cell['numNodes'])
        
        # Associate GridStreamCell with GridStreamFile
        gridCell.gridStreamFile = self
        
        for linkNode in cell['linkNodes']:
            # Create GSSHAPY GridStreamNode object
            gridNode = GridStreamNode(linkNumber=linkNode['linkNumber'],
                                      nodeNumber=linkNode['nodeNumber'],
                                      nodePercentGrid=linkNode['percent'])
            
            # Associate GridStreamNode with GridStreamCell
            gridNode.gridStreamCell = gridCell
        
        
        
    def _cellChunk(self, lines):
        '''
        Parse CELLIJ Chunk Method
        '''
        KEYWORDS = ('CELLIJ',
                    'NUMNODES',
                    'LINKNODE')
    
        result = {'i': None,
                  'j': None,
                  'numNodes': None,
                  'linkNodes': []}
        
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
                
                elif card == 'NUMNODES':
                    # NUMPIPES handler
                    result['numNodes'] = schunk[1]
                
                elif card == 'LINKNODE':
                    # SPIPE handler
                    pipe = {'linkNumber': schunk[1],
                            'nodeNumber': schunk[2],
                            'percent': schunk[3]}
                    
                    result['linkNodes'].append(pipe)
        
        return result
    

class GridStreamCell(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gst_grid_stream_cells'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    gridStreamFileID = Column(Integer, ForeignKey('gst_grid_stream_files.id'))
    
    # Value Columns
    cellI = Column(Integer, nullable=False)
    cellJ = Column(Integer, nullable=False)
    numNodes = Column(Integer, nullable=False)
    
    # Relationship Properties
    gridStreamFile = relationship('GridStreamFile', back_populates='gridStreamCells')
    gridStreamNodes = relationship('GridStreamNode', back_populates='gridStreamCell')
    
    def __init__(self, cellI, cellJ, numNodes):
        '''
        Constructor
        '''
        self.cellI = cellI
        self.cellJ = cellJ
        self.numNodes = numNodes

    def __repr__(self):
        return '<GridStreamCell: CellI=%s, CellJ=%s, NumNodes=%s>' % (self.cellI, self.cellJ, self.numNodes)
    
class GridStreamNode(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gst_grid_stream_nodes'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    gridStreamCellID = Column(Integer, ForeignKey('gst_grid_stream_cells.id'))
    
    # Value Columns
    linkNumber = Column(Integer, nullable=False)
    nodeNumber = Column(Integer, nullable=False)
    nodePercentGrid = Column(Float, nullable=False)
    
    # Relationship Properties
    gridStreamCell = relationship('GridStreamCell', back_populates='gridStreamNodes')
    
    def __init__(self, linkNumber, nodeNumber, nodePercentGrid):
        '''
        Constructor
        '''
        self.linkNumber = linkNumber
        self.nodeNumber = nodeNumber
        self.nodePercentGrid = nodePercentGrid

    def __repr__(self):
        return '<GridStreamNode: LinkNumber=%s, NodeNumber=%s, NodePercentGrid=%s>' % (self.linkNumber, self.nodeNumber, self.nodePercentGrid)
