'''
********************************************************************************
* Name: RaserMapModel
* Author: Nathan Swain
* Created On: August 1, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['RasterMapFile']

import os, subprocess

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from geoalchemy2 import Raster

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

class RasterMapFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    '''
    __tablename__ = 'raster_maps'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id')) #: FK
    
    # Value Columns
    fileExtension = Column(String, nullable=False) #: STRING
    raster = Column(Raster) #: RASTER
    
    # Relationship Properites
    projectFile = relationship('ProjectFile', back_populates='maps') #: RELATIONSHIP
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
        
    def __repr__(self):
        return '<RasterMap: FileExtension=%s>' % (self.fileExtension)
    
    def _read(self):
        '''
        Raster Map File Read from File Method
        '''
        # Assign file extension attribute to file object
        self.fileExtension = self.EXTENSION
        
        # Must read in using the raster2pgsql commandline tool.
        process = subprocess.Popen(
                                   [
                                    '/Applications/Postgres.app/Contents/MacOS/bin/raster2pgsql',
                                    '-a',
                                    '-s',
                                    '4236',
                                    '-M',
                                    self.PATH, self.__tablename__
                                    ],
                                    stdout=subprocess.PIPE
                                   )
        
        # This commandline tool generates the SQL to load the raster into the database
        # However, we want to use SQLAlchemy to load the values into the database. 
        # We do this by extracting the value from the sql that is generated.
        sql, error = process.communicate()        
        
        if sql:
            # This esoteric line is used to extract only the value of the raster (which is stored as a Well Know Binary string)
            
            # Example of Output:
            # BEGIN;
            # INSERT INTO "idx_index_maps" ("rast") VALUES ('0100...56C096CE87'::raster);
            # END;
            
            # The WKB is wrapped in single quotes. Splitting on single quotes isolates it as the 
            # second item in the resulting list.
            wellKnownBinary =  sql.split("'")[1]
            print wellKnownBinary
            
        self.raster = wellKnownBinary
        
    def _write(self, session, openFile):
        '''
        Raster Map File Write to File Method
        '''
        # Write file
        openFile.write(self.raster)

