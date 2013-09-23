'''
********************************************************************************
* Name: IndexMapModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['IndexMap']

import os, subprocess

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from geoalchemy2 import Raster

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase


class IndexMap(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    '''
    __tablename__ = 'idx_index_maps'
    
    tableName = __tablename__ #: Database tablename
    raster2pgsqlPath = '/Applications/Postgres.app/Contents/MacOS/bin/raster2pgsql'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    mapTableFileID = Column(Integer, ForeignKey('cmt_map_table_files.id')) #: FK
    
    # Value Columns
    srid = Column(Integer) #: SRID
    name = Column(String, nullable=False) #: STRING
    filename = Column(String, nullable=False) #: STRING
    raster = Column(Raster) #: RASTER
    
    # Relationship Properties
    mapTableFile = relationship('MapTableFile', back_populates='indexMaps') #: RELATIONSHIP
    mapTables = relationship('MapTable', back_populates='indexMap') #: RELATIONSHIP
    indices = relationship('MTIndex', back_populates='indexMap') #: RELATIONSHIP
    contaminants = relationship('MTContaminant', back_populates='indexMap') #: RELATIONSHIP
    
    # File Properties
    EXTENSION = 'idx'
    
    def __init__(self, directory, filename, session, name=None):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
        self.name = name
        self.filename = filename
        
    def __repr__(self):
        return '<IndexMap: Name=%s, Filename=%s, Raster=%s>' % (self.name, self.filename, self.raster)
    
    def __eq__(self, other):
        return (self.name == other.name and
                self.filename == other.filename and
                self.raster == other.raster)
    
    def _read(self):
        '''
        Index Map Read from File Method
        '''
        if self.SPATIAL:
            # Must read in using the raster2pgsql commandline tool.
            if self.srid:
                srid = self.srid
            else:
                srid = 4236
                
            process = subprocess.Popen(
                                       [
                                        self.raster2pgsqlPath,
                                        '-a',
                                        '-s',
                                        str(srid),
                                        '-M',
                                        self.PATH, 
                                        self.tableName
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
        
        else:
            ''''''
        
#         print 'File Read:', self.filename
        
    def write(self, directory, name=None, session=None):
        '''
        Index Map Write to File Method
        '''
        if self.SPATIAL:
            ''''''
            
        else:
            # Initiate file
            if name !=None:
                filename = '%s.%s' % (name, self.EXTENSION)
                filePath = os.path.join(directory, filename)
            else:
                filePath = os.path.join(directory, self.filename)
        
            # Open file and write
            with open(filePath, 'w') as mapFile:
                mapFile.write(self.raster)
            
#         print 'File Written:', self.filename
        
    

    
    
    
    
    
    