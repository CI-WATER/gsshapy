"""
********************************************************************************
* Name: Replace Files Model
* Author: Nathan Swain
* Created On: August 5, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from __future__ import unicode_literals

__all__ = ['ReplaceParamFile',
           'TargetParameter',
           'ReplaceValFile']

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from . import DeclarativeBase
from ..base.file_base import GsshaPyFileObjectBase


class ReplaceParamFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for the Replacement Parameters File.

    The contents of this file are abstracted to one other supporting object: :class:`.TargetParameter`. Use this object
    in conjunction with the :class:`.ReplaceValFile`.

    See: http://www.gsshawiki.com/Alternate_Run_Modes:Simulation_Setup_for_Alternate_Run_Modes
         http://www.gsshawiki.com/File_Formats:Project_File_Format#Replacement_cards
    """
    __tablename__ = 'rep_replace_param_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK

    # Value Columns
    numParameters = Column(Integer)  #: INTEGER
    fileExtension = Column(String, default='txt')  #: STRING

    # Relationship Properties
    projectFile = relationship('ProjectFile', uselist=False, back_populates='replaceParamFile')  #: RELATIONSHIP
    targetParameters = relationship('TargetParameter', back_populates='replaceParamFile')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
        """
        Replace Param File Read from File Method
        """
        # Set file extension property
        self.fileExtension = extension

        # Open file and parse into a data structure
        with open(path, 'r') as f:
            for line in f:
                sline = line.strip().split()
                if len(sline) == 1:
                    self.numParameters = sline[0]
                else:
                    # Create GSSHAPY TargetParameter object
                    target = TargetParameter(targetVariable=sline[0],
                                             varFormat=sline[1])

                    # Associate TargetParameter with ReplaceParamFile
                    target.replaceParamFile = self

    def _write(self, session, openFile, replaceParamFile):
        """
        Replace Param File Write to File Method
        """
        # Retrieve TargetParameter objects
        targets = self.targetParameters

        # Write lines
        openFile.write('%s\n' % self.numParameters)

        for target in targets:
            openFile.write('%s %s\n' % (target.targetVariable, target.varFormat))


class TargetParameter(DeclarativeBase):
    """
    Object containing data for a single target value as defined in the Replacement Parameters File.
    """
    __tablename__ = 'rep_target_parameter'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    replaceParamFileID = Column(Integer, ForeignKey('rep_replace_param_files.id'))  #: FK

    # Value Columns
    targetVariable = Column(String)  #: STRING
    varFormat = Column(String)  #: STRING

    # Relationship Properties
    replaceParamFile = relationship('ReplaceParamFile', back_populates='targetParameters')  #: RELATIONSHIP

    def __init__(self, targetVariable, varFormat):
        self.targetVariable = targetVariable
        self.varFormat = varFormat

    def __repr__(self):
        return '<TargetParameter: TargetVariable=%s, VarFormat=%s>' % (self.targetVariable, self.varFormat)


class ReplaceValFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for the Replacement Values File.

    Use this object in conjunction with the :class:`.ReplaceParamFile`.

    See: http://www.gsshawiki.com/Alternate_Run_Modes:Simulation_Setup_for_Alternate_Run_Modes
         http://www.gsshawiki.com/File_Formats:Project_File_Format#Replacement_cards
    """
    __tablename__ = 'rep_replace_val_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK

    # Value Columns
    values = Column(String)  #: STRING
    fileExtension = Column(String, default='txt')  #: STRING

    # Relationship Properties
    projectFile = relationship('ProjectFile', uselist=False, back_populates='replaceValFile')  #: RELATIONSHIP
    lines = relationship('ReplaceValLine', back_populates='replaceValFile')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
        """
        Replace Val File Read from File Method
        """
        # Set file extension property
        self.fileExtension = extension

        # Open file and parse into a data structure
        with open(path, 'r') as f:
            for line in f:
                valLine = ReplaceValLine()
                valLine.contents = line
                valLine.replaceValFile = self

    def _write(self, session, openFile, replaceParamFile):
        """
        Replace Val File Write to File Method
        """
        # Write lines
        for line in self.lines:
            openFile.write(line.contents)


class ReplaceValLine(DeclarativeBase):
    """
    Object containing data for a single line in the replacement value file. Each line represents a new realization of the
    parameters listed in the replacement parameter file.
    """
    __tablename__ = 'rep_replace_val_lines'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    replaceValFileID = Column(Integer, ForeignKey('rep_replace_val_files.id'))  #: FK

    # Value Columns
    contents = Column(String)  #: STRING

    # Relationship Properties
    replaceValFile = relationship('ReplaceValFile', back_populates='lines')  #: RELATIONSHIP


            

