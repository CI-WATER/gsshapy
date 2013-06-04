'''
********************************************************************************
* Name: ModelInstanceModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['ModelInstance']

from sqlalchemy import Column
from sqlalchemy.types import Integer, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase


class ModelInstance(DeclarativeBase):
    """
    classdocs

    """
    __tablename__ = 'model_instances'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    name = Column(String, nullable=False)
    location = Column(String)
    beginDate = Column(DateTime)
    endDate = Column(DateTime)
    
    # Relationship Properties
    scenarios = relationship('Scenario', back_populates='model')
    projectOptions = relationship('ProjectOptions', back_populates='model')
    precipEvents = relationship('PrecipEvent', back_populates='model')
    mapTables = relationship('MapTable', back_populates='model')
    indexMaps = relationship('IndexMap', back_populates='model')
    streamNetwork = relationship('StreamNetwork', back_populates='model')
    pipeNetwork = relationship('PipeNetwork', back_populates='model')
    hmetCollections = relationship('HMETCollection', back_populates='model')
    timeSeries = relationship('TimeSeries', back_populates='model')
    nwsrfsRecords = relationship('NWSRFSRecord', back_populates='model')
    orthoGages = relationship('OrhtographicGage', back_populates='model')
    
    
    
    def __init__(self, name, location='', beginDate=None, endDate=None):
        '''
        Constructor
        '''
        self.name = name
        self.location = location
        self.beginDate = beginDate
        self.endDate = endDate
        

    def __repr__(self):
        return '<ModelInstance: Name=%s, Location=%s, StartDate=%s, EndDate=%s>' % (self.name, self.location, self.beginDate, self.endDate)
