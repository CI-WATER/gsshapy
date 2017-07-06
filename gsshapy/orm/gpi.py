"""
********************************************************************************
* Name: StormDrainNetworkModel
* Author: Nathan Swain
* Created On: May 14, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from __future__ import unicode_literals

__all__ = ['GridPipeCell',
           'GridPipeFile',
           'GridPipeNode']

from future.utils import iteritems
from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float, String
from sqlalchemy.orm import relationship

from . import DeclarativeBase
from ..base.file_base import GsshaPyFileObjectBase
from ..lib import parsetools as pt


class GridPipeFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for the Grid Pipe File.

    The grid pipe file is used to map the grid pipe network for subsurface drainage to the model grid. The contents of
    the grid pipe file is abstracted into two types of objects including: :class:`.GridPipeCell` and
    :class:`.GridPipeNode`. Each cell lists the pipe nodes that are contained in the cell and each pipe node defines
    the percentage of a pipe that is contained inside a cell. See the documentation provided for each object for a more
    details.

    See: http://www.gsshawiki.com/Subsurface_Drainage:Subsurface_Drainage
         http://www.gsshawiki.com/images/d/d6/SUPERLINK_TN.pdf
    """
    __tablename__ = 'gpi_grid_pipe_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK

    # Relationship Properties
    gridPipeCells = relationship('GridPipeCell', back_populates='gridPipeFile')  #: RELATIONSHIP
    projectFile = relationship('ProjectFile', uselist=False, back_populates='gridPipeFile')  #: RELATIONSHIP

    # Value Columns
    pipeCells = Column(Integer, nullable=False)  #: INTEGER
    fileExtension = Column(String, default='gpi')  #: STRING

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
        """
        Grid Pipe File Read from File Method
        """
        # Set file extension property
        self.fileExtension = extension

        # Keywords
        KEYWORDS = ('PIPECELLS',
                    'CELLIJ')

        # Parse file into chunks associated with keywords/cards
        with open(path, 'r') as f:
            chunks = pt.chunk(KEYWORDS, f)

        # Parse chunks associated with each key
        for key, chunkList in iteritems(chunks):
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

    def _write(self, session, openFile, replaceParamFile):
        """
        Grid Pipe File Write to File Method
        """
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
        """
        Create GSSHAPY GridPipeCell and GridPipeNode Objects Method
        """
        # Initialize GSSHAPY GridPipeCell object
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
        """
        Parse CELLIJ Chunk Method
        """
        KEYWORDS = ('CELLIJ',
                    'NUMPIPES',
                    'SPIPE')

        result = {'i': None,
                  'j': None,
                  'numPipes': None,
                  'spipes': []}

        chunks = pt.chunk(KEYWORDS, lines)

        # Parse chunks associated with each key
        for card, chunkList in iteritems(chunks):
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
    """
    Object containing the pipe data for a single grid cell. A cell can contain several pipe nodes.
    """
    __tablename__ = 'gpi_grid_pipe_cells'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    gridPipeFileID = Column(Integer, ForeignKey('gpi_grid_pipe_files.id'))  #: FK

    # Value Columns
    cellI = Column(Integer)  #: INTEGER
    cellJ = Column(Integer)  #: INTEGER
    numPipes = Column(Integer)  #: INTEGER


    # Relationship Properties
    gridPipeFile = relationship('GridPipeFile', back_populates='gridPipeCells')  #: RELATIONSHIP
    gridPipeNodes = relationship('GridPipeNode', back_populates='gridPipeCell')  #: RELATIONSHIP

    def __init__(self, cellI, cellJ, numPipes):
        """
        Constructor
        """
        self.cellI = cellI
        self.cellJ = cellJ
        self.numPipes = numPipes

    def __repr__(self):
        return '<GridPipeCell: CellI=%s, CellJ=%s, NumPipes=%s>' % (
            self.cellI,
            self.cellJ,
            self.numPipes)


class GridPipeNode(DeclarativeBase):
    """
    Object containing data for a single pipe.
    """
    __tablename__ = 'gpi_grid_pipe_nodes'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    gridPipeCellID = Column(Integer, ForeignKey('gpi_grid_pipe_cells.id'))  #: FK

    # Value Columns
    linkNumber = Column(Integer)  #: INTEGER
    nodeNumber = Column(Integer)  #: INTEGER
    fractPipeLength = Column(Float)  #: FLOAT

    # Relationship Properties
    gridPipeCell = relationship('GridPipeCell', back_populates='gridPipeNodes')  #: RELATIONSHIP

    def __init__(self, linkNumber, nodeNumber, fractPipeLength):
        """
        Constructor
        """
        self.linkNumber = linkNumber
        self.nodeNumber = nodeNumber
        self.fractPipeLength = fractPipeLength

    def __repr__(self):
        return '<GridPipeNode: LinkNumber=%s, NodeNumber=%s, FractPipeLength=%s>' % (
            self.linkNumber,
            self.nodeNumber,
            self.fractPipeLength)
