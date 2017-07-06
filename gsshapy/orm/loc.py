"""
********************************************************************************
* Name: OutputLocationModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from __future__ import unicode_literals

__all__ = ['OutputLocationFile',
           'OutputLocation']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from . import DeclarativeBase
from ..base.file_base import GsshaPyFileObjectBase


class OutputLocationFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for the output location type files.

    There are several files that are used to specify output at internal locations in the model. These files are
    specified by the following cards in the project file: IN_HYD_LOCATION, IN_THETA_LOCATION, IN_GWFLUX_LOCATION,
    IN_SED_LOC, OVERLAND_DEPTH_LOCATION, OVERLAND_WSE_LOCATION, and OUT_WELL_LOCATION.

    Output location files contain either a list of cell addresses (i and j) for output from the grid **or** a list of
    link node addresses (link number and node number) for output requested from the stream network. The output is
    generated as timeseries at each location. The contents of this file is abstracted to one other object:
    :class:`.OutputLocation`.

    See: http://www.gsshawiki.com/Project_File:Output_Files_%E2%80%93_Required
    """

    __tablename__ = 'loc_output_location_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))  #: FK

    # Value Columns
    fileExtension = Column(String, default='ihl')  #: STRING
    numLocations = Column(Integer, nullable=False)  #: INTEGER

    # Relationship Properties
    projectFile = relationship('ProjectFile', back_populates='outputLocationFiles')  #: RELATIONSHIP
    outputLocations = relationship('OutputLocation', back_populates='outputLocationFile')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
        """
        Generic Output Location Read from File Method
        """
        # Assign file extension attribute to file object
        self.fileExtension = extension

        # Open file and parse into a data structure
        with open(path, 'r') as f:
            for line in f:
                sline = line.strip().split()

                if len(sline) == 1:
                    self.numLocations = sline[0]
                else:
                    # Create GSSHAPY OutputLocation object
                    location = OutputLocation(linkOrCellI=sline[0],
                                              nodeOrCellJ=sline[1])

                    # Associate OutputLocation with OutputLocationFile
                    location.outputLocationFile = self

    def _write(self, session, openFile, replaceParamFile):
        """
        Generic Output Location Write to File Method
        """
        # Retrieve output locations
        locations = self.outputLocations

        # Write lines
        openFile.write('%s\n' % self.numLocations)

        for location in locations:
            openFile.write('%s %s\n' % (location.linkOrCellI,
                                        location.nodeOrCellJ))


class OutputLocation(DeclarativeBase):
    """
    Object containing the data for a single output location coordinate pair. Depending on whether the file requests
    output on the grid or on the stream network, the coordinate pair will represent either cell i j or link node
    coordinates, respectively.
    """

    __tablename__ = 'loc_output_locations'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    outputLocationFileID = Column(Integer, ForeignKey('loc_output_location_files.id'))  #: FK

    # Value Columns
    linkOrCellI = Column(Integer)  #: INTEGER
    nodeOrCellJ = Column(Integer)  #: INTEGER

    # Relationship Properties
    outputLocationFile = relationship('OutputLocationFile', back_populates='outputLocations')  #: RELATIONSHIP

    def __init__(self, linkOrCellI, nodeOrCellJ):
        self.linkOrCellI = linkOrCellI
        self.nodeOrCellJ = nodeOrCellJ

    def __repr__(self):
        return '<OutputLocation: LinkOrCellI=%s, NodeOrCellJ=%s>' % (self.linkNumber, self.nodeNumber)