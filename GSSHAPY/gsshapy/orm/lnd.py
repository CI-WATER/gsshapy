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
           'TimeStep',
           'LinkNodeLine',
           'LinkDataset',
           'NodeDataset']

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, Float
from sqlalchemy.orm import relationship

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

    # Value Columns
    fileExtension = Column(String, default='lnd')  #: STRING
    name = Column(String, nullable=False)  #: STRING
    numLinks = Column(Integer, nullable=False)  #: INTEGER
    timeStep = Column(Integer, nullable=False)  #: INTEGER
    numTimeSteps = Column(Integer, nullable=False)  #: INTEGER
    startTime = Column(String, nullable=False)  #: STRING

    # Relationship Properties
    projectFile = relationship('ProjectFile', back_populates='linkNodeDatasets')  #: RELATIONSHIP
    timeSteps = relationship('TimeStep', back_populates='linkNodeDataset')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    ## TODO: Implement these methods

    def linkToChannelInputFile(self, channelInputFile):
        """
        Create database relationships between the dataset and the channel input file. This is
        done so that the geometry associated with links and nodes can be associated with the
        link and node datasets.
        """

        # Hint: Upstream and downstream links overlap one node. The first node in the downstream link is the same as the last node in the upstream link.
        # More Details Here: http://www.gsshawiki.com/Surface_Water_Routing:Channel_Routing

    def getAsKmlAnimation(self):
        """
        Generate a KML visualization of the the datset file.
        """

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
                    self.timeStep = schunk[1]

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
                            timeStep = TimeStep(timeStep=sline[1])
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
        openFile.write('TIME_STEP     %s\n' % self.timeStep)
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


class TimeStep(DeclarativeBase):
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
    linkNodeLines = relationship('LinkNodeLine', back_populates='timeStep')  #: RELATIONSHIP
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
    timeStep = relationship('TimeStep', back_populates='linkDatasets')  #: RELATIONSHIP
    nodeDatasets = relationship('NodeDataset', back_populates='linkDataset')  #: RELATIONSHIP
    link = relationship('StreamLink', back_populates='datasets')  #: RELATIONSHIP


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
