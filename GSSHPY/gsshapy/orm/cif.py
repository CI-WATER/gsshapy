'''
********************************************************************************
* Name: StreamNetworkModel
* Author: Nathan Swain
* Created On: May 12, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

## TODO: Add capability to store RATING_CURVE, RULE_CURVE, and SCHEDULED_RELEASE data

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
from gsshapy.lib import parsetools as pt, cif_chunk as cic



class ChannelInputFile(DeclarativeBase):
    '''
    Channel Input File
    '''
    __tablename__ = 'cif_channel_input_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    alpha = Column(Float)
    beta = Column(Float)
    theta = Column(Float)
    links = Column(Integer)
    maxNodes = Column(Integer)
    
    # Relationship Properties
    projectFile = relationship('ProjectFile', uselist=False, back_populates='channelInputFile')
    streamLinks = relationship('StreamLink', back_populates='channelInputFile')
        
    # Global Properties
    PATH = ''
    FILENAME = ''
    DIRECTORY = ''
    SESSION = None
    EXTENSION = 'cif'
    
    def __init__(self, directory, filename, session, alpha=None, beta=None, theta=None, links=None, maxNodes=None):
        '''
        Constructor
        '''
        self.FILENAME = filename
        self.DIRECTORY = directory
        self.SESSION = session
        self.PATH = '%s%s' % (self.DIRECTORY, self.FILENAME)
        self.alpha = alpha
        self.beta = beta
        self.theta = theta
        self.links = links
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
                    'CONNECT':cic.connectChunk,
                    'LINK':cic.linkChunk}
        
        links = []
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
                if key == 'LINK':
                    # Link handler
                    links.append(self._createLink(result))
                    
                elif key == 'CONNECT':
                    # Connectivity handler
                    connectivity.append(result)
                    
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
        
        self._createConnectivity(linkList=links, connectList=connectivity)                
                    
        
    def write(self, session, directory, filename):
        '''
        Channel Input File Write to File Method
        '''
        # Initiate channel input file
        filePath = '%s%s' % (directory, filename)
        
        with open(filePath, 'w') as cifFile:
            cifFile.write('GSSHA_CHAN\n')
            
            cifFile.write('ALPHA%s%.6f\n' % (' '*7, self.alpha))
            cifFile.write('BETA%s%.6f\n' % (' '*8, self.beta))
            cifFile.write('THETA%s%.6f\n' % (' '*7, self.theta))
            cifFile.write('LINKS%s%s\n' % (' '*7, self.links))
            cifFile.write('MAXNODES%s%s\n' % (' '*4, self.maxNodes))
            
            # Retrieve StreamLinks
            links = self.streamLinks
            
            self._writeConnectivity(links, cifFile)
            self._writeLinks(links, cifFile)
        
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
            
        elif linkResult['type'] in ('RESERVOIR', 'LAKE'):
            # Reservoir/lake handler
            link = self._createReservoir(linkResult)

        return link

    
    def _createConnectivity(self, linkList, connectList):
        '''
        Create GSSHAPY Connect Object Method
        '''
        # Create StreamLink-Connectivity Pairs
        
        for idx, link in enumerate(linkList):
            
            connectivity = connectList[idx]
            
            # Initialize GSSHAPY UpstreamLink objects
            for upLink in connectivity['upLinks']:
                upstreamLink = UpstreamLink(upstreamLinkID=int(upLink))
                upstreamLink.streamLink = link
            
            link.downstreamLinkID = int(connectivity['downLink'])
            link.numUpstreamLinks = int(connectivity['numUpLinks'])
            
        
    def _createCrossSection(self, linkResult):
        '''
        Create GSSHAPY Cross Section Objects Method
        '''
        # Extract header variables from link result object
        header = linkResult['header']
        
        # Initialize GSSHAPY StreamLink object
        link = StreamLink(linkNumber=int(header['link']),
                          type=header['xSecType'],
                          numElements=header['nodes'],
                          dx=header['dx'],
                          erode=header['erode'],
                          subsurface=header['subsurface'])
        
        # Associate StreamLink with ChannelInputFile
        link.channelInputFile = self
        
        # Initialize GSSHAPY TrapezoidalCS or BreakpointCS objects
        xSection = linkResult['xSection']
        
        # Cases
        if link.type == 'TRAPEZOID':
            # Trapezoid cross section handler
            # Initialize GSSHPY TrapeziodalCS object
            trapezoidCS = TrapezoidalCS(mannings_n=xSection['mannings_n'],
                                        bottomWidth=xSection['bottom_width'],
                                        bankfullDepth=xSection['bankfull_depth'],
                                        sideSlope=xSection['side_slope'],
                                        mRiver=xSection['m_river'],
                                        kRiver=xSection['k_river'],
                                        erode=xSection['erode'],
                                        subsurface=xSection['subsurface'],
                                        maxErosion=xSection['max_erosion'])
            
            # Associate TrapezoidalCS with StreamLink
            trapezoidCS.streamLink = link
            
        elif link.type == 'BREAKPOINT':
            # Breakpoint cross section handler
            # Initialize GSSHAPY BreakpointCS objects
            breakpointCS = BreakpointCS(mannings_n=xSection['mannings_n'],
                                        numPairs=xSection['npairs'],
                                        numInterp=xSection['num_interp'],
                                        mRiver=xSection['m_river'],
                                        kRiver=xSection['k_river'],
                                        erode=xSection['erode'],
                                        subsurface=xSection['subsurface'],
                                        maxErosion=xSection['max_erosion'])
            
            # Associate BreakpointCS with StreamLink
            breakpointCS.streamLink = link

            # Create GSSHAPY Breakpoint objects
            for b in xSection['breakpoints']:
                breakpoint = Breakpoint(x=b['x'],
                                        y=b['y'])
                
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
        # Constants
        WEIRS = ('WEIR', 'SAG_WEIR')
    
        CULVERTS = ('ROUND_CULVERT', 'RECT_CULVERT')
    
        CURVES = ('RATING_CURVE', 'SCHEDULED_RELEASE', 'RULE_CURVE')
        
        header = linkResult['header']
        
        # Intialize GSSHAPY StreamLink object
        link = StreamLink(linkNumber=header['link'],
                          type=linkResult['type'],
                          numElements=header['numstructs'])
        
        # Assosciate StreamLink with ChannelInputFile
        link.channelInputFile = self
        
        # Create Structure objects
        for s in linkResult['structures']:
            structType = s['structtype']
            
            # Cases
            if structType in WEIRS:
                # Weir type handler
                # Initialize GSSHAPY Weir object
                weir = Weir(type=structType,
                            crestLength=s['crest_length'], 
                            crestLowElevation=s['crest_low_elev'], 
                            dischargeCoeffForward=s['discharge_coeff_forward'], 
                            dischargeCoeffReverse=s['discharge_coeff_reverse'], 
                            crestLowLocation=s['crest_low_loc'], 
                            steepSlope=s['steep_slope'], 
                            shallowSlope=s['shallow_slope'])
                
                # Associate Weir with StreamLink
                weir.streamLink = link
                
            elif structType in CULVERTS:
                # Culvert type handler
                # Initialize GSSHAPY Culvert object
                culvert = Culvert(type=structType,
                                  upstreamInvert=s['upinvert'], 
                                  downstreamInvert=s['downinvert'], 
                                  inletDischargeCoeff=s['inlet_disch_coeff'], 
                                  reverseFlowDischargeCoeff=s['rev_flow_disch_coeff'], 
                                  slope=s['slope'], 
                                  length=s['length'], 
                                  roughness=s['rough_coeff'], 
                                  diameter=s['diameter'], 
                                  width=s['width'], 
                                  height=s['height'])
                
                # Associate Culvert with StreamLink
                culvert.streamLink = link
            
            elif structType in CURVES:
                # Curve type handler
                pass
        
        
        return link
        
    def _createReservoir(self, linkResult):
        '''
        Create GSSHAPY Reservoir Objects Method
        '''
        # Extract header variables from link result object
        header = linkResult['header']
        
        
        # Cases
        if linkResult['type'] == 'LAKE':
            # Lake handler
            initWSE = header['initwse']
            minWSE = header['minwse']
            maxWSE = header['maxwse']
            numPts = header['numpts']
        
        elif linkResult['type'] == 'RESERVOIR':
            # Reservoir handler
            initWSE = header['res_initwse']
            minWSE = header['res_minwse']
            maxWSE = header['res_maxwse']
            numPts = header['res_numpts']
            
        # Initialize GSSHAPY Reservoir object
        reservoir = Reservoir(initWSE=initWSE,
                              minWSE=minWSE,
                              maxWSE=maxWSE)
        
        # Initialize GSSHAPY StreamLink object
        link = StreamLink(linkNumber=int(header['link']),
                          type=linkResult['type'],
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
    
    def _writeConnectivity(self, links, fileObject):
        '''
        Write Connectivity Lines to File Method
        '''
        for link in links:
            linkNum = link.linkNumber
            downLink = link.downstreamLinkID
            numUpLinks = link.numUpstreamLinks
            upLinks = []
            for upLink in link.upstreamLinks:
                upLinks.append(str(upLink.upstreamLinkID))
            
            line = 'CONNECT    %s    %s    %s    %s\n' % (linkNum, downLink, numUpLinks, '    '.join(upLinks))
            fileObject.write(line)
        
    def _writeLinks(self, links, fileObject):
        '''
        Write Link Lines to File Method
        '''
        for link in links:
            linkType = link.type
            fileObject.write('LINK           %s\n' % link.linkNumber)
            
            # Cases
            if linkType in ('TRAPEZOID', 'BREAKPOINT'):
                self._writeCrossSectionLink(link, fileObject)
                            
            elif linkType == 'STRUCTURE':
                self._writeStructureLink(link, fileObject)
                
            elif linkType in ('RESERVOIR', 'LAKE'):
                self._writeReservoirLink(link, fileObject)
                
            else:
                print 'OOPS'
                
            fileObject.write('\n')
    
    def _writeReservoirLink(self, link, fileObject):
        '''
        Write Reservoir/Lake Link to File Method
        '''
        fileObject.write('%s\n' % link.type)
        
        # Retrieve reservoir
        reservoir = link.reservoir
        
        # Cases
        if link.type == 'LAKE':
            # Lake handler
            fileObject.write('INITWSE      %.6f\n' % reservoir.initWSE)
            fileObject.write('MINWSE       %.6f\n' % reservoir.minWSE)
            fileObject.write('MAXWSE       %.6f\n' % reservoir.maxWSE)
            fileObject.write('NUMPTS       %s\n' % link.numElements)
        elif link.type == 'RESERVOIR':
            # Reservoir handler
            fileObject.write('RES_INITWSE      %.6f\n' % reservoir.initWSE)
            fileObject.write('RES_MINWSE       %.6f\n' % reservoir.minWSE)
            fileObject.write('RES_MAXWSE       %.6f\n' % reservoir.maxWSE)
            fileObject.write('RES_NUMPTS       %s\n' % link.numElements)
        
        # Retrieve reservoir points
        points = reservoir.reservoirPoints
        
        for idx, point in enumerate(points):
            if ((idx + 1) % 10) != 0:
                fileObject.write('%s  %s     ' % (point.i, point.j))
            else:
                fileObject.write('%s  %s\n' % (point.i, point.j))
        
        if (link.numElements % 10) != 0:
            fileObject.write('\n')
                    
    
    def _writeStructureLink(self, link, fileObject):
        '''
        Write Structure Link to File Method
        '''
        fileObject.write('%s\n' % link.type)
        fileObject.write('NUMSTRUCTS     %s\n' % link.numElements)
        
        # Retrieve lists of structures
        weirs = link.weirs
        culverts = link.culverts
        
        # Write weirs to file
        for weir in weirs:
            fileObject.write('STRUCTTYPE     %s\n' % weir.type)
            
            if weir.crestLength != None:
                fileObject.write('CREST_LENGTH             %.6f\n' % weir.crestLength)
            
            if weir.crestLowElevation != None:
                fileObject.write('CREST_LOW_ELEV           %.6f\n' % weir.crestLowElevation)
                
            if weir.dischargeCoeffForward != None:
                fileObject.write('DISCHARGE_COEFF_FORWARD  %.6f\n' % weir.dischargeCoeffForward)
                
            if weir.dischargeCoeffReverse != None:
                fileObject.write('DISCHARGE_COEFF_REVERSE  %.6f\n' % weir.dischargeCoeffReverse)
                
            if weir.crestLowLocation != None:
                fileObject.write('CREST_LOW_LOC            %s\n' % weir.crestLowLocation)
                
            if weir.steepSlope != None:
                fileObject.write('STEEP_SLOPE              %.6f\n' % weir.steepSlope)
                
            if weir.shallowSlope != None:
                fileObject.write('SHALLOW_SLOPE            %.6f\n' % weir.shallowSlope)
            
        # Write culverts to file
        for culvert in culverts:
            fileObject.write('STRUCTTYPE     %s\n' % culvert.type)
            
            if culvert.upstreamInvert != None:
                fileObject.write('UPINVERT                 %.6f\n' % culvert.upstreamInvert)
                
            if culvert.downstreamInvert != None:
                fileObject.write('DOWNINVERT               %.6f\n' % culvert.downstreamInvert)
                
            if culvert.inletDischargeCoeff != None:
                fileObject.write('INLET_DISCH_COEFF        %.6f\n' % culvert.inletDischargeCoeff)
                
            if culvert.reverseFlowDischargeCoeff != None:
                fileObject.write('REV_FLOW_DISCH_COEFF     %.6f\n' % culvert.reverseFlowDischargeCoeff)
                
            if culvert.slope != None:
                fileObject.write('SLOPE                    %.6f\n' % culvert.slope)
                
            if culvert.length != None:
                fileObject.write('LENGHT                   %.6f\n' % culvert.length)
                
            if culvert.roughness != None:
                fileObject.write('ROUGH_COEFF              %.6f\n' % culvert.roughness)
                
            if culvert.diameter != None:
                fileObject.write('DIAMETER                 %.6f\n' % culvert.diameter)
                
            if culvert.width != None:
                fileObject.write('WIDTH                    %.6f\n' % culvert.width)
                
            if culvert.height != None:
                fileObject.write('HEIGHT                   %.6f\n' % culvert.height)
        
            
    def _writeCrossSectionLink(self, link, fileObject):
        '''
        Write Cross Section Link to File Method
        '''
        linkType = link.type
        
        # Write cross section link header
        fileObject.write('DX             %.6f\n' % link.dx)
        fileObject.write('%s\n' % linkType)
        fileObject.write('NODES          %s\n' % link.numElements)
        
        for node in link.nodes:
            # Write node information
            fileObject.write('NODE %s\n' % node.nodeNumber)
            fileObject.write('X_Y  %.6f %.6f\n' % (node.x, node.y))
            fileObject.write('ELEV %.6f\n' % node.elevation)
            
            if node.nodeNumber == 1:
                # Write cross section information after first node
                fileObject.write('XSEC\n')
                
                # Cases
                if linkType == 'TRAPEZOID':
                    # Retrieve cross section
                    xSec = link.trapezoidalCS
                    
                    # Write cross section properties
                    fileObject.write('MANNINGS_N     %.6f\n' % xSec.mannings_n)
                    fileObject.write('BOTTOM_WIDTH   %.6f\n' % xSec.bottomWidth)
                    fileObject.write('BANKFULL_DEPTH %.6f\n' % xSec.bankfullDepth)
                    fileObject.write('SIDE_SLOPE     %.6f\n' % xSec.sideSlope)
                    
                    # Write optional cross section properties
                    self._writeOptionalXsecCards(fileObject=fileObject, xSec=xSec)
                                    
                elif linkType == 'BREAKPOINT':
                    # Retrieve cross section
                    xSec = link.breakpointCS
                    
                    # Write cross section properties
                    fileObject.write('MANNINGS_N     %.6f\n' % xSec.mannings_n)
                    fileObject.write('NPAIRS         %s\n' % xSec.numPairs)
                    fileObject.write('NUM_INTERP     %s\n' % xSec.numInterp)
                    
                    # Write optional cross section properties
                    self._writeOptionalXsecCards(fileObject=fileObject, xSec=xSec)
                    
                    # Write breakpoint lines
                    for bp in xSec.breakpoints:
                        fileObject.write('X1   %.6f %.6f\n' % (bp.x, bp.y))

    def _writeOptionalXsecCards(self, fileObject, xSec):
        '''
        Write Optional Cross Section Cards to File Method
        '''
        if xSec.erode:
            fileObject.write('ERODE\n')
            
        if xSec.maxErosion != None: 
            fileObject.write('MAX_EROSION    %.6f\n' % xSec.maxErosion)
        
        if xSec.subsurface:
            fileObject.write('SUBSURFACE\n')
            
        if xSec.mRiver != None: 
            fileObject.write('M_RIVER        %.6f\n' % xSec.mRiver)
            
        if xSec.kRiver != None: 
            fileObject.write('K_RIVER        %.6f\n' % xSec.kRiver)
            
        
    

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
    type = Column(String, nullable=False)
    numElements = Column(Integer, nullable=False)
    dx = Column(Float)
    erode = Column(Boolean)
    subsurface = Column(Boolean)
    downstreamLinkID = Column(Integer)
    numUpstreamLinks = Column(Integer)

    # Relationship Properties
    channelInputFile = relationship('ChannelInputFile', back_populates='streamLinks')
    upstreamLinks = relationship('UpstreamLink', back_populates='streamLink')
    nodes = relationship('StreamNode', back_populates='streamLink')
    weirs = relationship('Weir', back_populates='streamLink')
    culverts = relationship('Culvert', back_populates='streamLink')
    reservoir = relationship('Reservoir', uselist=False, back_populates='streamLink')
    breakpointCS = relationship('BreakpointCS', uselist=False, back_populates='streamLink')
    trapezoidalCS = relationship('TrapezoidalCS', uselist=False, back_populates='streamLink')
    
    def __init__(self, linkNumber, type, numElements, dx=None, erode=False, subsurface=False):
        '''
        Constructor
        '''
        self.linkNumber = linkNumber
        self.type = type
        self.numElements = numElements
        self.dx = dx  
        self.erode = erode
        self.subsurface = subsurface    
        

    def __repr__(self):
        return '<StreamLink: LinkNumber=%s, Type=%s, NumberElements=%s, DX=%s, Erode=%s, Subsurface=%s, DownstreamLinkID=%s, NumUpstreamLinks=%s>' % (
                self.linkNumber,
                self.type,
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
        
    def __repr__(self):
        return '<UpstreamLink: LinkID=%s, UpstreamLinkID=%s>' % (self.linkID, self.upstreamLinkID)
        

    
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
    type = Column(String)
    crestLength = Column(Float)
    crestLowElevation = Column(Float)
    dischargeCoeffForward = Column(Float)
    dischargeCoeffReverse = Column(Float)
    crestLowLocation = Column(Float)
    steepSlope = Column(Float)
    shallowSlope = Column(Float)
    
    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='weirs')

    
    def __init__(self, type, crestLength, crestLowElevation, dischargeCoeffForward, dischargeCoeffReverse, crestLowLocation, steepSlope, shallowSlope):
        '''
        Constructor
        '''
        self.type = type
        self.crestLength = crestLength
        self.crestLowElevation = crestLowElevation
        self.dischargeCoeffForward = dischargeCoeffForward
        self.dischargeCoeffReverse = dischargeCoeffReverse
        self.crestLowLocation = crestLowLocation
        self.steepSlope = steepSlope
        self.shallowSlope = shallowSlope
       
        

    def __repr__(self):
        return '<Weir: Type=%s, CrestLenght=%s, CrestLowElevation=%s, DischargeCoeffForward=%s, DischargeCoeffReverse=%s, CrestLowLocation=%s, SteepSlope=%s, ShallowSlope=%s>' % (
               self.type,
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
    type = Column(String)
    upstreamInvert = Column(Float)
    downstreamInvert = Column(Float)
    inletDischargeCoeff = Column(Float)
    reverseFlowDischargeCoeff = Column(Float)
    slope = Column(Float)
    length = Column(Float)
    roughness = Column(Float)
    diameter = Column(Float)
    width = Column(Float)
    height = Column(Float)
    
    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='culverts')
    
    def __init__(self, type, upstreamInvert, downstreamInvert, inletDischargeCoeff, reverseFlowDischargeCoeff, slope, length, roughness, diameter, width, height):
        '''
        Constructor
        '''
        self.type = type
        self.upstreamInvert = upstreamInvert
        self.downstreamInvert = downstreamInvert
        self.inletDischargeCoeff = inletDischargeCoeff
        self.reverseFlowDischargeCoeff = reverseFlowDischargeCoeff
        self.slope = slope
        self.length = length
        self.roughness = roughness
        self.diameter = diameter
        self.width = width
        self.height = height        

    def __repr__(self):
        return '<Culvert: Type=%s, UpstreamInvert=%s, DownstreamInvert=%s, InletDischargeCoeff=%s, ReverseFlowDischargeCoeff=%s, Slope=%s, Length=%s, Roughness=%s, Diameter=%s, Width=%s, Height=%s>' % (
                self.type,
                self.upstreamInvert,
                self.downstreamInvert,
                self.inletDischargeCoeff,
                self.reverseFlowDischargeCoeff,
                self.slope,
                self.length,
                self.roughness,
                self.diameter,
                self.width,
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
    streamLink = relationship('StreamLink', back_populates='reservoir')
    reservoirPoints = relationship('ReservoirPoint', back_populates='reservoir')
    
    def __init__(self, initWSE, minWSE, maxWSE):
        '''
        Constructor
        '''
        self.initWSE = initWSE
        self.minWSE = minWSE
        self.maxWSE = maxWSE

    def __repr__(self):
        return '<Reservoir: InitialWSE=%s, MinWSE=%s, MaxWSE=%s>' % (self.initWSE, self.minWSE, self.maxWSE)
    


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
    numInterp = Column(Integer)
    mRiver = Column(Float)
    kRiver = Column(Float)
    erode = Column(Boolean)
    subsurface = Column(Boolean)
    maxErosion = Column(Float)
    
    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='breakpointCS')
    breakpoints = relationship('Breakpoint', back_populates='crossSection')
    
    def __init__(self, mannings_n, numPairs, numInterp, mRiver, kRiver, erode, subsurface, maxErosion):
        '''
        Constructor
        '''
        self.mannings_n = mannings_n
        self.numPairs = numPairs
        self.numInterp = numInterp
        self.mRiver = mRiver
        self.kRiver = kRiver
        self.erode = erode
        self.subsurface = subsurface
        self.maxErosion = maxErosion

    def __repr__(self):
        return '<BreakpointCrossSection: Mannings-n=%s, NumPairs=%s, NumInterp=%s, M-River=%s, K-River=%s, Erode=%s, Subsurface=%s, MaxErosion=%s>' % (
                self.mannings_n, 
                self.numPairs, 
                self.numInterp, 
                self.mRiver, 
                self.kRiver, 
                self.erode, 
                self.subsurface,
                self.maxErosion)
    
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
    maxErosion = Column(Float)
    
    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='trapezoidalCS')
    
    def __init__(self, mannings_n, bottomWidth, bankfullDepth, sideSlope, mRiver, kRiver, erode, subsurface, maxErosion):
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
        self.maxErosion = maxErosion

    def __repr__(self):
        return '<TrapezoidalCS: Mannings-n=%s, BottomWidth=%s, BankfullDepth=%s, SideSlope=%s, M-River=%s, K-River=%s, Erode=%s, Subsurface=%s, MaxErosion=%s>' % (
                self.mannings_n,
                self.bottomWidth,
                self.bankfullDepth,
                self.sideSlope,
                self.mRiver,
                self.kRiver,
                self.erode,
                self.subsurface,
                self.maxErosion)
        