'''
********************************************************************************
* Name: StormDrainNetwork
* Author: Nathan Swain
* Created On: May 14, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['PipeNetwork', 
           'SuperLink', 
           'SuperNode',
           'Pipe',
           'SuperJunction']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.scenario import scenarioPipeNetwork


    
class PipeNetwork(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'spn_pipe_networks'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    modelID = Column(Integer, ForeignKey('model_instances.id'))
    
    # Value Columns
    
    # Relationship Properties
    model = relationship('ModelInstance', back_populates='pipeNetwork')
    scenarios = relationship('Scenario', secondary=scenarioPipeNetwork, back_populates='pipeNetworks')
    superLinks = relationship('SuperLink', back_populates='pipeNetwork')
    superJunctions = relationship('SuperJunction', back_populates='pipeNetwork')
    
    def __init__(self):
        '''
        Constructor
        '''
    
    def __repr__(self):
        return '<PipeNetwork: ID=%s>' %(self.id)



class SuperLink(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'spn_super_links'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    pipeNetworkID = Column(Integer, ForeignKey('spn_pipe_networks.id'))
    
    # Value Columns
    numPipes = Column(Integer, nullable=False)
    upstreamSJunct = Column(Integer, nullable=False)
    downstreamSJunct = Column(Integer, nullable=False)
    
    # Relationship Properties
    pipeNetwork = relationship('PipeNetwork', back_populates='superLinks')
    superNodes = relationship('SuperNode', back_populates='superLink')
    pipes = relationship('Pipe', back_populates='superLink')
    pipeGridCells = relationship('PipeGridCell', back_populates='superLink')
    
    def __init__(self, numPipes, upstreamSJunct, downstreamSJunct):
        '''
        Constructor
        '''
        self.numPipes = numPipes
        self.upstreamSJunct = upstreamSJunct
        self.downstreamSJunct = downstreamSJunct

    def __repr__(self):
        return '<SuperLink: NumPipes=%s, UpstreamSuperJunct=%s, DownstreamSuperJucnt=%s>' % (
                self.numPipes, 
                self.upstreamSJunct, 
                self.downstreamSJunct)
    
    
    
    
class SuperNode(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'spn_super_nodes'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    superLinkID = Column(Integer, ForeignKey('spn_super_links.id'))
    
    # Value Columns
    superLinkNode = Column(Integer, nullable=False)
    groundSurfaceElev = Column(Float, nullable=False)
    invertElev = Column(Float, nullable=False)
    manholeSA = Column(Float, nullable=False)
    nodeInletCode = Column(Integer, nullable=False)
    cellI = Column(Integer, nullable=False)
    cellJ = Column(Integer, nullable=False)
    weirSideLength = Column(Float, nullable=False)
    orifaceDiameter = Column(Float, nullable=False)

    # Relationship Properties
    superLink = relationship('SuperLink', back_populates='superNodes')
    
    def __init__(self, superLinkNode, groundSurfaceElev, invertElev, manholeSA, nodeInletCode, cellI, cellJ, weirSideLength, orifaceDiameter):
        '''
        Constructor
        '''
        self.superLinkNode = superLinkNode
        self.groundSurfaceElev = groundSurfaceElev
        self.invertElev = invertElev
        self.manholeSA = manholeSA
        self.nodeInletCode = nodeInletCode
        self.cellI = cellI
        self.cellJ = cellJ
        self.weirSideLength = weirSideLength
        self.orifaceDiameter = orifaceDiameter

    def __repr__(self):
        return '<SuperNode: SuperLinkNode=%s, GroundSurfaceElev=%s, InvertElev=%s, ManholeSA=%s, NodeInletCode=%s, CellI=%s, CellJ=%s, WeirSideLength=%s, OrifaceDiameter=%s>' % (
                self.superLinkNode,
                self.groundSurfaceElev,
                self.invertElev,
                self.manholeSA,
                self.nodeInletCode,
                self.cellI,
                self.cellJ,
                self.weirSideLength,
                self.orifaceDiameter) 
    
    
    
class Pipe(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'spn_pipes'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    superLinkID = Column(Integer, ForeignKey('spn_super_links.id'))
    
    # Value Columns
    superLinkPipe = Column(Integer, nullable=False)
    xSecType = Column(Integer, nullable=False)
    diameterOrHeight = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    slope = Column(Float, nullable=False)
    roughness = Column(Float, nullable=False)
    length = Column(Float, nullable=False)
    conductance = Column(Float, nullable=False)
    drainSpacing = Column(Float, nullable=False)
    
    # Relationship Properties
    superLink = relationship('SuperLink', back_populates='pipes')
    
    def __init__(self, superLinkPipe, xSecType, diameterOrHeight, width, slope, roughness, length, conductance, drainSpacing):
        '''
        Constructor
        '''
        self.superLinkPipe = superLinkPipe
        self.xSecType = xSecType
        self.diameterOrHeight= diameterOrHeight
        self.width = width,
        self.slope = slope,
        self.roughness = roughness,
        self.length = length,
        self.conductance = conductance,
        self.drainSpacing = drainSpacing

    def __repr__(self):
        return '<Pipe: SuperLinkPipe=%s, XSecType=%s, DiameterOrHeight=%s, Width=%s, Slope=%s, Roughness=%s, Length=%s, Conductance=%s, DrainSpacing=%s>' % (
                self.superLinkPipe,
                self.xSecType,
                self.diameterOrHeight,
                self.width,
                self.slope,
                self.roughness,
                self.length,
                self.conductance,
                self.drainSpacing)
    
    


class SuperJunction(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'spn_super_junctions'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    pipeNetworkID = Column(Integer, ForeignKey('spn_pipe_networks.id'))
    
    # Value Columns
    groundSurfaceElev = Column(Float, nullable=False)
    invertElev = Column(Float, nullable=False)
    manholeSA = Column(Float, nullable=False)
    inletCode = Column(Integer, nullable=False)
    linkOrCellI = Column(Integer, nullable=False)
    nodeOrCellJ = Column(Integer, nullable=False)
    weirSideLength = Column(Float, nullable=False)
    orifaceDiameter = Column(Float, nullable=False)
    
    # Relationship Properties
    pipeNetwork = relationship('PipeNetwork', back_populates='superJunctions')
    
    def __init__(self, groundSurfaceElev, invertElev, manholeSA, inletCode, linkOrCellI, nodeOrCellJ, weirSideLength, orifaceDiameter):
        '''
        Constructor
        '''
        self.groundSurfaceElev = groundSurfaceElev
        self.invertElev = invertElev
        self.manholeSA = manholeSA
        self.inletCode = inletCode
        self.linkOrCellI = linkOrCellI
        self.nodeOrCellJ = nodeOrCellJ
        self.weirSideLength = weirSideLength
        self.orifaceDiameter = orifaceDiameter

    def __repr__(self):
        return '<SuperJunction: GroundSurfaceElev=%s, InvertElev=%s, ManholeSA=%s, InletCode=%s, LinkOrCellI=%s, NodeOrCellJ=%s, WeirSideLength=%s, OrifaceDiameter=%s>' % (
                self.groundSurfaceElev,
                self.invertElev,
                self.manholeSA,
                self.inletCode,
                self.linkOrCellI,
                self.nodeOrCellJ,
                self.weirSideLength,
                self.orifaceDiameter)