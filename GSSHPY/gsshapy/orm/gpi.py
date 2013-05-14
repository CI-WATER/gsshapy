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
           'PipeGridNode']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase


class PipeGridCell(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gpi_pipe_grid_cells'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    superLinkID = Column(Integer, ForeignKey('spn_super_links.id'))
    
    # Value Columns
    cellI = Column(Integer, nullable=False)
    cellJ = Column(Integer, nullable=False)
    numPipes = Column(Integer, nullable=False)
    
    # Relationship Properties
    superLink = relationship('SuperLink', back_populates='pipeGridCells')
    pipeGridNodes = relationship('PipeGridNode', back_populates='pipeGridCell')
    
    def __init__(self, cellI, cellJ, numPipes):
        '''
        Constructor
        '''
        self.cellI = cellI
        self.cellJ = cellJ
        self.numPipes = numPipes

    def __repr__(self):
        return '<PipeGridCell: CellI=%s, CellJ=%s, NumPipes=%s>' % (self.cellI, self.cellJ, self.numPipes)
    



class PipeGridNode(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gpi_pipe_grid_nodes'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    pipeGridCellID = Column(Integer, ForeignKey('gpi_pipe_grid_cells.id'))
    
    # Value Columns
    superLinkNode = Column(Integer, nullable=False)
    fractPipeLength = Column(Float, nullable=False)
    
    # Relationship Properties
    pipeGridCell = relationship('PipeGridCell', back_populates='pipeGridNodes')
    
    def __init__(self, superLinkNode, fractPipeLength):
        '''
        Constructor
        '''
        self.superLinkNode = superLinkNode
        self.fractPipeLength = fractPipeLength

    def __repr__(self):
        return '<PipeGridNode: SuperLinkNode=%s, FractPipeLength=%s>' % (self.superLinkNode, self.fractPipeLength)
    
    