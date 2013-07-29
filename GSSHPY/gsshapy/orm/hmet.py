'''
********************************************************************************
* Name: Hydro-Meteorological Tables
* Author: Nathan Swain
* Created On: May 14, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

from datetime import datetime

__all__ = ['HmetFile','HmetRecord']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, String, Float, DateTime
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase

class HmetFile(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'hmet_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Relationship Properties
    hmetRecords = relationship('HmetRecord', back_populates='hmetFile')
    projectFile = relationship('ProjectFile', uselist=False, back_populates='hmetFile')
    
    # Global Properties
    PATH = ''
    FILENAME = ''
    DIRECTORY = ''
    SESSION = None
    
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        self.FILENAME = filename
        self.DIRECTORY = directory
        self.SESSION = session
        self.PATH = '%s%s' % (self.DIRECTORY, self.FILENAME)
        

    def __repr__(self):
        return '<HmetFile: Name=%s, Description=%s>' % (self.name, self.description)
    
    def readWES(self):
        '''
        Read HMET_WES from File Method
        '''
        # Open file and parse into HmetRecords
        with open(self.PATH, 'r') as hmetFile:
            
            for line in hmetFile:
                sline = line.strip().split()
                
                # Extract data time from record
                dateTime = datetime(int(sline[0]), int(sline[1]), int(sline[2]), int(sline[3]))
                
                # Intitialize GSSHAPY HmetRecord object
                hmetRecord = HmetRecord(hmetDateTime=dateTime,
                                        barometricPress=sline[4],
                                        relHumidity=sline[5],
                                        totalSkyCover=sline[6],
                                        windSpeed=sline[7],
                                        dryBulbTemp=sline[8],
                                        directRad=sline[9],
                                        globalRad=sline[10])
                
                # Associate HmetRecord with HmetFile
                hmetRecord.hmetFile = self
        
    def writeWES(self, session, directory, filePrefix):
        '''
        Write HMET_WES to File Method
        '''
        # NOTE: For HMET_WES Files, the filePrefix is the entire filename
        
        # Initiate hmet wes file
        fullPath = '%s%s' % (directory, filePrefix)
        
        with open(fullPath, 'w') as hmetFile:
            # Retrieve HmetRecords
            hmetRecords = self.hmetRecords
            
            for record in hmetRecords:
                hmetFile.write('%s\t%s\t%s\t%s\t%.3g\t%s\t%s\t%s\t%s\t%.2f\t%.2f\n' % (
                               record.hmetDateTime.year,
                               record.hmetDateTime.month,
                               record.hmetDateTime.day,
                               record.hmetDateTime.hour,
                               record.barometricPress,
                               record.relHumidity,
                               record.totalSkyCover,
                               record.windSpeed,
                               record.dryBulbTemp,
                               record.directRad,
                               record.globalRad))
                



class HmetRecord(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'hmet_records'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    hmetConfigID = Column(Integer, ForeignKey('hmet_files.id'))
    
    # Value Columns
    hmetDateTime = Column(DateTime, nullable=False)
    barometricPress = Column(Float, nullable=False)
    relHumidity = Column(Integer, nullable=False)
    totalSkyCover = Column(Integer, nullable=False)
    windSpeed = Column(Integer, nullable=False)
    dryBulbTemp = Column(Integer, nullable=False)
    directRad = Column(Float, nullable=False)
    globalRad = Column(Float, nullable=False)
    
    # Relationship Properties
    hmetFile = relationship('HmetFile', back_populates='hmetRecords')
    
    def __init__(self, hmetDateTime, barometricPress, relHumidity, totalSkyCover, windSpeed, dryBulbTemp, directRad, globalRad):
        '''
        Constructor
        '''
        self.hmetDateTime = hmetDateTime
        self.barometricPress = barometricPress
        self.relHumidity = relHumidity
        self.totalSkyCover = totalSkyCover
        self.windSpeed = windSpeed
        self.dryBulbTemp = dryBulbTemp
        self.directRad = directRad
        self.globalRad = globalRad

    def __repr__(self):
        return '<HmetRecord: DateTime=%s, BarometricPressure=%s, RelHumidity=%s, TotalSkyCover=%s, WindSpeed=%s, DryBulbTemp=%s, DirectRad=%s, GlobalRad=%s>' % (
                self.hmetDateTime,
                self.barometricPress,
                self.relHumidity,
                self.totalSkyCover,
                self.windSpeed,
                self.dryBulbTemp,
                self.directRad,
                self.globalRad)
