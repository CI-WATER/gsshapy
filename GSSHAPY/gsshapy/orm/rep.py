'''
********************************************************************************
* Name: Replace Files Model
* Author: Nathan Swain
* Created On: August 5, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['ReplaceParamFile',
           'TargetParameter',
           'ReplaceValFile']
import os

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

class ReplaceParamFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    '''
    __tablename__ = 'rep_replace_param_files'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    
    # Value Columns
    numParameters = Column(Integer, nullable=False) #: INTEGER
    
    # Relationship Properites
    projectFile = relationship('ProjectFile', uselist=False, back_populates='replaceParamFile') #: RELATIONSHIP
    targetParameters = relationship('TargetParameter', back_populates='replaceParamFile') #: RELATIONSHIP
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
    
    def _read(self):
        '''
        Replace Param File Read from File Method
        '''
               
        # Open file and parse into a data structure
        with open(self.PATH, 'r') as f:
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
        
    def _write(self, session, openFile):
        '''
        Replace Param File Write to File Method
        '''
        # Retrieve TargetParameter objects
        targets = self.targetParameters

        # Write lines
        openFile.write('%s\n' % self.numParameters)
        
        for target in targets:
            openFile.write('%s %s\n' % (target.targetVariable, target.varFormat))
            
class TargetParameter(DeclarativeBase):
    '''
    '''
    __tablename__ = 'rep_target_parameter'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    replaceParamFileID = Column(Integer, ForeignKey('rep_replace_param_files.id')) #: FK
    
    # Value Columns
    targetVariable = Column(String, nullable=False) #: STRING
    varFormat = Column(String, nullable=False) #: STRING
    
    # Relationship Properites
    replaceParamFile = relationship('ReplaceParamFile', back_populates='targetParameters') #: RELATIONSHIP
    
    def __init__(self, targetVariable, varFormat):
        self.targetVariable = targetVariable
        self.varFormat = varFormat
        
    def __repr__(self):
        return '<TargetParameter: TargetVariable=%s, VarFormat=%s>' % (self.targetVariable, self.varFormat)

class ReplaceValFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    '''
    __tablename__ = 'rep_replace_val_files'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    
    # Value Columns
    values = Column(String, nullable=False) #: STRING
    
    # Relationship Properites
    projectFile = relationship('ProjectFile', uselist=False, back_populates='replaceValFile') #: RELATIONSHIP
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
    
    def _read(self):
        '''
        Replace Val File Read from File Method
        '''
        # Open file and parse into a data structure
        with open(self.PATH, 'r') as f:
            self.values = f.read()
        
    def _write(self, session, openFile):
        '''
        Replace Val File Write to File Method
        '''
        # Write lines               
        openFile.write(self.values)
            

