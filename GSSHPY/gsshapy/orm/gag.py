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
    modelID = Column(Integer, ForeignKey('model_instances.id'), nullable=False)
    
    # Value Columns
    
    # Relationship Properties
    model = relationship('ModelInstance', back_populates='precipFiles')
    projectFile = relationship('ProjectFile', uselist=False, back_populates='precipFile') # One-to-one Relationship
    precipEvents = relationship('PrecipEvent', secondary=assocPrecip, back_populates='precipFiles')
        
    def __repr__(self):
        return '<PrecipitationFile>'
    

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
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.eventDesc,self.nrGag,self.nrPds)
    
    
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
    utmNorthing = Column(Float, nullable=False)
    utmEasting = Column(Float, nullable=False)
    
    # Relationship Properties
    values = relationship('PrecipValue', back_populates='gage')
    
    def __init__(self, description, utmNorthing, utmEasting):
        '''
        Constructor
        '''
        self.description = description
        self.utmNorthing = utmNorthing
        self.utmEasting = utmEasting
        

    def __repr__(self):
        return '<PrecipGage: Description=%s, UTM Northing=%s, UTM Easting=%s>' % (self.description, self.utmNorthing, self.utmEasting)
