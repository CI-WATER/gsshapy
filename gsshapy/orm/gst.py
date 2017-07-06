"""
********************************************************************************
* Name: GridToStreamModel
* Author: Nathan Swain
* Created On: May 14, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from __future__ import unicode_literals

from gsshapy.lib import parsetools as pt

__all__ = ['GridStreamFile',
           'GridStreamCell',
           'GridStreamNode']

from future.utils import iteritems
from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float, String
from sqlalchemy.orm import relationship

from . import DeclarativeBase
from ..base.file_base import GsshaPyFileObjectBase


class GridStreamFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for the Grid Stream File.

    The grid stream file is used to map the stream network to the model grid. The contents of
    the grid stream file is abstracted into two types of objects including: :class:`.GridStreamCell` and
    :class:`.GridStreamNode`. Each cell lists the stream nodes that are contained in it and each stream node defines
    the percentage of that stream that is contained inside a cell. See the documentation provided for each object for a
    more details.

    See: http://www.gsshawiki.com/Surface_Water_Routing:Channel_Routing#5.1.4.2.1_-_STREAM_CELL_file_identifier
    """
    __tablename__ = 'gst_grid_stream_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK

    # Value Columns
    streamCells = Column(Integer, nullable=False)  #: INTEGER
    fileExtension = Column(String, default='gst')  #: STRING

    # Relationship Properties
    gridStreamCells = relationship('GridStreamCell', back_populates='gridStreamFile')  #: RELATIONSHIP
    projectFile = relationship('ProjectFile', uselist=False, back_populates='gridStreamFile')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
        """
        Grid Stream File Read from File Method
        """
        # Set file extension property
        self.fileExtension = extension

        # Keywords
        KEYWORDS = ('STREAMCELLS',
                    'CELLIJ')

        # Parse file into chunks associated with keywords/cards
        with open(path, 'r') as f:
            chunks = pt.chunk(KEYWORDS, f)

        # Parse chunks associated with each key
        for key, chunkList in iteritems(chunks):
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


    def _write(self, session, openFile, replaceParamFile):
        """
        Grid Stream File Write to File Method
        """
        # Write lines
        openFile.write('GRIDSTREAMFILE\n')
        openFile.write('STREAMCELLS %s\n' % self.streamCells)

        for cell in self.gridStreamCells:
            openFile.write('CELLIJ    %s  %s\n' % (cell.cellI, cell.cellJ))
            openFile.write('NUMNODES  %s\n' % cell.numNodes)

            for node in cell.gridStreamNodes:
                openFile.write('LINKNODE  %s  %s  %.6f\n' % (
                    node.linkNumber,
                    node.nodeNumber,
                    node.nodePercentGrid))

    def _createGsshaPyObjects(self, cell):
        """
        Create GSSHAPY PipeGridCell and PipeGridNode Objects Method
        """
        # Initialize GSSHAPY PipeGridCell object
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
        """
        Parse CELLIJ Chunk Method
        """
        KEYWORDS = ('CELLIJ',
                    'NUMNODES',
                    'LINKNODE')

        result = {'i': None,
                  'j': None,
                  'numNodes': None,
                  'linkNodes': []}

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
    """
    Object containing the stream data for a single grid cell. A cell can contain several stream nodes.
    """
    __tablename__ = 'gst_grid_stream_cells'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    gridStreamFileID = Column(Integer, ForeignKey('gst_grid_stream_files.id'))  #: FK

    # Value Columns
    cellI = Column(Integer)  #: INTEGER
    cellJ = Column(Integer)  #: INTEGER
    numNodes = Column(Integer)  #: INTEGER

    # Relationship Properties
    gridStreamFile = relationship('GridStreamFile', back_populates='gridStreamCells')  #: RELATIONSHIP
    gridStreamNodes = relationship('GridStreamNode', back_populates='gridStreamCell')  #: RELATIONSHIP

    def __init__(self, cellI, cellJ, numNodes):
        """
        Constructor
        """
        self.cellI = cellI
        self.cellJ = cellJ
        self.numNodes = numNodes

    def __repr__(self):
        return '<GridStreamCell: CellI=%s, CellJ=%s, NumNodes=%s>' % (self.cellI, self.cellJ, self.numNodes)


class GridStreamNode(DeclarativeBase):
    """
    Object containing data for a single stream.
    """
    __tablename__ = 'gst_grid_stream_nodes'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    gridStreamCellID = Column(Integer, ForeignKey('gst_grid_stream_cells.id'))  #: FK

    # Value Columns
    linkNumber = Column(Integer)  #: INTEGER
    nodeNumber = Column(Integer)  #: INTEGER
    nodePercentGrid = Column(Float)  #: FLOAT

    # Relationship Properties
    gridStreamCell = relationship('GridStreamCell', back_populates='gridStreamNodes')  #: RELATIONSHIP

    def __init__(self, linkNumber, nodeNumber, nodePercentGrid):
        """
        Constructor
        """
        self.linkNumber = linkNumber
        self.nodeNumber = nodeNumber
        self.nodePercentGrid = nodePercentGrid

    def __repr__(self):
        return '<GridStreamNode: LinkNumber=%s, NodeNumber=%s, NodePercentGrid=%s>' % (
            self.linkNumber, self.nodeNumber, self.nodePercentGrid)
