'''
********************************************************************************
* Name: TimeSeriesModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['TimeSeries', 'TimeSeriesValue']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase

class TimeSeries(DeclarativeBase):
    '''
    classdocs

    '''
    __tablename__ = 'time_series'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    modelID = Column(Integer, ForeignKey('model_instances.id'), nullable=False)
    
    # Value Columns
    name = Column(String, nullable=False)
    fileExtension = Column(String, nullable=False)
    numValues = Column(Integer)
    # valueUnits = Column(String)
    
    # Relationship Properties
    model = relationship('ModelInstance', back_populates='timeSeries')
    values = relationship('TimeSeriesValue', back_populates='timeSeries', cascade='all, delete, delete-orphan')
    
    def __init__(self, name, fileExtension, numValues):
        '''
        Constructor
        '''
        self.name = name
        self.fileExtension = fileExtension
        self.numValues = numValues
        
    def __repr__(self):
        return '<TimeSeries: Name=%s, Extension=%s, NumValues=%s>' % (self.name, self.fileExtension, self.numValues)


class TimeSeriesValue(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'time_series_values'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    timeSeriesID = Column(Integer, ForeignKey('time_series.id'), nullable=False)
    
    # Value Columns
    simTime = Column(Float, nullable=False)
    value = Column(Float, nullable=False)
    
    # Relationship Properties
    timeSeries = relationship('TimeSeries', back_populates='values')
    
    def __init__(self, simTime, value):
        '''
        Constructor
        '''
        self.simTime = simTime
        self.value = value
        
    def __repr__(self):
        return '<TimeSeriesValue: Time=%s, Value=%s>' % (self.simTime, self.value)