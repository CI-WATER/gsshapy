'''
********************************************************************************
* Name: PrecipitationModel
* Author: Nathan Swain
* Created On: Mar 6, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

import os, sys
from datetime import datetime

__all__ = ['PrecipEvent','PrecipValue','PrecipGage']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, DateTime, String, Float
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase


class PrecipEvent(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gag_events'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    modelID = Column(Integer, ForeignKey('model_instances.id'))
    
    # Value Columns
    description = Column(String, nullable=False)
    nrGag = Column(Integer, nullable=False)
    nrPds = Column(Integer, nullable=False)
    
    # Relationship Properties
    model = relationship('ModelInstance', backpopulates='precipEvents')
    values = relationship('PrecipValue', backpopulates='event')
    
    def __init__(self, description, numGages, numPeriods):
        '''
        Constructor
        '''
        #TODO - add validation
        self.description = description
        self.nrGag = numGages
        self.nrPds = numPeriods
        

    def __repr__(self):
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.eventDesc,self.nrGag,self.nrPds);
    
    
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
    event = relationship('PrecipEvent', backpopulates='values')
    gage = relationship('PrecipGage', backpopulates='values')

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
    values = relationship('PrecipValues', backpopulates='gage')
    
    def __init__(self, description, utmNorthing, utmEasting):
        '''
        Constructor
        '''
        self.description = description
        self.utmNorthing = utmNorthing
        self.utmEasting = utmEasting
        

    def __repr__(self):
        return '<PrecipGage: Description=%s, UTM Northing=%s, UTM Easting=%s>' % (self.description, self.utmNorthing, self.utmEasting)
