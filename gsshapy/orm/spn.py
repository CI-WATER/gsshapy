"""
********************************************************************************
* Name: StormPipeNetworkModel
* Author: Nathan Swain
* Created On: May 14, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from __future__ import unicode_literals

__all__ = ['StormPipeNetworkFile',
           'SuperLink',
           'SuperNode',
           'Pipe',
           'SuperJunction',
           'Connection']

from future.utils import iteritems
from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float, String
from sqlalchemy.orm import relationship

from . import DeclarativeBase
from ..base.file_base import GsshaPyFileObjectBase
from ..lib import parsetools as pt, spn_chunk as spc


class StormPipeNetworkFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for the Storm Pipe Network File.

    This file is similar in structure as the channel input file. The contents of this file is abstracted to several
    supporting objects: :class:`.SuperLink`, :class:`.SuperNode`, :class:`.Pipe`, :class:`.SuperJunction`, and
    :class:`.Connection`.

    See: http://www.gsshawiki.com/Subsurface_Drainage:Subsurface_Drainage
         http://www.gsshawiki.com/images/d/d6/SUPERLINK_TN.pdf
    """
    __tablename__ = 'spn_storm_pipe_network_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK

    # Value Columns
    fileExtension = Column(String, default='spn')  #: STRING

    # Relationship Properties
    connections = relationship('Connection', back_populates='stormPipeNetworkFile')  #: RELATIONSHIP
    superLinks = relationship('SuperLink', back_populates='stormPipeNetworkFile')  #: RELATIONSHIP
    superJunctions = relationship('SuperJunction', back_populates='stormPipeNetworkFile')  #: RELATIONSHIP
    projectFile = relationship('ProjectFile', uselist=False, back_populates='stormPipeNetworkFile')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def __repr__(self):
        return '<PipeNetwork: ID=%s>' % self.id

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
        """
        Storm Pipe Network File Read from File Method
        """
        # Set file extension property
        self.fileExtension = extension

        # Dictionary of keywords/cards and parse function names
        KEYWORDS = {'CONNECT': spc.connectChunk,
                    'SJUNC': spc.sjuncChunk,
                    'SLINK': spc.slinkChunk}

        sjuncs = []
        slinks = []
        connections = []

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
                if key == 'CONNECT':
                    connections.append(result)
                elif key == 'SJUNC':
                    sjuncs.append(result)
                elif key == 'SLINK':
                    slinks.append(result)

        # Create GSSHAPY objects
        self._createConnection(connections)
        self._createSjunc(sjuncs)
        self._createSlink(slinks)

    def _write(self, session, openFile, replaceParamFile):
        """
        Storm Pipe Network File Write to File Method
        """
        # Retrieve Connection objects and write to file
        connections = self.connections
        self._writeConnections(connections=connections,
                               fileObject=openFile)

        # Retrieve SuperJunction objects and write to file
        sjuncs = self.superJunctions
        self._writeSuperJunctions(superJunctions=sjuncs,
                                  fileObject=openFile)

        # Retrieve SuperLink objects and write to file
        slinks = self.superLinks
        self._writeSuperLinks(superLinks=slinks,
                              fileObject=openFile)

    def _createConnection(self, connections):
        """
        Create GSSHAPY Connection Objects Method
        """

        for c in connections:
            # Create GSSHAPY Connection object
            connection = Connection(slinkNumber=c['slinkNumber'],
                                    upSjuncNumber=c['upSjunc'],
                                    downSjuncNumber=c['downSjunc'])

            # Associate Connection with StormPipeNetworkFile
            connection.stormPipeNetworkFile = self

    def _createSlink(self, slinks):
        """
        Create GSSHAPY SuperLink, Pipe, and SuperNode Objects Method
        """

        for slink in slinks:
            # Create GSSHAPY SuperLink object
            superLink = SuperLink(slinkNumber=slink['slinkNumber'],
                                  numPipes=slink['numPipes'])

            # Associate SuperLink with StormPipeNetworkFile
            superLink.stormPipeNetworkFile = self

            for node in slink['nodes']:
                # Create GSSHAPY SuperNode objects
                superNode = SuperNode(nodeNumber=node['nodeNumber'],
                                      groundSurfaceElev=node['groundSurfaceElev'],
                                      invertElev=node['invertElev'],
                                      manholeSA=node['manholeSA'],
                                      nodeInletCode=node['inletCode'],
                                      cellI=node['cellI'],
                                      cellJ=node['cellJ'],
                                      weirSideLength=node['weirSideLength'],
                                      orificeDiameter=node['orificeDiameter'])

                # Associate SuperNode with SuperLink
                superNode.superLink = superLink

            for p in slink['pipes']:
                # Create GSSHAPY Pipe objects
                pipe = Pipe(pipeNumber=p['pipeNumber'],
                            xSecType=p['xSecType'],
                            diameterOrHeight=p['diameterOrHeight'],
                            width=p['width'],
                            slope=p['slope'],
                            roughness=p['roughness'],
                            length=p['length'],
                            conductance=p['conductance'],
                            drainSpacing=p['drainSpacing'])

                # Associate Pipe with SuperLink
                pipe.superLink = superLink

    def _createSjunc(self, sjuncs):
        """
        Create GSSHAPY SuperJunction Objects Method
        """

        for sjunc in sjuncs:
            # Create GSSHAPY SuperJunction object
            superJunction = SuperJunction(sjuncNumber=sjunc['sjuncNumber'],
                                          groundSurfaceElev=sjunc['groundSurfaceElev'],
                                          invertElev=sjunc['invertElev'],
                                          manholeSA=sjunc['manholeSA'],
                                          inletCode=sjunc['inletCode'],
                                          linkOrCellI=sjunc['linkOrCellI'],
                                          nodeOrCellJ=sjunc['nodeOrCellJ'],
                                          weirSideLength=sjunc['weirSideLength'],
                                          orificeDiameter=sjunc['orificeDiameter'])

            # Associate SuperJunction with StormPipeNetworkFile
            superJunction.stormPipeNetworkFile = self

    def _writeConnections(self, connections, fileObject):
        """
        Write Connections to File Method
        """
        for connection in connections:
            fileObject.write('CONNECT  %s  %s  %s\n' % (
                connection.slinkNumber,
                connection.upSjuncNumber,
                connection.downSjuncNumber))

    def _writeSuperJunctions(self, superJunctions, fileObject):
        """
        Write SuperJunctions to File Method
        """
        for sjunc in superJunctions:
            fileObject.write('SJUNC  %s  %.2f  %.2f  %.6f  %s  %s  %s  %.6f  %.6f\n' % (
                sjunc.sjuncNumber,
                sjunc.groundSurfaceElev,
                sjunc.invertElev,
                sjunc.manholeSA,
                sjunc.inletCode,
                sjunc.linkOrCellI,
                sjunc.nodeOrCellJ,
                sjunc.weirSideLength,
                sjunc.orificeDiameter))

    def _writeSuperLinks(self, superLinks, fileObject):
        """
        Write SuperLinks to File Method
        """
        for slink in superLinks:
            fileObject.write('SLINK   %s      %s\n' % (
                slink.slinkNumber,
                slink.numPipes))

            for node in slink.superNodes:
                fileObject.write('NODE  %s  %.2f  %.2f  %.6f  %s  %s  %s  %.6f  %.6f\n' % (
                    node.nodeNumber,
                    node.groundSurfaceElev,
                    node.invertElev,
                    node.manholeSA,
                    node.nodeInletCode,
                    node.cellI,
                    node.cellJ,
                    node.weirSideLength,
                    node.orificeDiameter))
            for pipe in slink.pipes:
                fileObject.write('PIPE  %s  %s  %.6f  %.6f  %.6f  %.6f  %.2f  %.6f  %.6f\n' % (
                    pipe.pipeNumber,
                    pipe.xSecType,
                    pipe.diameterOrHeight,
                    pipe.width,
                    pipe.slope,
                    pipe.roughness,
                    pipe.length,
                    pipe.conductance,
                    pipe.drainSpacing))


class SuperLink(DeclarativeBase):
    """
    Object containing data for a single super link in the subsurface drainage network. A super link consists of several
    pipes and super nodes.
    """
    __tablename__ = 'spn_super_links'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    stormPipeNetworkFileID = Column(Integer, ForeignKey('spn_storm_pipe_network_files.id'))  #: FK

    # Value Columns
    slinkNumber = Column(Integer)  #: INTEGER
    numPipes = Column(Integer)  #: INTEGER

    # Relationship Properties
    stormPipeNetworkFile = relationship('StormPipeNetworkFile', back_populates='superLinks')  #: RELATIONSHIP
    superNodes = relationship('SuperNode', back_populates='superLink')  #: RELATIONSHIP
    pipes = relationship('Pipe', back_populates='superLink')  #: RELATIONSHIP

    def __init__(self, slinkNumber, numPipes):
        """
        Constructor
        """
        self.slinkNumber = slinkNumber
        self.numPipes = numPipes

    def __repr__(self):
        return '<SuperLink: SlinkNumber=%s, NumPipes=%s>' % (
            self.slinkNumber,
            self.numPipes)


class SuperNode(DeclarativeBase):
    """
    Object containing data for a single super node in the subsurface drainage network. Super nodes belong to one super
    link.
    """
    __tablename__ = 'spn_super_nodes'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    superLinkID = Column(Integer, ForeignKey('spn_super_links.id'))  #: FK

    # Value Columns
    nodeNumber = Column(Integer)  #: INTEGER
    groundSurfaceElev = Column(Float)  #: FLOAT
    invertElev = Column(Float)  #: FLOAT
    manholeSA = Column(Float)  #: FLOAT
    nodeInletCode = Column(Integer)  #: INTEGER
    cellI = Column(Integer)  #: INTEGER
    cellJ = Column(Integer)  #: INTEGER
    weirSideLength = Column(Float)  #: FLOAT
    orificeDiameter = Column(Float)  #: FLOAT

    # Relationship Properties
    superLink = relationship('SuperLink', back_populates='superNodes')  #: RELATIONSHIP

    def __init__(self, nodeNumber, groundSurfaceElev, invertElev, manholeSA, nodeInletCode, cellI, cellJ,
                 weirSideLength, orificeDiameter):
        """
        Constructor
        """
        self.nodeNumber = nodeNumber
        self.groundSurfaceElev = groundSurfaceElev
        self.invertElev = invertElev
        self.manholeSA = manholeSA
        self.nodeInletCode = nodeInletCode
        self.cellI = cellI
        self.cellJ = cellJ
        self.weirSideLength = weirSideLength
        self.orificeDiameter = orificeDiameter

    def __repr__(self):
        return '<SuperNode: NodeNumber=%s, GroundSurfaceElev=%s, InvertElev=%s, ManholeSA=%s, NodeInletCode=%s, CellI=%s, CellJ=%s, WeirSideLength=%s, OrificeDiameter=%s>' % (
            self.nodeNumber,
            self.groundSurfaceElev,
            self.invertElev,
            self.manholeSA,
            self.nodeInletCode,
            self.cellI,
            self.cellJ,
            self.weirSideLength,
            self.orificeDiameter)


class Pipe(DeclarativeBase):
    """
    Object containing data for a single pipe in the subsurface drainage network. Pipes belong to one super link.
    """
    __tablename__ = 'spn_pipes'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    superLinkID = Column(Integer, ForeignKey('spn_super_links.id'))  #: FK

    # Value Columns
    pipeNumber = Column(Integer)  #: INTEGER
    xSecType = Column(Integer)  #: INTEGER
    diameterOrHeight = Column(Float)  #: FLOAT
    width = Column(Float)  #: FLOAT
    slope = Column(Float)  #: FLOAT
    roughness = Column(Float)  #: FLOAT
    length = Column(Float)  #: FLOAT
    conductance = Column(Float)  #: FLOAT
    drainSpacing = Column(Float)  #: FLOAT

    # Relationship Properties
    superLink = relationship('SuperLink', back_populates='pipes')  #: RELATIONSHIP

    def __init__(self, pipeNumber, xSecType, diameterOrHeight, width, slope, roughness, length, conductance,
                 drainSpacing):
        """
        Constructor
        """
        self.pipeNumber = pipeNumber
        self.xSecType = xSecType
        self.diameterOrHeight = diameterOrHeight
        self.width = width
        self.slope = slope
        self.roughness = roughness
        self.length = length
        self.conductance = conductance
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
    """
    Object containing data for a single super junction in the subsurface drainage network. Super junctions are where two
    or more super links join or the unconnected end of a super link.
    """
    __tablename__ = 'spn_super_junctions'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    stormPipeNetworkFileID = Column(Integer, ForeignKey('spn_storm_pipe_network_files.id'))  #: FK

    # Value Columns
    sjuncNumber = Column(Integer)  #: INTEGER
    groundSurfaceElev = Column(Float)  #: FLOAT
    invertElev = Column(Float)  #: FLOAT
    manholeSA = Column(Float)  #: FLOAT
    inletCode = Column(Integer)  #: INTEGER
    linkOrCellI = Column(Integer)  #: INTEGER
    nodeOrCellJ = Column(Integer)  #: INTEGER
    weirSideLength = Column(Float)  #: FLOAT
    orificeDiameter = Column(Float)  #: FLOAT

    # Relationship Properties
    stormPipeNetworkFile = relationship('StormPipeNetworkFile', back_populates='superJunctions')  #: RELATIONSHIP

    def __init__(self, sjuncNumber, groundSurfaceElev, invertElev, manholeSA, inletCode, linkOrCellI, nodeOrCellJ,
                 weirSideLength, orificeDiameter):
        """
        Constructor
        """
        self.sjuncNumber = sjuncNumber
        self.groundSurfaceElev = groundSurfaceElev
        self.invertElev = invertElev
        self.manholeSA = manholeSA
        self.inletCode = inletCode
        self.linkOrCellI = linkOrCellI
        self.nodeOrCellJ = nodeOrCellJ
        self.weirSideLength = weirSideLength
        self.orificeDiameter = orificeDiameter

    def __repr__(self):
        return '<SuperJunction: SjuncNumber=%s, GroundSurfaceElev=%s, InvertElev=%s, ManholeSA=%s, InletCode=%s, LinkOrCellI=%s, NodeOrCellJ=%s, WeirSideLength=%s, OrificeDiameter=%s>' % (
            self.sjuncNumber,
            self.groundSurfaceElev,
            self.invertElev,
            self.manholeSA,
            self.inletCode,
            self.linkOrCellI,
            self.nodeOrCellJ,
            self.weirSideLength,
            self.orificeDiameter)


class Connection(DeclarativeBase):
    """
    Object containing data for a single connection in the subsurface drainage network. Connections between super links
    and super junctions are mapped via these records.
    """
    __tablename__ = 'spn_connections'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    stormPipeNetworkFileID = Column(Integer, ForeignKey('spn_storm_pipe_network_files.id'))  #: FK

    # Value Columns
    slinkNumber = Column(Integer)  #: INTEGER
    upSjuncNumber = Column(Integer)  #: INTEGER
    downSjuncNumber = Column(Integer)  #: INTEGER

    # Relationship Properties
    stormPipeNetworkFile = relationship('StormPipeNetworkFile', back_populates='connections')  #: RELATIONSHIP

    def __init__(self, slinkNumber, upSjuncNumber, downSjuncNumber):
        """
        Constructor
        """
        self.slinkNumber = slinkNumber
        self.upSjuncNumber = upSjuncNumber
        self.downSjuncNumber = downSjuncNumber

    def __repr__(self):
        return '<Connection: SlinkNumber=%s, UpSjuncNumber=%s, DownSjuncNumber=%s>' % (
            self.slinkNumber,
            self.upSjuncNumber,
            self.downSjuncNumber)
