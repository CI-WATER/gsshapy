'''
********************************************************************************
* Name: SnowSimulation
* Author: Nathan Swain
* Created On: May 16, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

import os, sys
from datetime import datetime

__all__ = ['ElevationNWSRFS',
           'OrthographicGage',
           'OrthoMeasurement']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float, DateTime
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase


class ElevationNWSRFS(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'snw_nwsrfs_elev_snow'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    modelID = Column(Integer, ForeignKey('model_instances.id'))
    
    # Value Columns
    lowerElev = Column(Integer, nullable=False)
    upperElev = Column(Integer, nullable=False)
    mfMin = Column(Float, nullable=False)
    mfMax = Column(Float, nullable=False)
    scf = Column(Float, nullable=False)
    frUse = Column(Float, nullable=False)
    tipm = Column(Float, nullable=False)
    nmf = Column(Float, nullable=False)
    fua = Column(Float, nullable=False)
    plwhc = Column(Float, nullable=False)
    
    # Relationship Properties
    model = relationship('ModelInstance', back_populates='elevationNWSRFS')
    
    def __init__(self, lowerElev, upperElev, mfMin, mfMax, scf, frUse, tipm, nmf, fua, plwhc):
        '''
        Constructor
        '''
        self.lowerElev = lowerElev
        self.upperElev = upperElev
        self.mfMin = mfMin
        self.mfMax = mfMax
        self.scf = scf
        self.frUse = frUse
        self.tipm = tipm
        self.nmf = nmf
        self.fua = fua
        self.plwhc = plwhc
        

    def __repr__(self):
        return '<ElevationNWSRFS: LowerElev=%s, UpperElev=%s, MFMin=%s, MFMax=%s, SCF=%s, FRUse=%s, TIPM=%s, NMF=%s, FUA=%s, PLWHC=%s>' % (
                self.lowerElev,
                self.upperElev,
                self.mfMin,
                self.mfMax,
                self.scf,
                self.frUse,
                self.tipm,
                self.nmf,
                self.fua,
                self.plwhc)
    
    
    

class OrthographicGage(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'snw_orthographic_gages'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)    
    modelID = Column(Integer, ForeignKey('model_instances.id'))
    
    # Value Columns
    numSites = Column(Integer, nullable=False)
    elevBase = Column(Float, nullable=False)
    elev2 = Column(Float, nullable=False)
    
    # Relationship Properties
    orthoMeasurement = relationship('OrthoMeasurement', back_populates='orthographicGage')
    model = relationship('ModelInstance', back_populates='orthographicGage')
    
    def __init__(self, numSites, elevBase, elev2):
        '''
        Constructor
        '''
        self.numSites = numSites
        self.elevBase = elevBase
        self.elev2 = elev2

    def __repr__(self):
        return '<OrthographicGage: NumSites=%s, ElevBase=%s, Elev2=%s>' % (self.numSites, self.elevBase, self.elev2)
    
    
    

class OrthoMeasurement(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'snw_orthographic_measurements'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    oeID = Column(Integer, ForeignKey('snw_orthographic_gages.id'))
    
    # Value Columns
    dateTime = Column(DateTime, nullable=False)
    temp2 = Column(Float, nullable=False)
    
    # Relationship Properties
    orthographicGage = relationship('OrthographicGage', back_populates='orthoMeasurement')
    
    
    def __init__(self, dateTime, temp2):
        '''
        Constructor
        '''
        self.dateTime = dateTime
        self.temp2 = temp2

    def __repr__(self):
        return '<OrthoMeasurement: DateTime=%s, Temp2=%s>' % (self.dateTime, self.temp2)
    
