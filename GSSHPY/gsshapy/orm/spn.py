'''
********************************************************************************
* Name: StormDrainNetwork
* Author: Nathan Swain
* Created On: May 14, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['StormPipeNetworkFile', 
           'SuperLink', 
           'SuperNode',
           'Pipe',
           'SuperJunction']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.lib import parsetools as pt, stormPipeChunk as spc


    
class StormPipeNetworkFile(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'spn_storm_pipe_network_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Relationship Properties
    superLinks = relationship('SuperLink', back_populates='stormPipeNetworkFile')
    superJunctions = relationship('SuperJunction', back_populates='stormPipeNetworkFile')
    projectFile = relationship('ProjectFile', uselist=False, back_populates='stormPipeNetworkFile')
    
    # Global Properties
    PATH = ''
    PROJECT_NAME = ''
    DIRECTORY = ''
    SESSION = None
    EXTENSION = 'spn'
    
    def __init__(self, name, directory, session):
        '''
        Constructor
        '''
        self.PROJECT_NAME = name
        self.DIRECTORY = directory
        self.SESSION = session
        self.PATH = '%s%s.%s' % (self.DIRECTORY, self.PROJECT_NAME, self.EXTENSION)
    
    def __repr__(self):
        return '<PipeNetwork: ID=%s>' %(self.id)
    
    def read(self):
        '''
        Storm Pipe Network File Read from File Method
        '''
        # Dictionary of keywords/cards and parse function names
        KEYWORDS = {'CONNECT': spc.connectChunk,
                    'SJUNC': spc.sjuncChunk,
                    'SLINK': spc.slinkChunk}
        
        sjuncs = []
        slinks = []
        connectivity = []
        # Parse file into chunks associated with keywords/cards
        with open(self.PATH, 'r') as f:
            chunks = pt.chunk(KEYWORDS, f)
            
        # Parse chunks associated with each key    
        for key, chunkList in chunks.iteritems():
            # Parse each chunk in the chunk list
            for chunk in chunkList:
                # Call chunk specific parsers for each chunk
                result = KEYWORDS[key](key, chunk)

                # Cases
                if key == 'CONNECT':
                    connectivity.append(result)
                elif key == 'SJUNC':
                    sjuncs.append(result)
                elif key == 'SLINK':
                    slinks.append(result)
                
        
    def write(self):
        '''
        Storm Pipe Network File Write to File Method
        '''
        



class SuperLink(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'spn_super_links'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    stormPipeNetworkFileID = Column(Integer, ForeignKey('spn_storm_pipe_network_files.id'))
    
    # Value Columns
    numPipes = Column(Integer, nullable=False)
    upstreamSJunct = Column(Integer, nullable=False)
    downstreamSJunct = Column(Integer, nullable=False)
    
    # Relationship Properties
    stormPipeNetworkFile = relationship('StormPipeNetworkFile', back_populates='superLinks')
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
    nodeNumber = Column(Integer, nullable=False)
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
    
    def __init__(self, nodeNumber, groundSurfaceElev, invertElev, manholeSA, nodeInletCode, cellI, cellJ, weirSideLength, orifaceDiameter):
        '''
        Constructor
        '''
        self.nodeNumber = nodeNumber
        self.groundSurfaceElev = groundSurfaceElev
        self.invertElev = invertElev
        self.manholeSA = manholeSA
        self.nodeInletCode = nodeInletCode
        self.cellI = cellI
        self.cellJ = cellJ
        self.weirSideLength = weirSideLength
        self.orifaceDiameter = orifaceDiameter

    def __repr__(self):
        return '<SuperNode: NodeNumber=%s, GroundSurfaceElev=%s, InvertElev=%s, ManholeSA=%s, NodeInletCode=%s, CellI=%s, CellJ=%s, WeirSideLength=%s, OrifaceDiameter=%s>' % (
                self.nodeNumber,
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
    pipeNumber = Column(Integer, nullable=False)
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
    
    def __init__(self, pipeNumber, xSecType, diameterOrHeight, width, slope, roughness, length, conductance, drainSpacing):
        '''
        Constructor
        '''
        self.pipeNumber = pipeNumber
        self.xSecType = xSecType
        self.diameterOrHeight= diameterOrHeight
        self.width = width,
        self.slope = slope,
        self.roughness = roughness,
        self.length = length,
        self.conductance = conductance,
        self.drainSpacing = drainSpacing

    def __repr__(self):
        return '<Pipe: PipeNumber=%s, XSecType=%s, DiameterOrHeight=%s, Width=%s, Slope=%s, Roughness=%s, Length=%s, Conductance=%s, DrainSpacing=%s>' % (
                self.pipeNumber,
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
    stormPipeNetworkFileID = Column(Integer, ForeignKey('spn_storm_pipe_network_files.id'))
    
    # Value Columns
    sjuncNumber = Column(Integer, nullable=False)
    groundSurfaceElev = Column(Float, nullable=False)
    invertElev = Column(Float, nullable=False)
    manholeSA = Column(Float, nullable=False)
    inletCode = Column(Integer, nullable=False)
    linkOrCellI = Column(Integer, nullable=False)
    nodeOrCellJ = Column(Integer, nullable=False)
    weirSideLength = Column(Float, nullable=False)
    orifaceDiameter = Column(Float, nullable=False)
    
    # Relationship Properties
    stormPipeNetworkFile = relationship('StormPipeNetworkFile', back_populates='superJunctions')
    
    def __init__(self, sjuncNumber, groundSurfaceElev, invertElev, manholeSA, inletCode, linkOrCellI, nodeOrCellJ, weirSideLength, orifaceDiameter):
        '''
        Constructor
        '''
        self.sjuncNumber = sjuncNumber,
        self.groundSurfaceElev = groundSurfaceElev
        self.invertElev = invertElev
        self.manholeSA = manholeSA
        self.inletCode = inletCode
        self.linkOrCellI = linkOrCellI
        self.nodeOrCellJ = nodeOrCellJ
        self.weirSideLength = weirSideLength
        self.orifaceDiameter = orifaceDiameter

    def __repr__(self):
        return '<SuperJunction: SjuncNumber=%s, GroundSurfaceElev=%s, InvertElev=%s, ManholeSA=%s, InletCode=%s, LinkOrCellI=%s, NodeOrCellJ=%s, WeirSideLength=%s, OrifaceDiameter=%s>' % (
                self.sjuncNumber,
                self.groundSurfaceElev,
                self.invertElev,
                self.manholeSA,
                self.inletCode,
                self.linkOrCellI,
                self.nodeOrCellJ,
                self.weirSideLength,
                self.orifaceDiameter)