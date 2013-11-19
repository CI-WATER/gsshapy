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
from gsshapy.mapit.RasterConverter import RasterConverter


class IndexMap(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    '''
    __tablename__ = 'idx_index_maps'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    mapTableFileID = Column(Integer, ForeignKey('cmt_map_table_files.id')) #: FK
    
    # Value Columns
    srid = Column(Integer) #: SRID
    name = Column(String, nullable=False) #: STRING
    filename = Column(String, nullable=False) #: STRING
    raster_text = Column(String) #: STRING
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
        # Open file and read plain raster_text into raster_text field
        with open(self.PATH, 'r') as f:
            self.raster_text = f.read()
                
        if self.SPATIAL:
            # Assign file extension attribute to file object
            self.fileExtension = self.EXTENSION
            
            # Must read in using the raster2pgsql commandline tool.                    
            process = subprocess.Popen(
                                       [
                                        self.RASTER2PGSQL_PATH,
                                        '-a',
                                        '-s',
                                        str(self.SRID),
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
                
            self.raster = wellKnownBinary            
        
#         print 'File Read:', self.filename
        
    def write(self, directory, name=None, session=None):
        '''
        Index Map Write to File Method
        '''
        
        # Initiate file
        if name !=None:
            filename = '%s.%s' % (name, self.EXTENSION)
            filePath = os.path.join(directory, filename)
        else:
            filePath = os.path.join(directory, self.filename)
    
        # If the raster field is not empty, write from this field
        if type(self.raster) != type(None):
            '''
            '''
            # Use the ST_AsGDALRaster function of PostGIS to retrieve the 
            # raster as an ascii grid. Function defined as per instructions
            # to make a geoalchemy function from 
            # see: http://www.postgis.org/documentation/manual-svn/RT_ST_AsGDALRaster.html
            # Cast as a string because ST_AsGDALRaster returns as a buffer object
            arcInfoGrid = str(session.scalar(self.raster.ST_AsGDALRaster('AAIGRID'))).splitlines()
            
            ## Convert arcInfoGrid to GRASS ASCII format ##
            # Get values from heaser which look something this:
            # ncols        67
            # nrows        55
            # xllcorner    425802.32143212341
            # yllcorner    44091450.41551345213
            # cellsize     90.0000000
            # ...
            nCols = int(arcInfoGrid[0].split()[1])
            nRows = int(arcInfoGrid[1].split()[1])
            xLLCorner = float(arcInfoGrid[2].split()[1])
            yLLCorner = float(arcInfoGrid[3].split()[1])
            cellSize = float(arcInfoGrid[4].split()[1])
            
            # Remove old headers
            for i in range(0, 5):
                arcInfoGrid.pop(0)
            
            ## Calculate values for GRASS ASCII headers ##
            # These should look like this:
            # north: 4501028.972140
            # south: 4494548.972140
            # east: 460348.288604
            # west: 454318.288604
            # rows: 72
            # cols: 67
            # ...
            
            # xLLCorner and yLLCorner represent the coordinates for the Lower Left corner of the raster
            north = yLLCorner + (cellSize * nRows)
            south = yLLCorner
            east = xLLCorner + (cellSize * nCols)
            west = xLLCorner
            
            # Create header Lines (the first shall be last and the last shall be first)
            grassHeader = ['cols: %s' % nCols,
                           'rows: %s' % nRows,
                           'west: %s' % west,
                           'east: %s' % east,
                           'south: %s' % south,
                           'north: %s' % north]
            
            # Insert grass headers into the grid
            for header in grassHeader:
                arcInfoGrid.insert(0, header)
            
            # Write to file
            with open(filePath, 'w') as mapFile:
                for line in arcInfoGrid:
                    mapFile.write(line.strip() + '\n')
            
        else:
            # Open file and write, raster_text only
            with open(filePath, 'w') as mapFile:
                mapFile.write(self.raster_text)
            
#         print 'File Written:', self.filename
        
        
        
    def getAsKmlGrid(self, session, path, ramp='rainbow', alpha=1.0):
        '''
        Get the raster in KML format
        '''
          
        if type(self.raster) != type(None):
            # Make sure the raster field is valid
            converter = RasterConverter(session=session,
                                        tableName=self.tableName,
                                        rasterId=self.id,
                                        outFilePath=path,
                                        name=self.filename,
                                        rasterType='discrete')
            
            converter.getAsKmlGrid(ramp=ramp, alpha=alpha)
                
            

    

    
    
    
    
    
    