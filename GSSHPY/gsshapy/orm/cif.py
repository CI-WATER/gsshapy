'''
********************************************************************************
* Name: StreamNetwork
* Author: Nathan Swain
* Created On: May 12, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

import os, sys
from datetime import datetime

__all__ = ['StreamNetwork', 
           'StreamLink', 
           'UpstreamLink', 
           'Node', 
           'Weir', 
           'Culvert', 
           'Reservoir', 
           'ReservoirPoint', 
           'BreakpointCS', 
           'Breakpoint', 
           'TrapezoidalCS']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, String, Float, Boolean
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase

class StreamNetwork(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_stream_networks'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    alpha = Column(Float)
    beta = Column(Float)
    theta = Column(Float)
    numLinks = Column(Integer)
    maxNodes = Column(Integer)
    
    # Relationship Properties
    streamLinks = relationship('StreamLink', back_populates='streamNetwork')
    
    def __init__(self, alpha, beta, theta, numLinks, maxNodes):
        '''
        Constructor
        '''
        self.alpha = alpha
        self.beta = beta
        self.theta = theta
        self.numLinks = numLinks
        self.maxNodes = maxNodes

    def __repr__(self):
        return '<StreamNetwork: Alpha=%s, Beta=%s, Theta=%s, NumLinks=%s, MaxNodes=%s>' % (self.alpha, self.beta, self.theta, self.numLinks, self.maxNodes)
    

class StreamLink(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_links'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    streamNetworkID = Column(Integer, ForeignKey('cif_stream_networks.id'), nullable=False)
    
    # Value Columns
    linkType = Column(String, nullable=False)
    numElements = Column(Integer, nullable=False)
    dx = Column(Float)
    downstreamLinkID = Column(Integer, nullable=False)
    numUpstreamLinks = Column(Integer, nullable=False)

    # Relationship Properties
    streamNetwork = relationship('StreamNetwork', back_populates='streamLinks')
    upstreamLinks = relationship('UpstreamLink', back_populates='streamLink')
    nodes = relationship('Node', back_populates='streamLink')
    weirs = relationship('Weir', back_populates='streamLink')
    culverts = relationship('Culvert', back_populates='streamLink')
    reservoirs = relationship('Reservoir', back_populates='streamLink')
    breakpointCS = relationship('BreakpointCS', back_populates='streamLink')
    trapezoidalCS = relationship('TrapezoidalCS', back_populates='streamLink')
    streamGridCells = relationship('StreamGridCell', back_populates='streamLink')
    
    def __init__(self, linkType, numElements, dx, downstreamLinkID, numUpstreamLinks):
        '''
        Constructor
        '''
        self.linkType = linkType
        self.numElements = numElements
        self.dx = dx
        self.downstreamLinkID = downstreamLinkID
        self.numUpstreamLinks = numUpstreamLinks      
        

    def __repr__(self):
        return '<StreamLink: LinkType=%s, NumberElements=%s, DX=%s, DownstreamLinkID=%s, NumUpstreamLinks=%s>' % (
                self.linkType,
                self.numElements, 
                self.dx, 
                self.downstreamLinkID, 
                self.numUpstreamLinks)
    

    
class UpstreamLink(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_upstream_links'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    linkID = Column(Integer, ForeignKey('cif_links.id'))
    
    # Value Columns
    upstreamLinkID = Column(Integer, nullable=False)
    
    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='upstreamLinks')
    
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
    linkNode = Column(Integer, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    elevation = Column(Float, nullable=False)
    
    
    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='nodes')

    
    def __init__(self, linkNode, x, y, elevation):
        '''
        Constructor
        '''
        self.linkNode = linkNode
        self.x = x
        self.y = y
        self.elevation = elevation
        

    def __repr__(self):
        return '<Node: LinkNode=%s, X=%s, Y=%s, Elevation=%s>' % (self.linkNodeID, self.x, self.y, self.elevation)
    
        
    
class Weir(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_weirs'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    linkID = Column(Integer, ForeignKey('cif_links.id'))
    
    # Value Columns
    crestLength = Column(Float)
    crestLowElevation = Column(Float)
    dischargeCoeffForward = Column(Float)
    dischargeCoeffReverse = Column(Float)
    crestLowLocation = Column(Float)
    steepSlope = Column(Float)
    shallowSlope = Column(Float)
    
    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='weirs')

    
    def __init__(self, crestLength, crestLowElevation, dischargeCoeffForward, dischargeCoeffReverse, crestLowLocation, steepSlope, shallowSlope):
        '''
        Constructor
        '''
        self.crestLength = crestLength
        self.crestLowElevation = crestLowElevation
        self.dischargeCoeffForward = dischargeCoeffForward
        self.dischargeCoeffReverse = dischargeCoeffReverse
        self.crestLowLocation = crestLowLocation
        self.steepSlope = steepSlope
        self.shallowSlope = shallowSlope
       
        

    def __repr__(self):
        return '<Weir: CrestLenght=%s, CrestLowElevation=%s, DischargeCoeffForward=%s, DischargeCoeffReverse=%s, CrestLowLocation=%s, SteepSlope=%s, ShallowSlope=%s>' % (
               self.crestLength,
               self.crestLowElevation,
               self.dischargeCoeffForward,
               self.dischargeCoeffReverse,
               self.crestLowLocation,
               self.steepSlope,
               self.shallowSlope)
    
    

class Culvert(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_culverts'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    linkID = Column(Integer, ForeignKey('cif_links.id'))

    # Value Columns
    upstreamInvert = Column(Float)
    downstreamInvert = Column(Float)
    inletDischargeCoeff = Column(Float)
    reverseFlowDischargeCoeff = Column(Float)
    slope = Column(Float)
    length = Column(Float)
    roughness = Column(Float)
    widthOrDiameter = Column(Float)
    height = Column(Float)
    
    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='culverts')
    
    def __init__(self, upstreamInvert, downstreamInvert, inletDischargeCoeff, reverseFlowDischargeCoeff, slope, length, roughness, widthOrDiameter, height):
        '''
        Constructor
        '''
        self.upstreamInvert = upstreamInvert
        self.downstreamInvert = downstreamInvert
        self.inletDischargeCoeff = inletDischargeCoeff
        self.reverseFlowDischargeCoeff = reverseFlowDischargeCoeff
        self.slope = slope
        self.length = length
        self.roughness = roughness
        self.widthOrDiameter = widthOrDiameter
        self.height = height        

    def __repr__(self):
        return '<Culvert: UpstreamInvert=%s, DownstreamInvert=%s, InletDischargeCoeff=%s, ReverseFlowDischargeCoeff=%s, Slope=%s, Length=%s, Roughness=%s, WidthOrDiameter=%s, Height=%s>' % (
                self.upstreamInvert,
                self.downstreamInvert,
                self.inletDischargeCoeff,
                self.reverseFlowDischargeCoeff,
                self.slope,
                self.length,
                self.roughness,
                self.widthOrDiameter,
                self.height)
    


class Reservoir(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_reservoirs'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    linkID = Column(Integer, ForeignKey('cif_links.id'))
    
    # Value Columns
    initWSE = Column(Float)
    minWSE = Column(Float)
    maxWSE = Column(Float)
    
    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='reservoirs')
    reservoirPoints = relationship('ReservoirPoint', back_populates='reservoir')
    
    def __init__(self, initialWSE, minWSE, maxWSE):
        '''
        Constructor
        '''
        self.initWSE = initialWSE
        self.minWES = minWSE
        self.maxWSE = maxWSE

    def __repr__(self):
        return '<Reservoir: InitialWSE=%s, MinWSE=%s, MaxWSE=%s>' % (self.initWSE, self.minWES, self.maxWSE)
    


class ReservoirPoint(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_reservoir_points'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    reservoirID = Column(Integer, ForeignKey('cif_reservoirs.id'))
    
    # Value Columns
    cellI = Column(Integer, nullable=False)
    cellJ = Column(Integer, nullable=False)
    
    # Relationship Properties
    reservoir = relationship('Reservoir', back_populates='reservoirPoints')
    
    def __init__(self, cellI, cellJ):
        '''
        Constructor
        '''
        self.cellI = cellI
        self.cellJ = cellJ       

    def __repr__(self):
        return '<ReservoirPoint: CellI=%s, CellJ=%s>' % (self.cellI, self.cellJ)
    



class BreakpointCS(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_breakpoint'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    linkID = Column(Integer, ForeignKey('cif_links.id'))
    
    # Value Columns
    mannings_n = Column(Float)
    numPairs = Column(Integer)
    numInterp = Column(Float)
    mRiver = Column(Float)
    kRiver = Column(Float)
    erode = Column(Boolean)
    subsurface = Column(Boolean)
    
    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='breakpointCS')
    breakpoints = relationship('Breakpoint', back_populates='crossSection')
    
    def __init__(self, mannings_n, numPairs, numInterp, mRiver, kRiver, erode, subsurface):
        '''
        Constructor
        '''
        self.mannings_n = mannings_n
        self.numPairs = numPairs
        self.numInterp = numInterp
        self.mRiver = mRiver
        self.kRiver = kRiver
        self.erode = erode
        self.subsurface =subsurface

    def __repr__(self):
        return '<BreakpointCrossSection: Mannings-n=%s, NumPairs=%s, NumInterp=%s, M-River=%s, K-River=%s, Erode=%s, Subsurface=%s>' % (
                self.mannings_n, 
                self.numPairs, 
                self.numInterp, 
                self.mRiver, 
                self.kRiver, 
                self.erode, 
                self.subsurface)
    
class Breakpoint(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_bcs_points'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    crossSectionID = Column(Integer, ForeignKey('cif_breakpoint.id'))
    
    # Value Columns
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    
    # Relationship Properties
    crossSection = relationship('BreakpointCS', back_populates='breakpoints')
    
    def __init__(self, x, y):
        '''
        Constructor
        '''
        self.x = x
        self.y = y

    def __repr__(self):
        return '<Breakpoint: X=%s, Y=%s>' % (self.x, self.y)
    
    

    
class TrapezoidalCS(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_trapeziod'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    linkID = Column(Integer, ForeignKey('cif_links.id'))
    
    # Value Columns
    mannings_n = Column(Float)
    bottomWidth = Column(Float)
    bankfullDepth = Column(Float)
    sideSlope = Column(Float)
    mRiver = Column(Float)
    kRiver = Column(Float)
    erode = Column(Boolean)
    subsurface = Column(Boolean)
    
    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='trapezoidalCS')
    
    def __init__(self, manning_n, bottomWidth, bankfullDepth, sideSlope, mRiver, kRiver, erode, subsurface):
        '''
        Constructor
        '''
        self.mannings_n = manning_n
        self.bottomWidth = bottomWidth
        self.bankfullDepth = bankfullDepth
        self.sideSlope = sideSlope
        self.mRiver = mRiver
        self.kRiver = kRiver
        self.erode = erode
        self.subsurface = subsurface

    def __repr__(self):
        return '<TrapezoidalCS: Mannings-n=%s, BottomWidth=%s, BankfullDepth=%s, SideSlope=%s, M-River=%s, K-River=%s, Erode=%s, Subsurface=%s>' % (
                self.mannings_n,
                self.bottomWidth,
                self.bankfullDepth,
                self.sideSlope,
                self.mRiver,
                self.kRiver,
                self.erode,
                self.subsurface)
        