'''
********************************************************************************
* Name: StreamNetwork
* Author: Nathan Swain
* Created On: May 12, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

from datetime import datetime



__all__ = ['ChannelInputFile', 
           'StreamLink', 
           'UpstreamLink', 
           'StreamNode', 
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
from gsshapy.lib import parsetools as pt, channelInputChunk as cic



class ChannelInputFile(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_channel_input_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    alpha = Column(Float)
    beta = Column(Float)
    theta = Column(Float)
    numLinks = Column(Integer)
    maxNodes = Column(Integer)
    
    # Relationship Properties
    projectFile = relationship('ProjectFile', uselist=False, back_populates='channelInputFile')
    streamLinks = relationship('StreamLink', back_populates='channelInputFile')
    
    # Global Properties
    PATH = ''
    PROJECT_NAME = ''
    DIRECTORY = ''
    SESSION = None
    
    def __init__(self, directory, name, session, alpha=None, beta=None, theta=None, numLinks=None, maxNodes=None):
        '''
        Constructor
        '''
        self.PROJECT_NAME = name
        self.DIRECTORY = directory
        self.SESSION = session
        self.PATH = '%s%s%s' % (self.DIRECTORY, self.PROJECT_NAME, '.cif')
        self.alpha = alpha
        self.beta = beta
        self.theta = theta
        self.numLinks = numLinks
        self.maxNodes = maxNodes
        
    def read(self):
        '''
        Channel Input File Read from File Method
        '''
        # Dictionary of keywords/cards and parse function names
        KEYWORDS = {'ALPHA': cic.cardChunk,
                    'BETA': cic.cardChunk,
                    'THETA': cic.cardChunk,
                    'LINKS': cic.cardChunk,
                    'MAXNODES': cic.cardChunk,
                    'CONNECT':cic.cardChunk,
                    'LINK':cic.linkChunk}
        
        links = []
        
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
                if key == 'LINK':
                    # Link handler
                    links.append(self._createLink(result))
                    
                elif key == 'CONNECT':
                    # Connectivity handler
                    print 'CONNECT_CHECK', result
                    
                else:
                    # Global variable handler
                    card = result['card']
                    value = result['values'][0]
                    # Cases
                    if card == 'LINKS':
                        self.links = int(value)
                    elif card == 'MAXNODES':
                        self.maxNodes = int(value)
                    elif card == 'ALPHA':
                        self.alpha = float(value)
                    elif card == 'BETA':
                        self.beta = float(value)
                    elif card == 'THETA':
                        self.theta = float(value)   
        
        for link in links:
            print link                 
                    
        
    def write(self):
        '''
        Channel Input File Write to File Method
        '''
        
    def _createLink(self, linkResult):
        '''
        Create GSSHAPY Link Object Method
        '''
        link = None
        
        # Cases
        if linkResult['type'] == 'XSEC':
            # Cross section link handler
            link = self._createCrossSection(linkResult)
            
        elif linkResult['type'] == 'STRUCTURE':
            # Structure link handler
            link = self._creatStructure(linkResult)
            
            for key, value in linkResult.iteritems():
                print key, value
            print '\n'
            
            for structure in linkResult['structures']:
                print structure
            print '\n'
            
        elif linkResult['type'] in ['RESERVOIR', 'LAKE']:
            # Reservoir/lake handler
            link = self._createReservoir(linkResult)
            
            
            
        return link

    
    def _createConnect(self, result):
        '''
        Create GSSHAPY Connect Object Method
        '''
        
    def _createCrossSection(self, linkResult):
        '''
        Create GSSHAPY Cross Section Objects Method
        '''
        # Extract header variables from link result object
        header = linkResult['header']
        
        # Initialize GSSHAPY StreamLink object
        link = StreamLink(linkNumber= int(header['link']),
                          linkType= header['xSecType'],
                          numElements= header['nodes'],
                          dx= header['dx'],
                          erode= header['erode'],
                          subsurface= header['subsurface'])
        
        # Associate StreamLink with ChannelInputFile
        link.channelInputFile = self
        
        # Initialize GSSHAPY TrapezoidalCS or BreakpointCS objects
        xSection = linkResult['xSection']
        
        # Cases
        if link.linkType == 'TRAPEZOID':
            # Trapezoid cross section handler
            # Initialize GSSHPY TrapeziodalCS object
            trapezoidCS = TrapezoidalCS(mannings_n = xSection['mannings_n'],
                                        bottomWidth = xSection['bottom_width'],
                                        bankfullDepth = xSection['bankfull_depth'],
                                        sideSlope = xSection['side_slope'],
                                        mRiver = xSection['m_river'],
                                        kRiver = xSection['k_river'],
                                        erode = xSection['erode'],
                                        subsurface = xSection['subsurface'])
            
            # Associate TrapezoidalCS with StreamLink
            trapezoidCS.streamLink = link
            
        elif link.linkType == 'BREAKPOINT':
            # Breakpoint cross section handler
            # Initialize GSSHAPY BreakpointCS objects
            breakpointCS = BreakpointCS(mannings_n = xSection['mannings_n'],
                                        numPairs = xSection['npairs'],
                                        numInterp = xSection['num_interp'],
                                        mRiver = xSection['m_river'],
                                        kRiver = xSection['k_river'],
                                        erode = xSection['erode'],
                                        subsurface = xSection['subsurface'])
            
            # Associate BreakpointCS with StreamLink
            breakpointCS.streamLink = link

            # Create GSSHAPY Breakpoint objects
            for b in xSection['breakpoints']:
                breakpoint = Breakpoint(x = b['x'],
                                        y = b['y'])
                
                # Associate Breakpoint with BreakpointCS
                breakpoint.crossSection = breakpointCS
                
        # Initialize GSSHAPY StreamNode objects
        for n in linkResult['nodes']:
            # Initialize GSSHAPY StreamNode object
            node  = StreamNode(nodeNumber=int(n['node']),
                               x=n['x'],
                               y=n['y'],
                               elevation=n['elev'])
            
            # Associate StreamNode with StreamLink
            node.streamLink = link
    
        return link
    
    def _creatStructure(self, linkResult):
        '''
        Create GSSHAPY Structure Objects Method
        '''
        link = None
        
        
        return link
        
    def _createReservoir(self, linkResult):
        # Extract header variables from link result object
        header = linkResult['header']
        
        # Initialize GSSHAPY Reservoir object
        # Cases
        if linkResult['type'] == 'LAKE':
            # Lake handler
            reservoir = Reservoir(initWSE=header['initwse'],
                                  minWSE=header['minwse'],
                                  maxWSE=header['maxwse'])
            
            numPts = header['numpts']
        
        elif linkResult['type'] == 'RESERVOIR':
            # Reservoir handler
            reservoir = Reservoir(initWSE=header['res_initwse'],
                                  minWSE=header['res_minwse'],
                                  maxWSE=header['res_maxwse'])
            
            numPts = header['res_numpts']
        
        # Initialize GSSHAPY StreamLink object
        link = StreamLink(linkNumber=int(header['link']),
                          linkType=linkResult['type'],
                          numElements=numPts)
        
        # Associate StreamLink with ChannelInputFile
        link.channelInputFile = self
        
        # Associate Reservoir with StreamLink
        reservoir.streamLink = link
        
        # Create ReservoirPoint objects
        for p in linkResult['points']:
            # Initialize GSSHAPY ResrvoirPoint object
            resPoint = ReservoirPoint(i=p['i'],
                                      j=p['j'])
            
            # Associate ReservoirPoint with Reservoir
            resPoint.reservoir = reservoir
        
        return link
        
    

class StreamLink(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_links'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    channelInputFileID = Column(Integer, ForeignKey('cif_channel_input_files.id'), nullable=False)
    
    # Value Columns
    linkNumber = Column(Integer, nullable=False)
    linkType = Column(String, nullable=False)
    numElements = Column(Integer, nullable=False)
    dx = Column(Float)
    erode = Column(Boolean)
    subsurface = Column(Boolean)
    downstreamLinkID = Column(Integer, nullable=False)
    numUpstreamLinks = Column(Integer, nullable=False)

    # Relationship Properties
    channelInputFile = relationship('ChannelInputFile', back_populates='streamLinks')
    upstreamLinks = relationship('UpstreamLink', back_populates='streamLink')
    nodes = relationship('StreamNode', back_populates='streamLink')
    weirs = relationship('Weir', back_populates='streamLink')
    culverts = relationship('Culvert', back_populates='streamLink')
    reservoirs = relationship('Reservoir', back_populates='streamLink')
    breakpointCS = relationship('BreakpointCS', back_populates='streamLink')
    trapezoidalCS = relationship('TrapezoidalCS', back_populates='streamLink')
    streamGridCells = relationship('StreamGridCell', back_populates='streamLink')
    
    def __init__(self, linkNumber, linkType, numElements, dx=None, erode=False, subsurface=False):
        '''
        Constructor
        '''
        self.linkNumber = linkNumber
        self.linkType = linkType
        self.numElements = numElements
        self.dx = dx  
        self.erode = erode
        self.subsurface = subsurface    
        

    def __repr__(self):
        return '<StreamLink: LinkNumber=%s, LinkType=%s, NumberElements=%s, DX=%s, Erode=%s, Subsurface=%s, DownstreamLinkID=%s, NumUpstreamLinks=%s>' % (
                self.linkNumber,
                self.linkType,
                self.numElements, 
                self.dx,
                self.erode,
                self.subsurface, 
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
        

    
class StreamNode(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cif_nodes'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    linkID = Column(Integer, ForeignKey('cif_links.id'))
    
    # Value Columns
    nodeNumber = Column(Integer, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    elevation = Column(Float, nullable=False)
    
    
    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='nodes')

    
    def __init__(self, nodeNumber, x, y, elevation):
        '''
        Constructor
        '''
        self.nodeNumber = nodeNumber
        self.x = x
        self.y = y
        self.elevation = elevation
        

    def __repr__(self):
        return '<Node: NodeNumber=%s, X=%s, Y=%s, Elevation=%s>' % (
                self.nodeNumber,
                self.x,
                self.y,
                self.elevation)
    
        
    
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
    
    def __init__(self, initWSE, minWSE, maxWSE):
        '''
        Constructor
        '''
        self.initWSE = initWSE
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
    i = Column(Integer, nullable=False)
    j = Column(Integer, nullable=False)
    
    # Relationship Properties
    reservoir = relationship('Reservoir', back_populates='reservoirPoints')
    
    def __init__(self, i, j):
        '''
        Constructor
        '''
        self.i = i
        self.j = j       

    def __repr__(self):
        return '<ReservoirPoint: CellI=%s, CellJ=%s>' % (self.i, self.j)
    



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
    
    def __init__(self, mannings_n, bottomWidth, bankfullDepth, sideSlope, mRiver, kRiver, erode, subsurface):
        '''
        Constructor
        '''
        self.mannings_n = mannings_n
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
        