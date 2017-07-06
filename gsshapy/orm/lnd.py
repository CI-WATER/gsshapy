"""
********************************************************************************
* Name: Link Node Dataset Model
* Author: Nathan Swain
* Created On: August 1, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from __future__ import unicode_literals

__all__ = ['LinkNodeDatasetFile',
           'LinkNodeTimeStep',
           'LinkDataset',
           'NodeDataset']

import xml.etree.ElementTree as ET
from datetime import timedelta, datetime
from future.utils import iteritems
import logging

from sqlalchemy import Column, ForeignKey, func
from sqlalchemy.types import Integer, String, Float
from sqlalchemy.orm import relationship

from mapkit.GeometryConverter import GeometryConverter
from mapkit.ColorRampGenerator import ColorRampEnum, ColorRampGenerator

from . import DeclarativeBase
from ..base.file_base import GsshaPyFileObjectBase
from ..lib import parsetools as pt

log = logging.getLogger(__name__)


class LinkNodeDatasetFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for Link Node Dataset files.

    As the name implies, link node datasets store output data for link node networks. In the case of GSSHA, this type of
    file is used to write output for the stream network nodes. The contents of this file is abstracted to several
    supporting objects including: :class:`.LinkNodeTimeStep`, :class:`.LinkDataset`, and :class:`.NodeDataset`.

    Note: The link node dataset must be linked with the channel input file to generate spatial visualizations.
    """
    __tablename__ = 'lnd_link_node_dataset_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))  #: FK
    channelInputFileID = Column(Integer, ForeignKey('cif_channel_input_files.id'))  #: FK

    # Value Columns
    fileExtension = Column(String, default='lnd')  #: STRING
    name = Column(String)  #: STRING
    numLinks = Column(Integer)  #: INTEGER
    timeStepInterval = Column(Integer)  #: INTEGER
    numTimeSteps = Column(Integer)  #: INTEGER
    startTime = Column(String)  #: STRING

    # Relationship Properties
    projectFile = relationship('ProjectFile', back_populates='linkNodeDatasets')  #: RELATIONSHIP
    timeSteps = relationship('LinkNodeTimeStep', back_populates='linkNodeDataset')  #: RELATIONSHIP
    channelInputFile = relationship('ChannelInputFile', back_populates='linkNodeDatasets')  #: RELATIONSHIP
    linkDatasets = relationship('LinkDataset', back_populates='linkNodeDatasetFile')  #: RELATIONSHIP
    nodeDatasets = relationship('NodeDataset', back_populates='linkNodeDatasetFile')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def linkToChannelInputFile(self, session, channelInputFile, force=False):
        """
        Create database relationships between the link node dataset and the channel input file.

        The link node dataset only stores references to the links and nodes--not the geometry. The link and node
        geometries are stored in the channel input file. The two files must be linked with database relationships to
        allow the creation of link node dataset visualizations.

        This process is not performed automatically during reading, because it can be very costly in terms of read time.
        This operation can only be performed after both files have been read into the database.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            channelInputFile (:class:`gsshapy.orm.ChannelInputFile`): Channel input file object to be associated with
                this link node dataset file.
            force (bool, optional): Force channel input file reassignment. When false (default), channel input file
                assignment is skipped if it has already been performed.
        """

        # Only perform operation if the channel input file has not been assigned or the force parameter is true
        if self.channelInputFile is not None and not force:
            return

        # Set the channel input file relationship
        self.channelInputFile = channelInputFile

        # Retrieve the fluvial stream links
        orderedLinks = channelInputFile.getOrderedLinks(session)

        # Retrieve the LinkNodeTimeStep objects
        timeSteps = self.timeSteps

        # Link each link dataset in each time step
        for timeStep in timeSteps:
            # Retrieve link datasets
            linkDatasets = timeStep.linkDatasets

            # Link each node dataset
            for l, linkDataset in enumerate(linkDatasets):
                # Get the fluvial link and nodes
                streamLink = orderedLinks[l]
                streamNodes = streamLink.nodes

                # Link link datasets to fluvial links
                linkDataset.link = streamLink

                # Retrieve node datasets
                nodeDatasets = linkDataset.nodeDatasets

                # Link the node dataset with the channel input file nodes
                if len(nodeDatasets) > 0 and len(streamNodes) > 0:
                    for n, nodeDataset in enumerate(nodeDatasets):
                        nodeDataset.node = streamNodes[n]

        session.add(self)
        session.commit()

    def getAsKmlAnimation(self, session, channelInputFile, path=None, documentName=None, styles={}):
        """
        Generate a KML visualization of the the link node dataset file.

        Link node dataset files are time stamped link node value datasets. This will yield a value for each stream node
        at each time step that output is written. The resulting KML visualization will be an animation.

        The stream nodes are represented by cylinders where the z dimension/elevation represents the values. A color
        ramp is applied to make different values stand out even more. The method attempts to identify an appropriate
        scale factor for the z dimension, but it can be set manually using the styles dictionary.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            channelInputFile (:class:`gsshapy.orm.ChannelInputFile`): Channel input file object to be associated with
                this link node dataset file.
            path (str, optional): Path to file where KML will be written. Defaults to None.
            documentName (str, optional): Name of the KML document. This will be the name that appears in the legend.
                Defaults to the name of the link node dataset file.
            styles (dict, optional): Custom styles to apply to KML geometry. Defaults to empty dictionary.

                Valid keys (styles) include:
                   * zScale (float): multiplier to apply to the values (z dimension)
                   * radius (float): radius in meters of the node cylinder
                   * colorRampEnum (:mod:`mapkit.ColorRampGenerator.ColorRampEnum` or dict): Use ColorRampEnum to select a default color ramp or a dictionary with keys 'colors' and 'interpolatedPoints' to specify a custom color ramp. The 'colors' key must be a list of RGB integer tuples (e.g.: (255, 0, 0)) and the 'interpolatedPoints' must be an integer representing the number of points to interpolate between each color given in the colors list.

        Returns:
            str: KML string
        """
        # Constants
        DECMIAL_DEGREE_METER = 0.00001
        OPTIMAL_Z_MAX = 300  # meters

        # Default styles
        radiusMeters = 2 * DECMIAL_DEGREE_METER  # 2 meters
        zScale = 1
        colorRamp = ColorRampGenerator.generateDefaultColorRamp(ColorRampEnum.COLOR_RAMP_HUE)

        # Validate
        if not documentName:
            documentName = self.name

        if 'zScale' in styles:
            try:
                float(styles['zScale'])
                zScale = styles['zScale']

            except ValueError:
                log.warn('zScale must be a valid number representing z dimension multiplier.')

        if 'radius' in styles:
            try:
                float(styles['radius'])
                radiusMeters = styles['radius'] * DECMIAL_DEGREE_METER

            except ValueError:
                log.warn('radius must be a number representing the radius of the value cylinders in meters.')

        if 'colorRampEnum' in styles:
            colorRampEnum = styles['colorRampEnum']

            if isinstance(colorRampEnum, dict):
                colorRamp = ColorRampGenerator.generateCustomColorRamp(colorRampEnum['colors'], colorRampEnum['interpolatedPoints'])
            elif isinstance(colorRampEnum, int):
                colorRamp = ColorRampGenerator.generateDefaultColorRamp(colorRampEnum)

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

        # Calculate min and max values for the color ramp
        minValue = 0.0
        maxValue = session.query(func.max(NodeDataset.value)).\
                           filter(NodeDataset.linkNodeDatasetFile == self).\
                           filter(NodeDataset.status == 1).\
                           scalar()

        avgValue = session.query(func.avg(NodeDataset.value)).\
                           filter(NodeDataset.linkNodeDatasetFile == self).\
                           filter(NodeDataset.status == 1).\
                           scalar()

        # Calculate automatic zScale if not assigned
        if 'zScale' not in styles:
            zScale = OPTIMAL_Z_MAX / ((maxValue + avgValue) / 2)

        # Map color ramp to values
        mappedColorRamp = ColorRampGenerator.mapColorRampToValues(colorRamp, minValue, maxValue)

        if len(startTimeParts) > 5:
            # Default start date time to epoch
            startDateTime = datetime(year=int(startTimeParts[2]) or 1970,
                                     month=int(startTimeParts[1]) or 1,
                                     day=int(startTimeParts[0]) or 1,
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
            # Create current datetime objects
            timeSpanBegin = startDateTime + (linkNodeTimeStep.timeStep * timeStepDelta)
            timeSpanEnd = timeSpanBegin + timeStepDelta

            # Get Link Datasets
            linkDatasets = linkNodeTimeStep.linkDatasets

            for linkDataset in linkDatasets:
                # Don't process special link datasets (with node counts of -1 or 0)
                if linkDataset.numNodeDatasets <= 0:
                    break

                # Get Node Datasets
                nodeDatasets = linkDataset.nodeDatasets

                for nodeDataset in nodeDatasets:
                    # Get node
                    node = nodeDataset.node
                    link = node.streamLink
                    extrude = nodeDataset.value

                    # Don't extrude below 0
                    if nodeDataset.value < 0.0:
                        extrude = 0.0

                    # Convert to circle
                    circleString = converter.getPointAsKmlCircle(tableName=node.tableName,
                                                                 radius=radiusMeters,
                                                                 extrude=extrude,
                                                                 zScaleFactor=zScale,
                                                                 geometryId=node.id)

                    # Convert alpha from 0.0-1.0 decimal to 00-FF string
                    integerAlpha = mappedColorRamp.getAlphaAsInteger()

                    # Get RGB color from color ramp and convert to KML hex ABGR string with alpha
                    integerRGB = mappedColorRamp.getColorForValue(nodeDataset.value)

                    # Make color ABGR string
                    colorString = '%02X%02X%02X%02X' % (integerAlpha,
                                                        integerRGB[mappedColorRamp.B],
                                                        integerRGB[mappedColorRamp.G],
                                                        integerRGB[mappedColorRamp.R])

                    # Create placemark
                    placemark = ET.SubElement(document, 'Placemark')

                    # Create style tag and setup styles
                    style = ET.SubElement(placemark, 'Style')

                    # Set polygon line style
                    lineStyle = ET.SubElement(style, 'LineStyle')

                    # Disable lines by setting line width to 0
                    lineWidth = ET.SubElement(lineStyle, 'width')
                    lineWidth.text = str(0)

                    # Set polygon fill color
                    polyStyle = ET.SubElement(style, 'PolyStyle')
                    polyColor = ET.SubElement(polyStyle, 'color')
                    polyColor.text = colorString

                    if len(linkNodeTimeSteps) > 1:
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

                    # Embed node data
                    nodeExtendedData = ET.SubElement(placemark, 'ExtendedData')

                    nodeNumberData = ET.SubElement(nodeExtendedData, 'Data', name='node_number')
                    nodeNumberValue = ET.SubElement(nodeNumberData, 'value')
                    nodeNumberValue.text = str(node.nodeNumber)

                    nodeLinkNumberData = ET.SubElement(nodeExtendedData, 'Data', name='link_number')
                    nodeLinkNumberValue = ET.SubElement(nodeLinkNumberData, 'value')
                    nodeLinkNumberValue.text = str(link.linkNumber)

                    nodeElevationData = ET.SubElement(nodeExtendedData, 'Data', name='value')
                    nodeElevationValue = ET.SubElement(nodeElevationData, 'value')
                    nodeElevationValue.text = str(nodeDataset.value)


        kmlString = ET.tostring(kml)

        if path:
            with open(path, 'w') as f:
                f.write(kmlString)

        return kmlString



    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
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
        for card, chunkList in iteritems(chunks):
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
                            # Split the line
                            spLinkLine = line.strip().split()

                            # Create LinkDataset GSSHAPY object
                            linkDataset = LinkDataset()
                            linkDataset.numNodeDatasets = int(spLinkLine[0])
                            linkDataset.timeStep = timeStep
                            linkDataset.linkNodeDatasetFile = self

                            # Parse line into NodeDatasets
                            NODE_VALUE_INCREMENT = 2
                            statusIndex = 1
                            valueIndex = statusIndex + 1

                            # Parse line into node datasets
                            if linkDataset.numNodeDatasets > 0:
                                for i in range(0, linkDataset.numNodeDatasets):
                                    # Create NodeDataset GSSHAPY object
                                    nodeDataset = NodeDataset()
                                    nodeDataset.status = int(spLinkLine[statusIndex])
                                    nodeDataset.value = float(spLinkLine[valueIndex])
                                    nodeDataset.linkDataset = linkDataset
                                    nodeDataset.linkNodeDatasetFile = self

                                    # Increment to next status/value pair
                                    statusIndex += NODE_VALUE_INCREMENT
                                    valueIndex += NODE_VALUE_INCREMENT
                            else:
                                nodeDataset = NodeDataset()
                                nodeDataset.value = float(spLinkLine[1])
                                nodeDataset.linkDataset = linkDataset
                                nodeDataset.linkNodeDatasetFile = self



    def _write(self, session, openFile, replaceParamFile):
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

                if linkDataset.numNodeDatasets > 0:
                    for nodeDataset in nodeDatasets:
                        # Write status and value
                        openFile.write('{0}  {1:.5f}   '.format(nodeDataset.status, nodeDataset.value))
                else:
                    for nodeDataset in nodeDatasets:
                        # Write status and value

                        if linkDataset.numNodeDatasets < 0:
                            openFile.write('{0:.5f}'.format(nodeDataset.value))
                        else:
                            openFile.write('{0:.3f}'.format(nodeDataset.value))

                # Write new line character after each link dataset
                openFile.write('\n')

            # Insert empty line between time steps
            openFile.write('\n')


class LinkNodeTimeStep(DeclarativeBase):
    """
    Object containing data for a single time step of a link node dataset file. Each link node time step will have
    a link dataset for each stream link in the channel input file.
    """
    __tablename__ = 'lnd_time_steps'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    linkNodeDatasetFileID = Column(Integer, ForeignKey('lnd_link_node_dataset_files.id'))  #: FK

    # Value Columns
    timeStep = Column(Integer)  #: INTEGER

    # Relationship Properties
    linkNodeDataset = relationship('LinkNodeDatasetFile', back_populates='timeSteps')  #: RELATIONSHIP
    linkDatasets = relationship('LinkDataset', back_populates='timeStep')  #: RELATIONSHIP

    def __init__(self, timeStep):
        self.timeStep = timeStep

    def __repr__(self):
        return '<TimeStep: %s>' % self.timeStep


class LinkDataset(DeclarativeBase):
    """
    Object containing data for a single link dataset in a link node dataset file. A link dataset will have a node
    dataset for each of the stream nodes belonging to the stream link that it is associated with.
    """
    __tablename__ = 'lnd_link_datasets'
    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    timeStepID = Column(Integer, ForeignKey('lnd_time_steps.id'))  #: FK
    streamLinkID = Column(Integer, ForeignKey('cif_links.id'))  #: FK
    linkNodeDatasetFileID = Column(Integer, ForeignKey('lnd_link_node_dataset_files.id'))  #: FK

    # Value Columns
    numNodeDatasets = Column(Integer)  #: INTEGER

    # Relationship Properties
    linkNodeDatasetFile = relationship('LinkNodeDatasetFile', back_populates='linkDatasets')  #: RELATIONSHIP
    timeStep = relationship('LinkNodeTimeStep', back_populates='linkDatasets')  #: RELATIONSHIP
    nodeDatasets = relationship('NodeDataset', back_populates='linkDataset')  #: RELATIONSHIP
    link = relationship('StreamLink', back_populates='datasets')  #: RELATIONSHIP

    def __repr__(self):
        return '<LinkDataset: NumberNodeDatasets=%s>' % self.numNodeDatasets


class NodeDataset(DeclarativeBase):
    """
    Object containing data for a single node dataset in a link node dataset file. The values stored in a link node
    dataset file are found in the node datasets.
    """
    __tablename__ = 'lnd_node_datasets'
    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    linkDatasetID = Column(Integer, ForeignKey('lnd_link_datasets.id'))  #: FK
    streamNodeID = Column(Integer, ForeignKey('cif_nodes.id'))  #: FK
    linkNodeDatasetFileID = Column(Integer, ForeignKey('lnd_link_node_dataset_files.id'))  #: FK

    # Value Columns
    status = Column(Integer)  #: INTEGER
    value = Column(Float)  #: FLOAT

    # Relationship Properties
    linkNodeDatasetFile = relationship('LinkNodeDatasetFile', back_populates='nodeDatasets')  #: RELATIONSHIP
    linkDataset = relationship('LinkDataset', back_populates='nodeDatasets')  #: RELATIONSHIP
    node = relationship('StreamNode', back_populates='datasets')  #: RELATIONSHIP

    def __repr__(self):
        return '<NodeDataset: Status=%s, Value=%s>' % (self.status, self.value)
