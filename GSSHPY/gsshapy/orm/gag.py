'''
********************************************************************************
* Name: PrecipitationModel
* Author: Nathan Swain
* Created On: Mar 6, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['PrecipFile',
           'PrecipEvent',
           'PrecipValue',
           'PrecipGage']

from sqlalchemy import ForeignKey, Column, Table
from sqlalchemy.types import Integer, DateTime, String, Float
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase, metadata
from gsshapy.lib import gpparse

assocPrecip = Table('assoc_precipitation_files_events', metadata,
    Column('precipFileID', Integer, ForeignKey('gag_precipitation_files.id')),
    Column('precipEventID', Integer, ForeignKey('gag_events.id'))
    )

class PrecipFile(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gag_precipitation_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Relationship Properties
    precipEvents = relationship('PrecipEvent', secondary=assocPrecip, back_populates='precipFiles')
    
    # Global Properties
    PATH = ''
    PROJECT_NAME = ''
    DIRECTORY = ''
    SESSION = None
    STRUCTURE = \
        [ \
            ["R", None,\
                [\
                    ["R", 1, ["C", "D", "T-EDESC"]],\
                    ["R", 1, ["C", "D", "I-PPP"]],\
                    ["R", 1, ["C", "D", "I-PPP"]],\
                    ["R", "NRGAG", ["C", "D", "F-X", "F-Y", "T-CDESC"]],\
                    ["R", "NRPDS" , ["C", "D", "I-YEAR", "I-MONTH", "I-DAY", "I-HOUR", "I-MIN", ["R", "NRGAG", ["C", "F-GAGVAL"]]]]\
                ]\
             ]\
        ]
        
    def __init__(self, directory, name, session):
        self.PROJECT_NAME = name
        self.DIRECTORY = directory
        self.SESSION = session
        self.PATH = '%s%s%s' % (self.DIRECTORY, self.PROJECT_NAME, '.gag')
        
    def __repr__(self):
        return '<PrecipitationFile>'
    
    def read(self):
        '''Precipitation Read from File Method'''
        events = []
        coordinates = []
        values = []
        
        evt = []
        gag = []
        val = []
        
        parsedFile= gpparse.gpparser(self.STRUCTURE, self.PATH)
        
        # Transform the gpparse result into something more useful
        for var in parsedFile.list:
            print var
            if var[3] == 'EDESC':
                currEvent = [var]
                events.append(currEvent)
            elif var[3] == 'NRGAG':
                currEvent.append(var)
            elif var[3] == 'NRPDS':
                currEvent.append(var)
            elif var[3] == 'X':
                currCoord = [var]
                currEvent.append(currCoord)
            elif var[3] == 'Y':
                currCoord.append(var)
            elif var[3] == 'CDESC':
                currCoord.append(var)
            elif var[3] == 'YEAR':
                currVal = [var]
                currEvent.append(currVal)
            else:
                currVal.append(var)
                               
        for e in events:
            for i in e:
                print i
            
            if e[1][3] == 'NRGAG':
                ngag = int(e[1][5])
                npds = int(e[2][5])
            elif e[1][3] == 'NRPDS':
                ngag = int(e[2][5])
                npds = int(e[1][5])
            
            evt.append(PrecipEvent(description=e[0][5], numGages=ngag, numPeriods=npds))
            
            if ngag > 0:
                print 'yes'
                gag.append(PrecipGage())
                 
        
        print evt
        
        
    

class PrecipEvent(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gag_events'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    description = Column(String, nullable=False)
    nrGag = Column(Integer, nullable=False)
    nrPds = Column(Integer, nullable=False)
    
    # Relationship Properties
    values = relationship('PrecipValue', back_populates='event')
    precipFiles = relationship('PrecipFile', secondary=assocPrecip, back_populates='precipEvents')
    
    def __init__(self, description, numGages, numPeriods):
        '''
        Constructor
        '''
        #TODO - add validation
        self.description = description
        self.nrGag = numGages
        self.nrPds = numPeriods
        

    def __repr__(self):
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.description,self.nrGag,self.nrPds)
    
    
class PrecipValue(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gag_values'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    eventID = Column(Integer, ForeignKey('gag_events.id'))
    coordID = Column(Integer, ForeignKey('gag_coord.id'))
    
    # Value Columns
    valueType = Column(String, nullable=False)
    dateTime = Column(DateTime, nullable=False)
    value = Column(Float, nullable=False)
    
    # Relationship Properties
    event = relationship('PrecipEvent', back_populates='values')
    gage = relationship('PrecipGage', back_populates='values')

    def __init__(self, valueType, dateTime, value):
        '''
        Constructor
        '''
        self.valueType = valueType
        self.dateTime = dateTime
        self.value = value
        

    def __repr__(self):
        return '<PrecipValue: Type=%s, DateTime=%s, Value=%s>' % (self.valueType, self.dateTime, self.value)
    

    
class PrecipGage(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gag_coord'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    description = Column(String)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    
    # Relationship Properties
    values = relationship('PrecipValue', back_populates='gage')
    
    def __init__(self, description, x, y):
        '''
        Constructor
        '''
        self.description = description
        self.x = x
        self.y = y
        

    def __repr__(self):
        return '<PrecipGage: Description=%s, UTM Northing=%s, UTM Easting=%s>' % (self.description, self.x, self.y)
