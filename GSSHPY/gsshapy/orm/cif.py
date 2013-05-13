'''
********************************************************************************
* Name: StreamNetwork
* Author: Nathan Swain
* Created On: Mar 6, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

import os, sys
from datetime import datetime

__all__ = ['PrecipEvent','PrecipValue','PrecipGage']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, DateTime, String, Float
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase


class StreamLink(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_links'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    modelID = Column(Integer, ForeignKey('model_instances.id'))
    
    # Value Columns
    linkType = Column(String, nullable=False)
    numElements = Column(Integer, nullable=False)
    dx = Column(Float)

    # Relationship Properties
    model = relationship('ModelInstances', back_populates='streamLinks')
    connectivity = relationship('Connectivity', back_populates='streamLink')
    
    def __init__(self, linkType, numElements, dx):
        '''
        Constructor
        '''
        self.linkType = linkType
        self.numElements = numElements
        self.dx = dx      
        

    def __repr__(self):
        return '<StreamLink: LinkType=%s, NumberElements=%s, DX=%s>' % (self.linkType, self.numElements, self.dx)
    

class Connectivity(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_connectivity'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    linkID = Column(Integer, ForeignKey('cif_links.id'))

    # Value Columns
    downstreamLinkID = Column(Integer, nullable=False)
    numUpstreamLinks = Column(Integer, nullable=False)
    
    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='connectivity')
    upstreamLinks = relationship('UpstreamLink', back_populates='connectivity')
    
    def __init__(self, downstreamLinkID, numUpstreamLinks):
        '''
        Constructor
        '''
        self.downstreamLinkID = downstreamLinkID
        self.numUpstreamLinks = numUpstreamLinks

    def __repr__(self):
        return '<PrecipEvent: DownstreamLinkID=%s, NumUpstreamLinks=%s, UpstreamLinks=%s>' % (self.downstreamLinkID, self.numUpstreamLinks, self.upstreamLinks)
    
class UpstreamLink(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_upstream_links'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    linkID = Column(Integer, ForeignKey('cif_connectivity.linkID'))
    
    # Value Columns
    upstreamLinkID = Column(Integer, nullable=False)
    
    # Relationship Properties
    connectivity = relationship('Connectivity', back_populates='upstreamLinks')
    
    def __init__(self, upstreamLinkID):
        self.upstreamLinkID = upstreamLinkID

    
class Node(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_nodes'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    linkID = Column(Integer, ForeignKey('cif_links.id'))
    
    # Value Columns

    
    # Relationship Properties

    
    def __init__(self):
        '''
        Constructor
        '''
       
        

    def __repr__(self):
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.eventDesc,self.nrGag,self.nrPds)
    
    
class Structure(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_structures'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)

    
    # Value Columns

    
    # Relationship Properties

    
    def __init__(self):
        '''
        Constructor
        '''
       
        

    def __repr__(self):
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.eventDesc,self.nrGag,self.nrPds)
    
class Weir(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_weirs'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)

    
    # Value Columns

    
    # Relationship Properties

    
    def __init__(self):
        '''
        Constructor
        '''
       
        

    def __repr__(self):
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.eventDesc,self.nrGag,self.nrPds)
    
class Culvert(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_culverts'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)

    
    # Value Columns

    
    # Relationship Properties

    
    def __init__(self):
        '''
        Constructor
        '''
       
        

    def __repr__(self):
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.eventDesc,self.nrGag,self.nrPds)
    
class Reservoir(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_reservoirs'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)

    
    # Value Columns

    
    # Relationship Properties

    
    def __init__(self):
        '''
        Constructor
        '''
       
        

    def __repr__(self):
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.eventDesc,self.nrGag,self.nrPds)
    
class ReservoirPoints(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_reservoir_points'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)

    
    # Value Columns

    
    # Relationship Properties

    
    def __init__(self):
        '''
        Constructor
        '''
       
        

    def __repr__(self):
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.eventDesc,self.nrGag,self.nrPds)
    
class BreakpointCS(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_breakpoint'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)

    
    # Value Columns

    
    # Relationship Properties

    
    def __init__(self):
        '''
        Constructor
        '''
       
        

    def __repr__(self):
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.eventDesc,self.nrGag,self.nrPds)
    
class BCSPoints(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_bcs_points'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)

    
    # Value Columns

    
    # Relationship Properties

    
    def __init__(self):
        '''
        Constructor
        '''
       
        

    def __repr__(self):
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.eventDesc,self.nrGag,self.nrPds)
    
class TrapezoidalCS(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_trapeziod'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)

    
    # Value Columns

    
    # Relationship Properties

    
    def __init__(self):
        '''
        Constructor
        '''
       
        

    def __repr__(self):
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.eventDesc,self.nrGag,self.nrPds)
    
class Constants(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_contants'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)

    
    # Value Columns

    
    # Relationship Properties

    
    def __init__(self):
        '''
        Constructor
        '''
       
        

    def __repr__(self):
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.eventDesc,self.nrGag,self.nrPds)
    
