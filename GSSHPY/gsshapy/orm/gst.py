'''
********************************************************************************
* Name: GridToStream
* Author: Nathan Swain
* Created On: May 12, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

import os, sys
from datetime import datetime

__all__ = ['StreamGridCell']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, String, Float, Boolean
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase


    
class StreamGridCell(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gst_stream_grid_cells'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    linkID = Column(Integer, ForeignKey('cif_links.id'))
    
    # Value Columns
    cellI = Column(Integer, nullable=False)
    cellJ = Column(Integer, nullable=False)
    numNodes = Column(Integer, nullable=False)
    
    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='streamGridCells')
    streamGridNodes = relationship('StreamGridNode', back_populates='streamGridCell')
    
    def __init__(self, cellI, cellJ, numNodes):
        '''
        Constructor
        '''
        self.cellI = cellI
        self.cellJ = cellJ
        self.numNodes = numNodes

    def __repr__(self):
        return '<StreamGridCell: CellI=%s, CellJ=%s, NumNodes=%s>' % (self.cellI, self.cellJ, self.numNodes)
    
class StreamGridNode(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gst_stream_grid_nodes'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    streamGridCellID = Column(Integer, ForeignKey('gst_stream_grid_cells.id'))
    
    # Value Columns
    linkNode = Column(Integer, nullable=False)
    nodePercentGrid = Column(Float, nullable=False)
    
    # Relationship Properties
    streamGridCell = relationship('StreamGridCell', back_populates='streamGridNodes')
    
    def __init__(self, linkNode, nodePercentGrid):
        '''
        Constructor
        '''
        self.linkNode = linkNode
        self.nodePercentGrid = nodePercentGrid

    def __repr__(self):
        return '<StreamGridNode: LinkNode=%s, NodePercentGrid=%s>' % (self.linkNode, self.nodePercentGrid)
