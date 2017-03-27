"""
********************************************************************************
* Name: ProjectionFileModel
* Author: Nathan Swain
* Created On: August 2, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

__all__ = ['GenericFile']

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, LargeBinary
from sqlalchemy.orm import relationship

from . import DeclarativeBase
from ..base.file_base import GsshaPyFileObjectBase


class GenericFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for Generic Files.

    This object is used to store files that are not fully supported in GsshaPy. The files must be non-binary text files
    to be stored as a GenericFile object. The object simply reads the contents of the file into a text field during
    reading and dumps it again during writing. This allows these files to be carried through the entire GsshaPy cycle.
    """
    __tablename__ = 'gen_generic_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))  #: FK

    # Value Columns
    text = Column(String)  #: STRING
    binary = Column(LargeBinary)  #: BINARY
    name = Column(String)  #: STRING
    fileExtension = Column(String, default='txt')  #: STRING

    # Relationship Properties
    projectFile = relationship('ProjectFile', back_populates='genericFiles')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def __repr__(self):
        return '<GenericFile: Name=%s>' % (self.name)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
        """
        Generic File Read from File Method
        """
        # Persist name and extension of file
        self.name = name
        self.fileExtension = extension

        # Open file and parse into a data structure
        with open(path, 'r') as f:
            self.text = f.read()

    def _write(self, session, openFile, replaceParamFile):
        """
        Projection File Write to File Method
        """
        # Write lines
        openFile.write(self.text)
