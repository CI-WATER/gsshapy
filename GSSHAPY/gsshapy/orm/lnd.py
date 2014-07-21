"""
********************************************************************************
* Name: Link Node Dataset Model
* Author: Nathan Swain
* Created On: August 1, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

__all__ = ['LinkNodeDatasetFile',
           'LinkNodeTimeStep',
           'LinkDataset',
           'NodeDataset']

import xml.etree.ElementTree as ET
from datetime import timedelta, datetime

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, Float
from sqlalchemy.orm import relationship

from mapkit.GeometryConverter import GeometryConverter

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

from gsshapy.lib import parsetools as pt


class LinkNodeDatasetFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    """
    __tablename__ = 'lnd_link_node_dataset_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))  #: FK
    channelInputFileID = Column(Integer, ForeignKey('cif_channel_input_files.id'))  #: FK

    # Value Columns
    fileExtension = Column(String, default='lnd')  #: STRING
    name = Column(String, nullable=False)  #: STRING
    numLinks = Column(Integer, nullable=False)  #: INTEGER
    timeStepInterval = Column(Integer, nullable=False)  #: INTEGER
    numTimeSteps = Column(Integer, nullable=False)  #: INTEGER
    startTime = Column(String, nullable=False)  #: STRING

    # Relationship Properties
    projectFile = relationship('ProjectFile', back_populates='linkNodeDatasets')  #: RELATIONSHIP
    timeSteps = relationship('LinkNodeTimeStep', back_populates='linkNodeDataset')  #: RELATIONSHIP
    channelInputFile = relationship('ChannelInputFile', back_populates='linkNodeDatasets')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def linkToChannelInputFile(self, session, channelInputFile, force=False):
        """
        Create database relationships between the dataset and the channel input file. This is
        done so that the geometry associated with links and nodes can be associated with the
        link and node datasets.
        :param session: SQLAlchemy session bound to a PostGIS enabled database
        :param channelInputFile: The GSSHAPY ChannelInputFile object to associate with this LinkNodeDatasetFile
        :param force: For ChannelInputFile reassignment. Default behaviour is to skip assignment if already done.
        """
        # Only perform operation if the channel input file has not been assigned or the force parameter is true
        if self.channelInputFile is not None and not force:
            return

        # Set the channel input file relationship
        self.channelInputFile = channelInputFile

        # Retrieve the fluvial stream links
        fluvialLinks = channelInputFile.getFluvialLinks()

        # Retrieve the LinkNodeTimeStep objects
        timeSteps = self.timeSteps

        # Link each link dataset in each time step
        for timeStep in timeSteps:
            # Retrieve link datasets
            linkDatasets = timeStep.linkDatasets

            # Link each node dataset
            for l, linkDataset in enumerate(linkDatasets):
                # Get the fluvial link
                fluvialLink = fluvialLinks[l]
                fluvialNodes = fluvialLink.nodes

                # Link link datasets to fluvial links
                linkDataset.link = fluvialLink

                # Retrieve node datasets
                nodeDatasets = linkDataset.nodeDatasets

                for n, nodeDataset in enumerate(nodeDatasets):
                    nodeDataset.node = fluvialNodes[n]

        session.add(self)
        session.commit()

    ## TODO: Implement these methods

    def getAsKmlAnimation(self, session, channelInputFile, path=None, documentName=None, zScale=1.0):
        """
        Generate a KML visualization of the the dataset file.
        """
        # Validate
        if not documentName:
            documentName = self.fileExtension

        # Link to channel input file
        self.linkToChannelInputFile(session, channelInputFile)

        # Create instance of GeometryConverter
        converter = GeometryConverter(session)

        # Get LinkNodeTimeSteps
        linkNodeTimeSteps = self.timeSteps

        # Get date time parameters
        timeStepDelta = timedelta(minutes=self.timeStepInterval)
        startDateTime = datetime(1970, 1, 1)
        startTimeParts = self.startTime.split()

        if len(startTimeParts) > 5:
            # Default start date time to epoch
            startDateTime = datetime(year=int(startTimeParts[0]) or 1970,
                                     month=int(startTimeParts[1]) or 1,
                                     day=int(startTimeParts[2]) or 1,
                                     hour=int(startTimeParts[3]) or 0,
                                     minute=int(startTimeParts[4]) or 0)

        # Start the Kml Document
        kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
        document = ET.SubElement(kml, 'Document')
        docName = ET.SubElement(document, 'name')
        docName.text = documentName

        # Apply special style to hide legend items
        style = ET.SubElement(document, 'Style', id='check-hide-children')
        listStyle = ET.SubElement(style, 'ListStyle')
        listItemType = ET.SubElement(listStyle, 'listItemType')
        listItemType.text = 'checkHideChildren'
        styleUrl = ET.SubElement(document, 'styleUrl')
        styleUrl.text = '#check-hide-children'

        for linkNodeTimeStep in linkNodeTimeSteps:
            print linkNodeTimeStep.timeStep

            # Create current datetime objects
            timeSpanBegin = startDateTime + (linkNodeTimeStep.timeStep * timeStepDelta)
            timeSpanEnd = timeSpanBegin + timeStepDelta

            # Get Link Datasets
            linkDatasets = linkNodeTimeStep.linkDatasets

            for linkDataset in linkDatasets:
                # Get Node Datasets
                nodeDatasets = linkDataset.nodeDatasets

                for nodeDataset in nodeDatasets:
                    # Get node
                    node = nodeDataset.node

                    circleString = converter.getPointAsKmlCircle(tableName=node.tableName,
                                                                 radius=0.0001,
                                                                 extrude=nodeDataset.value,
                                                                 zScaleFactor=zScale,
                                                                 geometryId=node.id)

                    # Create placemark
                    placemark = ET.SubElement(document, 'Placemark')

                    # Create TimeSpan tag
                    timeSpan = ET.SubElement(placemark, 'TimeSpan')

                    # Create begin and end tags
                    begin = ET.SubElement(timeSpan, 'begin')
                    begin.text = timeSpanBegin.strftime('%Y-%m-%dT%H:%M:%S')
                    end = ET.SubElement(timeSpan, 'end')
                    end.text = timeSpanEnd.strftime('%Y-%m-%dT%H:%M:%S')

                    # Append geometry
                    polygonCircle = ET.fromstring(circleString)
                    placemark.append(polygonCircle)


        kmlString = ET.tostring(kml)

        if path:
            with open(path, 'w') as f:
                f.write(kmlString)

        return kmlString



    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, raster2pgsqlPath):
        """
        Link Node Dataset File Read from File Method
        """
        # Set file extension property
        self.fileExtension = extension

        # Dictionary of keywords/cards and parse function names
        KEYWORDS = ('NUM_LINKS',
                    'TIME_STEP',
                    'NUM_TS',
                    'START_TIME',
                    'TS')

        # Parse file into chunks associated with keywords/cards
        with open(path, 'r') as f:
            self.name = f.readline().strip()
            chunks = pt.chunk(KEYWORDS, f)

        # Parse chunks associated with each key    
        for card, chunkList in chunks.iteritems():
            # Parse each chunk in the chunk list
            for chunk in chunkList:
                schunk = chunk[0].strip().split()

                # Cases
                if card == 'NUM_LINKS':
                    # NUM_LINKS handler
                    self.numLinks = schunk[1]

                elif card == 'TIME_STEP':
                    # TIME_STEP handler
                    self.timeStepInterval = schunk[1]

                elif card == 'NUM_TS':
                    # NUM_TS handler
                    self.numTimeSteps = schunk[1]

                elif card == 'START_TIME':
                    # START_TIME handler
                    self.startTime = '%s  %s    %s  %s  %s  %s' % (
                        schunk[1],
                        schunk[2],
                        schunk[3],
                        schunk[4],
                        schunk[5],
                        schunk[6])

                elif card == 'TS':
                    # TS handler
                    for line in chunk:
                        sline = line.strip().split()
                        token = sline[0]

                        # Cases
                        if token == 'TS':
                            # Time Step line handler
                            timeStep = LinkNodeTimeStep(timeStep=sline[1])
                            timeStep.linkNodeDataset = self

                        else:
                            # LinkNodeLine handler
                            linkDataset = self._createLinkDataset(line.strip())
                            linkDataset.timeStep = timeStep

    def _write(self, session, openFile):
        """
        Link Node Dataset File Write to File Method
        """
        # Retrieve TimeStep objects
        timeSteps = self.timeSteps

        # Write Lines
        openFile.write('%s\n' % self.name)
        openFile.write('NUM_LINKS     %s\n' % self.numLinks)
        openFile.write('TIME_STEP     %s\n' % self.timeStepInterval)
        openFile.write('NUM_TS        %s\n' % self.numTimeSteps)
        openFile.write('START_TIME    %s\n' % self.startTime)

        for timeStep in timeSteps:
            openFile.write('TS    %s\n' % timeStep.timeStep)

            # Retrieve LinkDataset objects
            linkDatasets = timeStep.linkDatasets

            for linkDataset in linkDatasets:
                # Write number of node datasets values
                openFile.write('{0}   '.format(linkDataset.numNodeDatasets))

                # Retrieve NodeDatasets
                nodeDatasets = linkDataset.nodeDatasets

                for nodeDataset in nodeDatasets:
                    # Write status and value
                    openFile.write('{0}  {1:.5f}   '.format(nodeDataset.status, nodeDataset.value))

                # Write new line character after each link dataset
                openFile.write('\n')

            # Insert empty line between time steps 
            openFile.write('\n')

    def _createLinkDataset(self, linkLine):
        """
        Create LinkDataset object
        """
        # Split the line
        spLinkLine = linkLine.split()

        # Create LinkDataset GSSHAPY object
        linkDataset = LinkDataset()
        linkDataset.numNodeDatasets = int(spLinkLine[0])

        # Parse line into NodeDatasets
        NODE_VALUE_INCREMENT = 2
        statusIndex = 1
        valueIndex = statusIndex + 1

        # Parse line into node datasets
        for i in range(0, linkDataset.numNodeDatasets):
            # Create NodeDataset GSSHAPY object
            nodeDataset = NodeDataset()
            nodeDataset.status = int(spLinkLine[statusIndex])
            nodeDataset.value = float(spLinkLine[valueIndex])
            nodeDataset.linkDataset = linkDataset

            # Increment to next status/value pair
            statusIndex += NODE_VALUE_INCREMENT
            valueIndex += NODE_VALUE_INCREMENT

        return linkDataset


class LinkNodeTimeStep(DeclarativeBase):
    """
    """
    __tablename__ = 'lnd_time_steps'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    linkNodeDatasetFileID = Column(Integer, ForeignKey('lnd_link_node_dataset_files.id'))  #: FK

    # Value Columns
    timeStep = Column(Integer, nullable=False)  #: INTEGER

    # Relationship Properties
    linkNodeDataset = relationship('LinkNodeDatasetFile', back_populates='timeSteps')  #: RELATIONSHIP
    linkDatasets = relationship('LinkDataset', back_populates='timeStep')  #: RELATIONSHIP

    def __init__(self, timeStep):
        self.timeStep = timeStep

    def __repr__(self):
        return '<TimeStep: %s>' % self.timeStep


class LinkDataset(DeclarativeBase):
    """
    """
    __tablename__ = 'lnd_link_datasets'
    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    timeStepID = Column(Integer, ForeignKey('lnd_time_steps.id'))  #: FK
    streamLinkID = Column(Integer, ForeignKey('cif_links.id'))  #: FK

    # Value Columns
    numNodeDatasets = Column(Integer)  #: INTEGER

    # Relationship Properties
    timeStep = relationship('LinkNodeTimeStep', back_populates='linkDatasets')  #: RELATIONSHIP
    nodeDatasets = relationship('NodeDataset', back_populates='linkDataset')  #: RELATIONSHIP
    link = relationship('StreamLink', back_populates='datasets')  #: RELATIONSHIP

    def __repr__(self):
        return '<LinkDataset: NumberNodeDatasets=%s>' % self.numNodeDatasets


class NodeDataset(DeclarativeBase):
    """
    """
    __tablename__ = 'lnd_node_datasets'
    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    linkDatasetID = Column(Integer, ForeignKey('lnd_link_datasets.id'))  #: FK
    streamNodeID = Column(Integer, ForeignKey('cif_nodes.id'))  #: FK

    # Value Columns
    status = Column(Integer)  #: INTEGER
    value = Column(Float)  #: FLOAT

    # Relationship Properties
    linkDataset = relationship('LinkDataset', back_populates='nodeDatasets')  #: RELATIONSHIP
    node = relationship('StreamNode', back_populates='datasets')  #: RELATIONSHIP

    def __repr__(self):
        return '<NodeDataset: Status=%s, Value=%s>' % (self.status, self.value)
