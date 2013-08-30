'''
********************************************************************************
* Name: Hydro-MeteorologicalModel
* Author: Nathan Swain
* Created On: May 14, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

from datetime import datetime

__all__ = ['HmetFile','HmetRecord']

import os

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float, DateTime
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase

class HmetFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    '''
    __tablename__ = 'hmet_files'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    
    # Relationship Properties
    hmetRecords = relationship('HmetRecord', back_populates='hmetFile') #: RELATIONSHIP
    projectFile = relationship('ProjectFile', uselist=False, back_populates='hmetFile') #: RELATIONSHIP
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
        

    def __repr__(self):
        return '<HmetFile: Name=%s, Description=%s>' % (self.name, self.description)
    
    def _read(self):
        '''
        Read HMET WES from File Method
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
        
    def _write(self, session, openFile):
        '''
        Write HMET WES to File Method
        '''
        ## TODO: Ensure Other HMET Formats are supported
        hmetRecords = self.hmetRecords
        
        for record in hmetRecords:
            openFile.write('%s\t%s\t%s\t%s\t%.3f\t%s\t%s\t%s\t%s\t%.2f\t%.2f\n' % (
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
    '''
    __tablename__ = 'hmet_records'
    
    tableName = __tablename__ #: Database tablename
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    hmetConfigID = Column(Integer, ForeignKey('hmet_files.id')) #: INTEGER
    
    # Value Columns
    hmetDateTime = Column(DateTime, nullable=False) #: DATETIME
    barometricPress = Column(Float, nullable=False) #: FLOAT
    relHumidity = Column(Integer, nullable=False) #: INTEGER
    totalSkyCover = Column(Integer, nullable=False) #: INTEGER
    windSpeed = Column(Integer, nullable=False) #: INTEGER
    dryBulbTemp = Column(Integer, nullable=False) #: INTEGER
    directRad = Column(Float, nullable=False) #: FLOAT
    globalRad = Column(Float, nullable=False) #: FLOAT
    
    # Relationship Properties
    hmetFile = relationship('HmetFile', back_populates='hmetRecords') #: RELATIONSHIP
    
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
