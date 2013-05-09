'''
********************************************************************************
* Name: IndexMapModel
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

from model.gsshapy import DeclarativeBase

class TimeSeries(DeclarativeBase):
    """
    classdocs

    """
    __tablename__ = 'time_series'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    modelID = Column(Integer, ForeignKey('model_instances.id'), nullable=False)
    
    # Value Columns
    name = Column(String, nullable=False)
    fileExtension = Column(String, nullable=False)
    numValues = Column(Integer)
    
    # Relationship Properties
    model = relationship('ModelInstance', back_populates='timeseries')
    values = relationship('TimeSeriesValue', back_populates='timeseries')
    
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
    """
    classdocs

    """
    __tablename__ = 'time_series_values'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    timeSeriesID = Column(Integer, ForeignKey('time_series.id'), nullable=False)
    
    # Value Columns
    simTime = Column(Float, nullable=False)
    value = Column(Float, nullable=False)
    
    # Relationship Properties
    timeseries = relationship('TimeSeries', back_populates='values')
    
    def __init__(self, simTime, value):
        '''
        Constructor
        '''
        self.simTime = simTime
        self.value = value
        
    def __repr__(self):
        return '<TimeSeriesValue: Name=%s, Time=%s, Value=%s>' % (self.name, self.simTime, self.value)