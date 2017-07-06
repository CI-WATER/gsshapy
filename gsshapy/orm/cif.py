"""
********************************************************************************
* Name: StreamNetworkModel
* Author: Nathan Swain
* Created On: May 12, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from __future__ import unicode_literals

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

from future.utils import iteritems
import logging
import json
from mapkit.sqlatypes import Geometry
from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, String, Float, Boolean
from sqlalchemy.orm import relationship
import xml.etree.ElementTree as ET

from . import DeclarativeBase
from ..base.geom import GeometricObjectBase
from ..base.file_base import GsshaPyFileObjectBase
from ..lib import parsetools as pt, cif_chunk as cic
from ..lib.parsetools import valueReadPreprocessor as vrp, valueWritePreprocessor as vwp

log = logging.getLogger(__name__)


class ChannelInputFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for the Channel Input File.

    The contents of the channel input file is abstracted into several objects including:
    :class:`.StreamLink`, :class:`.UpstreamLink`, :class:`.StreamNode`, :class:`.Weir`, :class:`.Culvert`,
    :class:`.Reservoir`, :class:`.ReservoirPoint`, :class:`.BreakpointCS`, :class:`.Breakpoint`, and
    :class:`.TrapezoidalCS`. See the documentation provided for each object for a more details.

    See: http://www.gsshawiki.com/Surface_Water_Routing:Channel_Routing
    """
    __tablename__ = 'cif_channel_input_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK

    # Value Columns
    alpha = Column(Float)  #: FLOAT
    beta = Column(Float)  #: FLOAT
    theta = Column(Float)  #: FLOAT
    links = Column(Integer)  #: INTEGER
    maxNodes = Column(Integer)  #: INTEGER
    fileExtension = Column(String, default='cif')  #: STRING

    # Relationship Properties
    projectFile = relationship('ProjectFile', uselist=False, back_populates='channelInputFile')  #: RELATIONSHIP
    streamLinks = relationship('StreamLink', back_populates='channelInputFile')  #: RELATIONSHIP
    linkNodeDatasets = relationship('LinkNodeDatasetFile', back_populates='channelInputFile')  #: RELATIONSHIP

    def __init__(self, alpha=None, beta=None, theta=None, links=None, maxNodes=None):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)
        self.alpha = alpha
        self.beta = beta
        self.theta = theta
        self.links = links
        self.maxNodes = maxNodes

    def __eq__(self, other):
        return (self.alpha == other.alpha and
                self.beta == other.beta and
                self.theta == other.theta and
                self.links == other.links and
                self.maxNodes == other.maxNodes)

    def getFluvialLinks(self):
        """
        Retrieve only the links that represent fluvial portions of the stream. Returns a list of StreamLink instances.

        Returns:
            list: A list of fluvial :class:`.StreamLink` objects.
        """
        # Define fluvial types
        fluvialTypeKeywords = ('TRAPEZOID', 'TRAP', 'BREAKPOINT', 'ERODE', 'SUBSURFACE')

        fluvialLinks = []

        for link in self.streamLinks:
            for fluvialTypeKeyword in fluvialTypeKeywords:
                if fluvialTypeKeyword in link.type:
                    fluvialLinks.append(link)
                    break

        return fluvialLinks

    def getOrderedLinks(self, session):
        """
        Retrieve the links in the order of the link number.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database.

        Returns:
            list: A list of :class:`.StreamLink` objects.
        """
        streamLinks = session.query(StreamLink).\
                            filter(StreamLink.channelInputFile == self).\
                            order_by(StreamLink.linkNumber).\
                            all()

        return streamLinks



    def getStreamNetworkAsKml(self, session, path=None, documentName='Stream Network', withNodes=False, styles={}):
        """
        Retrieve the stream network visualization in KML format.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            path (str, optional): Path to file where KML will be written. Defaults to None.
            documentName (str, optional): Name of the KML document. This will be the name that appears in the legend.
                Defaults to 'Stream Network'.
            withNodes (bool, optional): Include nodes. Defaults to False.
            styles (dict, optional): Custom styles to apply to KML geometry. Defaults to empty dictionary.

                Valid keys (styles) include:
                   * lineColor: tuple/list of RGBA integers (0-255) e.g.: (255, 0, 0, 128)
                   * lineWidth: float line width in pixels
                   * nodeIconHref: link to icon image (PNG format) to represent nodes (see: http://kml4earth.appspot.com/icons.html)
                   * nodeIconScale: scale of the icon image

        Returns:
            str: KML string
        """
        # Retrieve Stream Links
        links = self.getFluvialLinks()

        # Set Default Styles
        lineColorValue = (255, 255, 0, 0)  # Blue
        lineWidthValue = 2
        nodeIconHrefValue = 'http://maps.google.com/mapfiles/kml/paddle/red-circle.png'
        nodeIconScaleValue = 1.0

        if 'lineColor' in styles:
            if len(styles['lineColor']) < 4:
                log.warn('lineColor style must be a list or a tuple of four elements containing integer RGBA values.')
            else:
                userLineColor = styles['lineColor']
                lineColorValue = (userLineColor[3], userLineColor[2], userLineColor[1], userLineColor[0])

        if 'lineWidth' in styles:
            try:
                float(styles['lineWidth'])
                lineWidthValue = styles['lineWidth']

            except ValueError:
                log.warn('lineWidth must be a valid number containing the width of the line in pixels.')

        if 'nodeIconHref' in styles:
            nodeIconHrefValue = styles['nodeIconHref']

        if 'nodeIconScale' in styles:
            try:
                float(styles['nodeIconScale'])
                nodeIconScaleValue = styles['nodeIconScale']

            except ValueError:
                log.warn('nodeIconScaleValue must be a valid number containing the width of the line in pixels.')


        # Initialize KML Document
        kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
        document = ET.SubElement(kml, 'Document')
        docName = ET.SubElement(document, 'name')
        docName.text = documentName

        for link in links:
            placemark = ET.SubElement(document, 'Placemark')
            placemarkName = ET.SubElement(placemark, 'name')
            placemarkName.text = str(link.linkNumber)

            # Create style tag and setup styles
            styles = ET.SubElement(placemark, 'Style')

            # Set line style
            lineStyle = ET.SubElement(styles, 'LineStyle')
            lineColor = ET.SubElement(lineStyle, 'color')
            lineColor.text = '%02X%02X%02X%02X' % lineColorValue
            lineWidth = ET.SubElement(lineStyle, 'width')
            lineWidth.text = str(lineWidthValue)

            # Add the geometry to placemark
            linkKML = link.getAsKml(session)
            if linkKML:
                lineString = ET.fromstring(linkKML)
                placemark.append(lineString)
            else:
                log.warn("No geometry found for link with id {0}".format(link.id))

            if withNodes:
                # Create the node styles
                nodeStyles = ET.SubElement(document, 'Style', id='node_styles')

                # Hide labels
                nodeLabelStyle = ET.SubElement(nodeStyles, 'LabelStyle')
                nodeLabelScale = ET.SubElement(nodeLabelStyle, 'scale')
                nodeLabelScale.text = str(0)

                # Style icon
                nodeIconStyle = ET.SubElement(nodeStyles, 'IconStyle')

                # Set icon
                nodeIcon = ET.SubElement(nodeIconStyle, 'Icon')
                iconHref = ET.SubElement(nodeIcon, 'href')
                iconHref.text = nodeIconHrefValue

                # Set icon scale
                iconScale = ET.SubElement(nodeIconStyle, 'scale')
                iconScale.text = str(nodeIconScaleValue)

                for node in link.nodes:
                    # New placemark for each node
                    nodePlacemark = ET.SubElement(document, 'Placemark')
                    nodePlacemarkName = ET.SubElement(nodePlacemark, 'name')
                    nodePlacemarkName.text = str(node.nodeNumber)

                    # Styles for the node
                    nodeStyleUrl = ET.SubElement(nodePlacemark, 'styleUrl')
                    nodeStyleUrl.text = '#node_styles'

                    nodeString = ET.fromstring(node.getAsKml(session))
                    nodePlacemark.append(nodeString)

                    # Embed node data
                    nodeExtendedData = ET.SubElement(nodePlacemark, 'ExtendedData')

                    nodeNumberData = ET.SubElement(nodeExtendedData, 'Data', name='node_number')
                    nodeNumberValue = ET.SubElement(nodeNumberData, 'value')
                    nodeNumberValue.text = str(node.nodeNumber)

                    nodeLinkNumberData = ET.SubElement(nodeExtendedData, 'Data', name='link_number')
                    nodeLinkNumberValue = ET.SubElement(nodeLinkNumberData, 'value')
                    nodeLinkNumberValue.text = str(link.linkNumber)

                    nodeElevationData = ET.SubElement(nodeExtendedData, 'Data', name='elevation')
                    nodeElevationValue = ET.SubElement(nodeElevationData, 'value')
                    nodeElevationValue.text = str(node.elevation)

            # Create the data tag
            extendedData = ET.SubElement(placemark, 'ExtendedData')

            # Add value to data
            linkNumberData = ET.SubElement(extendedData, 'Data', name='link_number')
            linkNumberValue = ET.SubElement(linkNumberData, 'value')
            linkNumberValue.text = str(link.linkNumber)

            linkTypeData = ET.SubElement(extendedData, 'Data', name='link_type')
            linkTypeValue = ET.SubElement(linkTypeData, 'value')
            linkTypeValue.text = str(link.type)

            numElementsData = ET.SubElement(extendedData, 'Data', name='number_elements')
            numElementsValue = ET.SubElement(numElementsData, 'value')
            numElementsValue.text = str(link.numElements)

            dxData = ET.SubElement(extendedData, 'Data', name='dx')
            dxValue = ET.SubElement(dxData, 'value')
            dxValue.text = str(link.dx)

            erodeData = ET.SubElement(extendedData, 'Data', name='erode')
            erodeValue = ET.SubElement(erodeData, 'value')
            erodeValue.text = str(link.type)

            subsurfaceData = ET.SubElement(extendedData, 'Data', name='subsurface')
            subsurfaceValue = ET.SubElement(subsurfaceData, 'value')
            subsurfaceValue.text = str(link.type)

        kmlString = ET.tostring(kml)

        if path:
            with open(path, 'w') as f:
                f.write(kmlString)

        return kmlString

    def getStreamNetworkAsWkt(self, session, withNodes=True):
        """
        Retrieve the stream network geometry in Well Known Text format.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            withNodes (bool, optional): Include nodes. Defaults to False.

        Returns:
            str: Well Known Text string.
        """
        wkt_list = []

        for link in self.streamLinks:
            wkt_link = link.getAsWkt(session)

            if wkt_link:
                wkt_list.append(wkt_link)

            if withNodes:
                for node in link.nodes:
                    wkt_node = node.getAsWkt(session)

                    if wkt_node:
                        wkt_list.append(wkt_node)

        return 'GEOMCOLLECTION ({0})'.format(', '.join(wkt_list))

    def getStreamNetworkAsGeoJson(self, session, withNodes=True):
        """
        Retrieve the stream network geometry in GeoJSON format.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            withNodes (bool, optional): Include nodes. Defaults to False.

        Returns:
            str: GeoJSON string.
        """
        features_list = []

        # Assemble link features
        for link in self.streamLinks:
            link_geoJson = link.getAsGeoJson(session)

            if link_geoJson:
                link_geometry = json.loads(link.getAsGeoJson(session))

                link_properties = {"link_number": link.linkNumber,
                                   "type": link.type,
                                   "num_elements": link.numElements,
                                   "dx": link.dx,
                                   "erode": link.erode,
                                   "subsurface": link.subsurface}

                link_feature = {"type": "Feature",
                                "geometry": link_geometry,
                                "properties": link_properties,
                                "id": link.id}

                features_list.append(link_feature)

            # Assemble node features
            if withNodes:
                for node in link.nodes:
                    node_geoJson = node.getAsGeoJson(session)

                    if node_geoJson:
                        node_geometry = json.loads(node_geoJson)

                    node_properties = {"link_number": link.linkNumber,
                                       "node_number": node.nodeNumber,
                                       "elevation": node.elevation}

                    node_feature = {"type": "Feature",
                                    "geometry": node_geometry,
                                    "properties": node_properties,
                                    "id": node.id}

                    features_list.append(node_feature)

        feature_collection = {"type": "FeatureCollection",
                              "features": features_list}

        return json.dumps(feature_collection)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
        """
        Channel Input File Read from File Method
        """
        # Set file extension property
        self.fileExtension = extension

        # Dictionary of keywords/cards and parse function names
        KEYWORDS = {'ALPHA': cic.cardChunk,
                    'BETA': cic.cardChunk,
                    'THETA': cic.cardChunk,
                    'LINKS': cic.cardChunk,
                    'MAXNODES': cic.cardChunk,
                    'CONNECT': cic.connectChunk,
                    'LINK': cic.linkChunk}

        links = []
        connectivity = []

        # Parse file into chunks associated with keywords/cards
        with open(path, 'r') as f:
            chunks = pt.chunk(KEYWORDS, f)

        # Parse chunks associated with each key
        for key, chunkList in iteritems(chunks):
            # Parse each chunk in the chunk list
            for chunk in chunkList:
                # Call chunk specific parsers for each chunk
                result = KEYWORDS[key](key, chunk)

                # Cases
                if key == 'LINK':
                    # Link handler
                    links.append(self._createLink(result, replaceParamFile))

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
                        self.alpha = float(vrp(value, replaceParamFile))
                    elif card == 'BETA':
                        self.beta = float(vrp(value, replaceParamFile))
                    elif card == 'THETA':
                        self.theta = float(vrp(value, replaceParamFile))

        self._createConnectivity(linkList=links, connectList=connectivity)

        if spatial:
            self._createGeometry(session, spatialReferenceID)

    def _write(self, session, openFile, replaceParamFile):
        """
        Channel Input File Write to File Method
        """
        # Write lines
        openFile.write('GSSHA_CHAN\n')

        alpha = vwp(self.alpha, replaceParamFile)
        try:
            openFile.write('ALPHA%s%.6f\n' % (' ' * 7, alpha))
        except:
            openFile.write('ALPHA%s%s\n' % (' ' * 7, alpha))

        beta = vwp(self.beta, replaceParamFile)
        try:
            openFile.write('BETA%s%.6f\n' % (' ' * 8, beta))
        except:
            openFile.write('BETA%s%s\n' % (' ' * 8, beta))

        theta = vwp(self.theta, replaceParamFile)
        try:
            openFile.write('THETA%s%.6f\n' % (' ' * 7, theta))
        except:
            openFile.write('THETA%s%s\n' % (' ' * 7, theta))

        openFile.write('LINKS%s%s\n' % (' ' * 7, self.links))
        openFile.write('MAXNODES%s%s\n' % (' ' * 4, self.maxNodes))

        # Retrieve StreamLinks
        links = self.getOrderedLinks(session)

        self._writeConnectivity(links=links,
                                fileObject=openFile)
        self._writeLinks(links=links,
                         fileObject=openFile,
                         replaceParamFile=replaceParamFile)

    def _createLink(self, linkResult, replaceParamFile):
        """
        Create GSSHAPY Link Object Method
        """
        link = None

        # Cases
        if linkResult['type'] == 'XSEC':
            # Cross section link handler
            link = self._createCrossSection(linkResult, replaceParamFile)

        elif linkResult['type'] == 'STRUCTURE':
            # Structure link handler
            link = self._createStructure(linkResult, replaceParamFile)

        elif linkResult['type'] in ('RESERVOIR', 'LAKE'):
            # Reservoir/lake handler
            link = self._createReservoir(linkResult, replaceParamFile)

        return link


    def _createConnectivity(self, linkList, connectList):
        """
        Create GSSHAPY Connect Object Method
        """
        # Create StreamLink-Connectivity Pairs

        for idx, link in enumerate(linkList):

            connectivity = connectList[idx]

            # Initialize GSSHAPY UpstreamLink objects
            for upLink in connectivity['upLinks']:
                upstreamLink = UpstreamLink(upstreamLinkID=int(upLink))
                upstreamLink.streamLink = link

            link.downstreamLinkID = int(connectivity['downLink'])
            link.numUpstreamLinks = int(connectivity['numUpLinks'])


    def _createCrossSection(self, linkResult, replaceParamFile):
        """
        Create GSSHAPY Cross Section Objects Method
        """
        # Extract header variables from link result object
        header = linkResult['header']

        # Initialize GSSHAPY StreamLink object
        link = StreamLink(linkNumber=int(header['link']),
                          type=header['xSecType'],
                          numElements=header['nodes'],
                          dx=vrp(header['dx'], replaceParamFile),
                          erode=header['erode'],
                          subsurface=header['subsurface'])

        # Associate StreamLink with ChannelInputFile
        link.channelInputFile = self

        # Initialize GSSHAPY TrapezoidalCS or BreakpointCS objects
        xSection = linkResult['xSection']

        # Cases
        if 'TRAPEZOID' in link.type or 'TRAP' in link.type:
            # Trapezoid cross section handler
            # Initialize GSSHPY TrapeziodalCS object
            trapezoidCS = TrapezoidalCS(mannings_n=vrp(xSection['mannings_n'], replaceParamFile),
                                        bottomWidth=vrp(xSection['bottom_width'], replaceParamFile),
                                        bankfullDepth=vrp(xSection['bankfull_depth'], replaceParamFile),
                                        sideSlope=vrp(xSection['side_slope'], replaceParamFile),
                                        mRiver=vrp(xSection['m_river'], replaceParamFile),
                                        kRiver=vrp(xSection['k_river'], replaceParamFile),
                                        erode=xSection['erode'],
                                        subsurface=xSection['subsurface'],
                                        maxErosion=vrp(xSection['max_erosion'], replaceParamFile))

            # Associate TrapezoidalCS with StreamLink
            trapezoidCS.streamLink = link

        elif 'BREAKPOINT' in link.type:
            # Breakpoint cross section handler
            # Initialize GSSHAPY BreakpointCS objects
            breakpointCS = BreakpointCS(mannings_n=vrp(xSection['mannings_n'], replaceParamFile),
                                        numPairs=xSection['npairs'],
                                        numInterp=vrp(xSection['num_interp'], replaceParamFile),
                                        mRiver=vrp(xSection['m_river'], replaceParamFile),
                                        kRiver=vrp(xSection['k_river'], replaceParamFile),
                                        erode=xSection['erode'],
                                        subsurface=xSection['subsurface'],
                                        maxErosion=vrp(xSection['max_erosion'], replaceParamFile))

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
            node = StreamNode(nodeNumber=int(n['node']),
                              x=n['x'],
                              y=n['y'],
                              elevation=n['elev'])

            # Associate StreamNode with StreamLink
            node.streamLink = link

        return link

    def _createStructure(self, linkResult, replaceParamFile):
        """
        Create GSSHAPY Structure Objects Method
        """
        # Constants
        WEIRS = ('WEIR', 'SAG_WEIR')

        CULVERTS = ('ROUND_CULVERT', 'RECT_CULVERT')

        CURVES = ('RATING_CURVE', 'SCHEDULED_RELEASE', 'RULE_CURVE')

        header = linkResult['header']

        # Initialize GSSHAPY StreamLink object
        link = StreamLink(linkNumber=header['link'],
                          type=linkResult['type'],
                          numElements=header['numstructs'])

        # Associate StreamLink with ChannelInputFile
        link.channelInputFile = self

        # Create Structure objects
        for s in linkResult['structures']:
            structType = s['structtype']

            # Cases
            if structType in WEIRS:
                # Weir type handler
                # Initialize GSSHAPY Weir object
                weir = Weir(type=structType,
                            crestLength=vrp(s['crest_length'], replaceParamFile),
                            crestLowElevation=vrp(s['crest_low_elev'], replaceParamFile),
                            dischargeCoeffForward=vrp(s['discharge_coeff_forward'], replaceParamFile),
                            dischargeCoeffReverse=vrp(s['discharge_coeff_reverse'], replaceParamFile),
                            crestLowLocation=vrp(s['crest_low_loc'], replaceParamFile),
                            steepSlope=vrp(s['steep_slope'], replaceParamFile),
                            shallowSlope=vrp(s['shallow_slope'], replaceParamFile))

                # Associate Weir with StreamLink
                weir.streamLink = link

            elif structType in CULVERTS:
                # Culvert type handler
                # Initialize GSSHAPY Culvert object
                culvert = Culvert(type=structType,
                                  upstreamInvert=vrp(s['upinvert'], replaceParamFile),
                                  downstreamInvert=vrp(s['downinvert'], replaceParamFile),
                                  inletDischargeCoeff=vrp(s['inlet_disch_coeff'], replaceParamFile),
                                  reverseFlowDischargeCoeff=vrp(s['rev_flow_disch_coeff'], replaceParamFile),
                                  slope=vrp(s['slope'], replaceParamFile),
                                  length=vrp(s['length'], replaceParamFile),
                                  roughness=vrp(s['rough_coeff'], replaceParamFile),
                                  diameter=vrp(s['diameter'], replaceParamFile),
                                  width=vrp(s['width'], replaceParamFile),
                                  height=vrp(s['height'], replaceParamFile))

                # Associate Culvert with StreamLink
                culvert.streamLink = link

            elif structType in CURVES:
                # Curve type handler
                pass

        return link

    def _createReservoir(self, linkResult, replaceParamFile):
        """
        Create GSSHAPY Reservoir Objects Method
        """
        # Extract header variables from link result object
        header = linkResult['header']

        # Cases
        if linkResult['type'] == 'LAKE':
            # Lake handler
            initWSE = vrp(header['initwse'], replaceParamFile)
            minWSE = vrp(header['minwse'], replaceParamFile)
            maxWSE = vrp(header['maxwse'], replaceParamFile)
            numPts = header['numpts']

        elif linkResult['type'] == 'RESERVOIR':
            # Reservoir handler
            initWSE = vrp(header['res_initwse'], replaceParamFile)
            minWSE = vrp(header['res_minwse'], replaceParamFile)
            maxWSE = vrp(header['res_maxwse'], replaceParamFile)
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
            # Initialize GSSHAPY ReservoirPoint object
            resPoint = ReservoirPoint(i=p['i'],
                                      j=p['j'])

            # Associate ReservoirPoint with Reservoir
            resPoint.reservoir = reservoir

        return link

    def _createGeometry(self, session, spatialReferenceID):
        """
        Create PostGIS geometric objects
        """
        # Flush the current session
        session.flush()

        # Create geometry for each fluvial link
        for link in self.getFluvialLinks():

            # Retrieve the nodes for each link
            nodes = link.nodes
            nodeCoordinates = []

            # Create geometry for each node
            for node in nodes:
                # Assemble coordinates in well known text format
                coordinates = '{0} {1} {2}'.format(node.x, node.y, node.elevation)
                nodeCoordinates.append(coordinates)

                # Create well known text string for point with z coordinate
                wktPoint = 'POINT Z ({0})'.format(coordinates)

                # Write SQL statement
                statement = self._getUpdateGeometrySqlString(geometryID=node.id,
                                                             tableName=node.tableName,
                                                             spatialReferenceID=spatialReferenceID,
                                                             wktString=wktPoint)

                session.execute(statement)

            # Assemble line string in well known text format
            wktLineString = 'LINESTRING Z ({0})'.format(', '.join(nodeCoordinates))

            # Write SQL statement
            statement = self._getUpdateGeometrySqlString(geometryID=link.id,
                                                         tableName=link.tableName,
                                                         spatialReferenceID=spatialReferenceID,
                                                         wktString=wktLineString)

            session.execute(statement)

    def _writeConnectivity(self, links, fileObject):
        """
        Write Connectivity Lines to File Method
        """
        for link in links:
            linkNum = link.linkNumber
            downLink = link.downstreamLinkID
            numUpLinks = link.numUpstreamLinks
            upLinks = ''
            for upLink in link.upstreamLinks:
                upLinks = '{}{:>5}'.format(upLinks, str(upLink.upstreamLinkID))

            line = 'CONNECT{:>5}{:>5}{:>5}{}\n'.format(linkNum, downLink, numUpLinks, upLinks)
            fileObject.write(line)
        fileObject.write('\n')

    def _writeLinks(self, links, fileObject, replaceParamFile):
        """
        Write Link Lines to File Method
        """
        for link in links:
            linkType = link.type
            fileObject.write('LINK           %s\n' % link.linkNumber)

            # Cases
            if 'TRAP' in linkType or 'TRAPEZOID' in linkType or 'BREAKPOINT' in linkType:
                self._writeCrossSectionLink(link, fileObject, replaceParamFile)

            elif linkType == 'STRUCTURE':
                self._writeStructureLink(link, fileObject, replaceParamFile)

            elif linkType in ('RESERVOIR', 'LAKE'):
                self._writeReservoirLink(link, fileObject, replaceParamFile)

            else:
                log.error('OOPS: CIF LINE 417')  # THIS SHOULDN'T HAPPEN

            fileObject.write('\n')

    def _writeReservoirLink(self, link, fileObject, replaceParamFile):
        """
        Write Reservoir/Lake Link to File Method
        """
        fileObject.write('%s\n' % link.type)

        # Retrieve reservoir
        reservoir = link.reservoir

        # Reservoir parameters
        initWSE = vwp(reservoir.initWSE, replaceParamFile)
        minWSE = vwp(reservoir.minWSE, replaceParamFile)
        maxWSE = vwp(reservoir.maxWSE, replaceParamFile)
        numElements = link.numElements

        # Cases
        if link.type == 'LAKE':
            # Lake handler
            try:
                fileObject.write('INITWSE      %.6f\n' % initWSE)
            except:
                fileObject.write('INITWSE      %s\n' % initWSE)

            try:
                fileObject.write('MINWSE       %.6f\n' % minWSE)
            except:
                fileObject.write('MINWSE       %s\n' % minWSE)

            try:
                fileObject.write('MAXWSE       %.6f\n' % maxWSE)
            except:
                fileObject.write('MAXWSE       %s\n' % maxWSE)

            fileObject.write('NUMPTS       %s\n' % numElements)

        elif link.type == 'RESERVOIR':
            # Reservoir handler
            try:
                fileObject.write('RES_INITWSE      %.6f\n' % initWSE)
            except:
                fileObject.write('RES_INITWSE      %s\n' % initWSE)

            try:
                fileObject.write('RES_MINWSE       %.6f\n' % minWSE)
            except:
                fileObject.write('RES_MINWSE       %s\n' % minWSE)

            try:
                fileObject.write('RES_MAXWSE       %.6f\n' % maxWSE)
            except:
                fileObject.write('RES_MAXWSE       %s\n' % maxWSE)

            fileObject.write('RES_NUMPTS       %s\n' % numElements)

        # Retrieve reservoir points
        points = reservoir.reservoirPoints

        for idx, point in enumerate(points):
            if ((idx + 1) % 10) != 0:
                fileObject.write('%s  %s     ' % (point.i, point.j))
            else:
                fileObject.write('%s  %s\n' % (point.i, point.j))

        if (link.numElements % 10) != 0:
            fileObject.write('\n')


    def _writeStructureLink(self, link, fileObject, replaceParamFile):
        """
        Write Structure Link to File Method
        """
        fileObject.write('%s\n' % link.type)
        fileObject.write('NUMSTRUCTS     %s\n' % link.numElements)

        # Retrieve lists of structures
        weirs = link.weirs
        culverts = link.culverts

        # Write weirs to file
        for weir in weirs:
            fileObject.write('STRUCTTYPE     %s\n' % weir.type)

            # Check for replacement vars
            crestLength = vwp(weir.crestLength, replaceParamFile)
            crestLowElevation = vwp(weir.crestLowElevation, replaceParamFile)
            dischargeCoeffForward = vwp(weir.dischargeCoeffForward, replaceParamFile)
            dischargeCoeffReverse = vwp(weir.dischargeCoeffReverse, replaceParamFile)
            crestLowLocation = vwp(weir.crestLowLocation, replaceParamFile)
            steepSlope = vwp(weir.steepSlope, replaceParamFile)
            shallowSlope = vwp(weir.shallowSlope, replaceParamFile)

            if weir.crestLength != None:
                try:
                    fileObject.write('CREST_LENGTH             %.6f\n' % crestLength)
                except:
                    fileObject.write('CREST_LENGTH             %s\n' % crestLength)

            if weir.crestLowElevation != None:
                try:
                    fileObject.write('CREST_LOW_ELEV           %.6f\n' % crestLowElevation)
                except:
                    fileObject.write('CREST_LOW_ELEV           %s\n' % crestLowElevation)

            if weir.dischargeCoeffForward != None:
                try:
                    fileObject.write('DISCHARGE_COEFF_FORWARD  %.6f\n' % dischargeCoeffForward)
                except:
                    fileObject.write('DISCHARGE_COEFF_FORWARD  %s\n' % dischargeCoeffForward)

            if weir.dischargeCoeffReverse != None:
                try:
                    fileObject.write('DISCHARGE_COEFF_REVERSE  %.6f\n' % dischargeCoeffReverse)
                except:
                    fileObject.write('DISCHARGE_COEFF_REVERSE  %s\n' % dischargeCoeffReverse)

            if weir.crestLowLocation != None:
                    fileObject.write('CREST_LOW_LOC            %s\n' % crestLowLocation)

            if weir.steepSlope != None:
                try:
                    fileObject.write('STEEP_SLOPE              %.6f\n' % steepSlope)
                except:
                    fileObject.write('STEEP_SLOPE              %s\n' % steepSlope)

            if weir.shallowSlope != None:
                try:
                    fileObject.write('SHALLOW_SLOPE            %.6f\n' % shallowSlope)
                except:
                    fileObject.write('SHALLOW_SLOPE            %s\n' % shallowSlope)

        # Write culverts to file
        for culvert in culverts:
            fileObject.write('STRUCTTYPE     %s\n' % culvert.type)

            # Check for replacement vars
            upstreamInvert = vwp(culvert.upstreamInvert, replaceParamFile)
            downstreamInvert = vwp(culvert.downstreamInvert, replaceParamFile)
            inletDischargeCoeff = vwp(culvert.inletDischargeCoeff, replaceParamFile)
            reverseFlowDischargeCoeff = vwp(culvert.reverseFlowDischargeCoeff, replaceParamFile)
            slope = vwp(culvert.slope, replaceParamFile)
            length = vwp(culvert.length, replaceParamFile)
            roughness = vwp(culvert.roughness, replaceParamFile)
            diameter = vwp(culvert.diameter, replaceParamFile)
            width = vwp(culvert.width, replaceParamFile)
            height = vwp(culvert.height, replaceParamFile)

            if culvert.upstreamInvert != None:
                try:
                    fileObject.write('UPINVERT                 %.6f\n' % upstreamInvert)
                except:
                    fileObject.write('UPINVERT                 %s\n' % upstreamInvert)

            if culvert.downstreamInvert != None:
                try:
                    fileObject.write('DOWNINVERT               %.6f\n' % downstreamInvert)
                except:
                    fileObject.write('DOWNINVERT               %s\n' % downstreamInvert)

            if culvert.inletDischargeCoeff != None:
                try:
                    fileObject.write('INLET_DISCH_COEFF        %.6f\n' % inletDischargeCoeff)
                except:
                    fileObject.write('INLET_DISCH_COEFF        %s\n' % inletDischargeCoeff)

            if culvert.reverseFlowDischargeCoeff != None:
                try:
                    fileObject.write('REV_FLOW_DISCH_COEFF     %.6f\n' % reverseFlowDischargeCoeff)
                except:
                    fileObject.write('REV_FLOW_DISCH_COEFF     %s\n' % reverseFlowDischargeCoeff)

            if culvert.slope != None:
                try:
                    fileObject.write('SLOPE                    %.6f\n' % slope)
                except:
                    fileObject.write('SLOPE                    %s\n' % slope)

            if culvert.length != None:
                try:
                    fileObject.write('LENGTH                   %.6f\n' % length)
                except:
                    fileObject.write('LENGTH                   %s\n' % length)

            if culvert.roughness != None:
                try:
                    fileObject.write('ROUGH_COEFF              %.6f\n' % roughness)
                except:
                    fileObject.write('ROUGH_COEFF              %s\n' % roughness)

            if culvert.diameter != None:
                try:
                    fileObject.write('DIAMETER                 %.6f\n' % diameter)
                except:
                    fileObject.write('DIAMETER                 %s\n' % diameter)


            if culvert.width != None:
                try:
                    fileObject.write('WIDTH                    %.6f\n' % width)
                except:
                    fileObject.write('WIDTH                    %s\n' % width)

            if culvert.height != None:
                try:
                    fileObject.write('HEIGHT                   %.6f\n' % height)
                except:
                    fileObject.write('HEIGHT                   %s\n' % height)

    def _writeCrossSectionLink(self, link, fileObject, replaceParamFile):
        """
        Write Cross Section Link to File Method
        """
        linkType = link.type

        # Write cross section link header
        dx = vwp(link.dx, replaceParamFile)
        try:
            fileObject.write('DX             %.6f\n' % dx)
        except:
            fileObject.write('DX             %s\n' % dx)

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
                if 'TRAPEZOID' in linkType or 'TRAP' in linkType:
                    # Retrieve cross section
                    xSec = link.trapezoidalCS

                    # Write cross section properties
                    mannings_n = vwp(xSec.mannings_n, replaceParamFile)
                    bottomWidth = vwp(xSec.bottomWidth, replaceParamFile)
                    bankfullDepth = vwp(xSec.bankfullDepth, replaceParamFile)
                    sideSlope = vwp(xSec.sideSlope, replaceParamFile)

                    try:
                        fileObject.write('MANNINGS_N     %.6f\n' % mannings_n)
                    except:
                        fileObject.write('MANNINGS_N     %s\n' % mannings_n)

                    try:
                        fileObject.write('BOTTOM_WIDTH   %.6f\n' % bottomWidth)
                    except:
                        fileObject.write('BOTTOM_WIDTH   %s\n' % bottomWidth)

                    try:
                        fileObject.write('BANKFULL_DEPTH %.6f\n' % bankfullDepth)
                    except:
                        fileObject.write('BANKFULL_DEPTH %s\n' % bankfullDepth)

                    try:
                        fileObject.write('SIDE_SLOPE     %.6f\n' % sideSlope)
                    except:
                        fileObject.write('SIDE_SLOPE     %s\n' % sideSlope)

                    # Write optional cross section properties
                    self._writeOptionalXsecCards(fileObject=fileObject, xSec=xSec, replaceParamFile=replaceParamFile)

                elif 'BREAKPOINT' in linkType:
                    # Retrieve cross section
                    xSec = link.breakpointCS

                    # Write cross section properties
                    mannings_n = vwp(xSec.mannings_n, replaceParamFile)
                    try:
                        fileObject.write('MANNINGS_N     %.6f\n' % mannings_n)
                    except:
                        fileObject.write('MANNINGS_N     %s\n' % mannings_n)

                    fileObject.write('NPAIRS         %s\n' % xSec.numPairs)
                    fileObject.write('NUM_INTERP     %s\n' % vwp(xSec.numInterp, replaceParamFile))


                    # Write optional cross section properties
                    self._writeOptionalXsecCards(fileObject=fileObject, xSec=xSec, replaceParamFile=replaceParamFile)

                    # Write breakpoint lines
                    for bp in xSec.breakpoints:
                        fileObject.write('X1   %.6f %.6f\n' % (bp.x, bp.y))
                else:
                    log.error('OOPS: MISSED A CROSS SECTION TYPE. CIF LINE 580. {0}'.format(linkType))

    def _writeOptionalXsecCards(self, fileObject, xSec, replaceParamFile):
        """
        Write Optional Cross Section Cards to File Method
        """
        if xSec.erode:
            fileObject.write('ERODE\n')

        if xSec.maxErosion != None:
            fileObject.write('MAX_EROSION    %.6f\n' % xSec.maxErosion)

        if xSec.subsurface:
            fileObject.write('SUBSURFACE\n')

        if xSec.mRiver != None:
            mRiver = vwp(xSec.mRiver, replaceParamFile)
            try:
                fileObject.write('M_RIVER        %.6f\n' % mRiver)
            except:
                fileObject.write('M_RIVER        %s\n' % mRiver)

        if xSec.kRiver != None:
            kRiver = vwp(xSec.kRiver, replaceParamFile)
            try:
                fileObject.write('K_RIVER        %.6f\n' % kRiver)
            except:
                fileObject.write('K_RIVER        %s\n' % kRiver)

    def _getUpdateGeometrySqlString(self, geometryID, tableName, spatialReferenceID, wktString):
        statement = """
                    UPDATE {0} SET geometry=ST_GeomFromText('{1}', {2})
                    WHERE id={3};
                    """.format(tableName,
                               wktString,
                               spatialReferenceID,
                               geometryID)
        return statement


class StreamLink(DeclarativeBase, GeometricObjectBase):
    """
    Object containing generic stream link or reach data.

    GSSHA stream networks are composed of a series of stream links and nodes. A stream link is composed of two or more
    nodes. A basic fluvial stream link contains the cross section. Stream links can also be used to describe structures
    on a stream such as culverts, weirs, or reservoirs.

    This object inherits several methods from the :class:`gsshapy.orm.GeometricObjectBase` base class for generating
    geometric visualizations.

    See: http://www.gsshawiki.com/Surface_Water_Routing:Channel_Routing#5.1.4.1.4_-_Link_.28Reach.29_information
    """
    __tablename__ = 'cif_links'

    tableName = __tablename__  #: Database tablename

    # Public Table Metadata
    tableName = __tablename__
    geometryColumnName = 'geometry'

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    channelInputFileID = Column(Integer, ForeignKey('cif_channel_input_files.id'))  #: FK

    # Value Columns
    linkNumber = Column(Integer)  #: INTEGER
    type = Column(String)  #: STRING
    numElements = Column(Integer)  #: INTEGER
    dx = Column(Float)  #: FLOAT
    erode = Column(Boolean)  #: BOOLEAN
    subsurface = Column(Boolean)  #: BOOLEAN
    downstreamLinkID = Column(Integer)  #: INTEGER
    numUpstreamLinks = Column(Integer)  #: INTEGER
    geometry = Column(Geometry)  #: GEOMETRY

    # Relationship Properties
    channelInputFile = relationship('ChannelInputFile', back_populates='streamLinks')  #: RELATIONSHIP
    upstreamLinks = relationship('UpstreamLink', back_populates='streamLink')  #: RELATIONSHIP
    nodes = relationship('StreamNode', back_populates='streamLink')  #: RELATIONSHIP
    weirs = relationship('Weir', back_populates='streamLink')  #: RELATIONSHIP
    culverts = relationship('Culvert', back_populates='streamLink')  #: RELATIONSHIP
    reservoir = relationship('Reservoir', uselist=False, back_populates='streamLink')  #: RELATIONSHIP
    breakpointCS = relationship('BreakpointCS', uselist=False, back_populates='streamLink')  #: RELATIONSHIP
    trapezoidalCS = relationship('TrapezoidalCS', uselist=False, back_populates='streamLink')  #: RELATIONSHIP
    datasets = relationship('LinkDataset', back_populates='link')  #: RELATIONSHIP

    def __init__(self, linkNumber, type, numElements, dx=None, erode=False, subsurface=False):
        """
        Constructor
        """
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

    def __eq__(self, other):
        return (self.linkNumber == other.linkNumber and
                self.type == other.type and
                self.numElements == other.numElements and
                self.dx == other.dx and
                self.erode == other.erode and
                self.subsurface == other.subsurface and
                self.downstreamLinkID == other.downstreamLinkID and
                self.numUpstreamLinks == other.numUpstreamLinks)


class UpstreamLink(DeclarativeBase):
    """
    Object used to map stream links with their upstream link counterparts.

    See: http://www.gsshawiki.com/Surface_Water_Routing:Channel_Routing#5.1.4.1.3_.E2.80.93_Channel_network_connectivity
    """
    __tablename__ = 'cif_upstream_links'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    linkID = Column(Integer, ForeignKey('cif_links.id'))  #: INTEGER

    # Value Columns
    upstreamLinkID = Column(Integer)  #: INTEGER

    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='upstreamLinks')  #: RELATIONSHIP

    def __init__(self, upstreamLinkID):
        self.upstreamLinkID = upstreamLinkID

    def __repr__(self):
        return '<UpstreamLink: LinkID=%s, UpstreamLinkID=%s>' % (self.linkID, self.upstreamLinkID)

    def __eq__(self, other):
        return self.upstreamLinkID == other.upstreamLinkID


class StreamNode(DeclarativeBase, GeometricObjectBase):
    """
    Object containing the stream node data in the channel network.

    Stream nodes represent the computational unit of GSSHA stream networks. Each stream link must consist of two or more
    stream nodes.

    This object inherits several methods from the :class:`gsshapy.orm.GeometricObjectBase` base class for generating
    geometric visualizations.

    See: http://www.gsshawiki.com/Surface_Water_Routing:Channel_Routing#5.1.4.1.4.2.1.4_Node_information
    """
    __tablename__ = 'cif_nodes'

    tableName = __tablename__  #: Database tablename

    # Public Table Metadata
    tableName = __tablename__
    geometryColumnName = 'geometry'

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    linkID = Column(Integer, ForeignKey('cif_links.id'))  #: FK

    # Value Columns
    nodeNumber = Column(Integer)  #: INTEGER
    x = Column(Float)  #: FLOAT
    y = Column(Float)  #: FLOAT
    elevation = Column(Float)  #: FLOAT
    geometry = Column(Geometry)  #: GEOMETRY

    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='nodes')  #: RELATIONSHIP
    datasets = relationship('NodeDataset', back_populates='node')  #: RELATIONSHIP


    def __init__(self, nodeNumber, x, y, elevation):
        """
        Constructor
        """
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

    def __eq__(self, other):
        return (self.nodeNumber == other.nodeNumber and
                self.x == other.x and
                self.y == other.y and
                self.elevation == other.elevation)


class Weir(DeclarativeBase):
    """
    Object containing data that defines a weir structure for a stream link.

    See: http://www.gsshawiki.com/Surface_Water_Routing:Channel_Routing#5.1.4.1.4.2_-_Structure_channel_links
    """
    __tablename__ = 'cif_weirs'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    linkID = Column(Integer, ForeignKey('cif_links.id'))  #: FK

    # Value Columns
    type = Column(String)  #: STRING
    crestLength = Column(Float)  #: FLOAT
    crestLowElevation = Column(Float)  #: FLOAT
    dischargeCoeffForward = Column(Float)  #: FLOAT
    dischargeCoeffReverse = Column(Float)  #: FLOAT
    crestLowLocation = Column(Float)  #: FLOAT
    steepSlope = Column(Float)  #: FLOAT
    shallowSlope = Column(Float)  #: FLOAT

    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='weirs')  #: RELATIONSHIP


    def __init__(self, type, crestLength, crestLowElevation, dischargeCoeffForward, dischargeCoeffReverse,
                 crestLowLocation, steepSlope, shallowSlope):
        """
        Constructor
        """
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

    def __eq__(self, other):
        return (self.type == other.type and
                self.crestLength == other.crestLength and
                self.crestLowElevation == other.crestLowElevation and
                self.dischargeCoeffForward == other.dischargeCoeffForward and
                self.dischargeCoeffReverse == other.dischargeCoeffReverse and
                self.crestLowLocation == other.crestLowLocation and
                self.steepSlope == other.steepSlope and
                self.shallowSlope == other.shallowSlope)


class Culvert(DeclarativeBase):
    """
    Object containing a culvert structure data for a stream link.

    See: http://www.gsshawiki.com/Surface_Water_Routing:Channel_Routing#5.1.4.1.4.2_-_Structure_channel_links
    """
    __tablename__ = 'cif_culverts'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    linkID = Column(Integer, ForeignKey('cif_links.id'))  #: FK

    # Value Columns
    type = Column(String)  #: STRING
    upstreamInvert = Column(Float)  #: FLOAT
    downstreamInvert = Column(Float)  #: FLOAT
    inletDischargeCoeff = Column(Float)  #: FLOAT
    reverseFlowDischargeCoeff = Column(Float)  #: FLOAT
    slope = Column(Float)  #: FLOAT
    length = Column(Float)  #: FLOAT
    roughness = Column(Float)  #: FLOAT
    diameter = Column(Float)  #: FLOAT
    width = Column(Float)  #: FLOAT
    height = Column(Float)  #: FLOAT

    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='culverts')  #: RELATIONSHIP

    def __init__(self, type, upstreamInvert, downstreamInvert, inletDischargeCoeff, reverseFlowDischargeCoeff, slope,
                 length, roughness, diameter, width, height):
        """
        Constructor
        """
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

    def __eq__(self, other):
        return (self.type == other.type and
                self.upstreamInvert == other.upstreamInvert and
                self.downstreamInvert == other.downstreamInvert and
                self.inletDischargeCoeff == other.inletDischargeCoeff and
                self.reverseFlowDischargeCoeff == other.reverseFlowDischargeCoeff and
                self.slope == other.slope and
                self.length == other.length and
                self.roughness == other.roughness and
                self.diameter == other.diameter and
                self.width == other.width and
                self.height == other.height)


class Reservoir(DeclarativeBase):
    """
    Object containing a data that defines a reservoir for a stream link.

    See: http://www.gsshawiki.com/Surface_Water_Routing:Channel_Routing#5.1.4.1.4.3_-_Reservoir_channel_links
    """
    __tablename__ = 'cif_reservoirs'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    linkID = Column(Integer, ForeignKey('cif_links.id'))  #: FK

    # Value Columns
    initWSE = Column(Float)  #: FLOAT
    minWSE = Column(Float)  #: FLOAT
    maxWSE = Column(Float)  #: FLOAT

    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='reservoir')  #: RELATIONSHIP
    reservoirPoints = relationship('ReservoirPoint', back_populates='reservoir')  #: RELATIONSHIP

    def __init__(self, initWSE, minWSE, maxWSE):
        """
        Constructor
        """
        self.initWSE = initWSE
        self.minWSE = minWSE
        self.maxWSE = maxWSE

    def __repr__(self):
        return '<Reservoir: InitialWSE=%s, MinWSE=%s, MaxWSE=%s>' % (self.initWSE, self.minWSE, self.maxWSE)

    def __eq__(self, other):
        return (self.initWSE == other.initWSE and
                self.minWSE == other.minWSE and
                self.maxWSE == other.maxWSE)


class ReservoirPoint(DeclarativeBase):
    """
    Object containing the cells/points that define the maximum inundation area of a reservoir.

    See: http://www.gsshawiki.com/Surface_Water_Routing:Channel_Routing#
    """
    __tablename__ = 'cif_reservoir_points'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    reservoirID = Column(Integer, ForeignKey('cif_reservoirs.id'))  #: FK

    # Value Columns
    i = Column(Integer)  #: INTEGER
    j = Column(Integer)  #: INTEGER

    # Relationship Properties
    reservoir = relationship('Reservoir', back_populates='reservoirPoints')  #: RELATIONSHIP

    def __init__(self, i, j):
        """
        Constructor
        """
        self.i = i
        self.j = j

    def __repr__(self):
        return '<ReservoirPoint: CellI=%s, CellJ=%s>' % (self.i, self.j)

    def __eq__(self, other):
        return (self.i == other.i and
                self.j == other.j)


class BreakpointCS(DeclarativeBase):
    """
    Object containing breakpoint type cross section data for fluvial stream links.

    See: http://www.gsshawiki.com/Surface_Water_Routing:Channel_Routing#5.1.4.1.4.2.1.2_Natural_cross-section
    """
    __tablename__ = 'cif_breakpoint'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    linkID = Column(Integer, ForeignKey('cif_links.id'))  #: FK

    # Value Columns
    mannings_n = Column(Float)  #: FLOAT
    numPairs = Column(Integer)  #: INTEGER
    numInterp = Column(Integer)  #:INTEGER
    mRiver = Column(Float)  #: FLOAT
    kRiver = Column(Float)  #: FLOAT
    erode = Column(Boolean)  #: BOOLEAN
    subsurface = Column(Boolean)  #: BOOLEAN
    maxErosion = Column(Float)  #: FLOAT

    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='breakpointCS')  #: RELATIONSHIP
    breakpoints = relationship('Breakpoint', back_populates='crossSection')  #: RELATIONSHIP

    def __init__(self, mannings_n, numPairs, numInterp, mRiver, kRiver, erode, subsurface, maxErosion):
        """
        Constructor
        """
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

    def __eq__(self, other):
        return (self.mannings_n == other.mannings_n and
                self.numPairs == other.numPairs and
                self.numInterp == other.numInterp and
                self.mRiver == other.mRiver and
                self.kRiver == other.kRiver and
                self.erode == other.erode and
                self.subsurface == other.subsurface and
                self.maxErosion == other.maxErosion)


class Breakpoint(DeclarativeBase):
    """
    Object used to define points in a :class:`.BreakpointCS` object.

    See: http://www.gsshawiki.com/Surface_Water_Routing:Channel_Routing#5.1.4.1.4.2.1.2_Natural_cross-section
    """
    __tablename__ = 'cif_bcs_points'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    crossSectionID = Column(Integer, ForeignKey('cif_breakpoint.id'))  #: FK

    # Value Columns
    x = Column(Float)  #: FLOAT
    y = Column(Float)  #: FLOAT

    # Relationship Properties
    crossSection = relationship('BreakpointCS', back_populates='breakpoints')  #: RELATIONSHIP

    def __init__(self, x, y):
        """
        Constructor
        """
        self.x = x
        self.y = y

    def __repr__(self):
        return '<Breakpoint: X=%s, Y=%s>' % (self.x, self.y)

    def __eq__(self, other):
        return (self.x == other.x,
                self.y == other.y)


class TrapezoidalCS(DeclarativeBase):
    """
    Object containing trapezoidal type cross section data for fluvial stream links.

    See: http://www.gsshawiki.com/Surface_Water_Routing:Channel_Routing#5.1.4.1.4.2.1.1_Trapezoidal_cross-section
    """
    __tablename__ = 'cif_trapezoid'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    linkID = Column(Integer, ForeignKey('cif_links.id'))  #: FK

    # Value Columns
    mannings_n = Column(Float)  #: FLOAT
    bottomWidth = Column(Float)  #: FLOAT
    bankfullDepth = Column(Float)  #: FLOAT
    sideSlope = Column(Float)  #: FLOAT
    mRiver = Column(Float)  #: FLOAT
    kRiver = Column(Float)  #: FLOAT
    erode = Column(Boolean)  #: BOOLEAN
    subsurface = Column(Boolean)  #: BOOLEAN
    maxErosion = Column(Float)  #: BOOLEAN

    # Relationship Properties
    streamLink = relationship('StreamLink', back_populates='trapezoidalCS')  #: RELATIONSHIP

    def __init__(self, mannings_n, bottomWidth, bankfullDepth, sideSlope, mRiver, kRiver, erode, subsurface,
                 maxErosion):
        """
        Constructor
        """
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

    def __eq__(self, other):
        return (self.mannings_n == other.mannings_n and
                self.bottomWidth == other.bottomWidth and
                self.bankfullDepth == other.bankfullDepth and
                self.sideSlope == other.sideSlope and
                self.mRiver == other.mRiver and
                self.kRiver == other.kRiver and
                self.erode == other.erode and
                self.subsurface == other.subsurface and
                self.maxErosion == other.maxErosion)
