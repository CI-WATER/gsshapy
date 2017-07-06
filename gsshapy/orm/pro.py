"""
********************************************************************************
* Name: ProjectionFileModel
* Author: Nathan Swain
* Created On: August 2, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

__all__ = ['ProjectionFile']

from io import open as io_open
import os

from builtins import str as text
from sqlalchemy import Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from mapkit import lookupSpatialReferenceID

from . import DeclarativeBase
from ..base.file_base import GsshaPyFileObjectBase


class ProjectionFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for the Projection File.

    The projection file contains the Well Known Text version of the spatial reference system for the GSSHA model. This
    file contains a single line, so the file contents is stored in the file object. No supporting objects are needed.

    See: http://www.geoapi.org/3.0/javadoc/org/opengis/referencing/doc-files/WKT.html
         http://spatialreference.org/
    """
    __tablename__ = 'pro_projection_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK

    # Value Columns
    projection = Column(String)  #: STRING
    fileExtension = Column(String, default='pro')  #: STRING

    # Relationship Properties
    projectFile = relationship('ProjectFile', uselist=False, back_populates='projectionFile')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def __repr__(self):
        return '<ProjectionFile: Projection=%s>' % self.projection

    @classmethod
    def lookupSpatialReferenceID(cls, directory, filename):
        """
        Look up spatial reference system using the projection file.

        Args:
            directory (str):
            filename (str):

        Return:
            int: Spatial Reference ID
        """

        path = os.path.join(directory, filename)

        with open(path, 'r') as f:
            srid = lookupSpatialReferenceID(f.read())

        return srid


    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
        """
        Projection File Read from File Method
        """
        # Set file extension property
        self.fileExtension = extension

        # Open file and parse into a data structure
        with io_open(path, 'r') as f:
            self.projection = f.read()

    def _write(self, session, openFile, replaceParamFile):
        """
        Projection File Write to File Method
        """
        # Write lines
        openFile.write(text(self.projection))

    def _namePreprocessor(self, name):
        """
        Preprocess Name Method
        """
        if '_prj' not in name:
            name += '_prj'

        return name
