'''
********************************************************************************
* Name: Hydro-MeteorologicalSupport
* Author: Nathan Swain
* Created On: May 14, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

import os, sys
from datetime import datetime

__all__ = ['HMET']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float, DateTime
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase


class HMET(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'hmet'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    modelID = Column(Integer, ForeignKey('model_instances.id'))
    
    # Value Columns
    hmetDateTime = Column(DateTime, nullable=False)
    barometricPress = Column(Float, nullable=False)
    relHumidity = Column(Float, nullable=False)
    totalSkyCover = Column(Float, nullable=False)
    windSpeed = Column(Float, nullable=False)
    dryBulbTemp = Column(Float, nullable=False)
    directRad = Column(Float, nullable=False)
    globalRad = Column(Float, nullable=False)
    
    # Relationship Properties
    model = relationship('ModelInstance', back_populates='hmet')
    
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
        return '<HMET: DateTime=%s, BarometricPressure=%s, RelHumidity=%s, TotalSkyCover=%s, WindSpeed=%s, DryBulbTemp=%s, DirectRad=%s, GlobalRad=%s>' % (
                self.hmetDateTime,
                self.barometricPress,
                self.relHumidity,
                self.totalSkyCover,
                self.windSpeed,
                self.dryBulbTemp,
                self.directRad,
                self.globalRad)
