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
__all__ = ['Event','Value','Gage']

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime, String
from sqlalchemy.orm import relation, synonym, relationship, backref

from gsshapy.orm import DeclarativeBase


class Event(DeclarativeBase):
    """
    classdocs

    """
    __tablename__ = 'gag_events'

    id = Column(Integer, autoincrement=True, primary_key=True)
    created = Column(DateTime, default=datetime.now)
    modelID = Column(Integer, ForeignKey('models.id')); #TODO - foreign key
    eventDesc = Column(String, unique=True, nullable=False) #TODO - is unique needed?
    #numGages
    nrGag = Column(Integer);
    #numPeriods
    nrPds = Column(Integer); 
    
    
    
    Relation = relation('OtherClass', backref='otherColumn', cascade='all, delete, delete-orphan')
    
    def __init__(self, eventDesc, numGages, numPeriods):
        '''
        Constructor
        '''
        #TODO - add validation
        self.eventDesc = eventDesc
        self.nrGag = numGages
        self.nrPds = numPeriods
        

    def __repr__(self):
        return '<Event: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.eventDesc,self.nrGag,self.nrPds);
    
    
class Value(DeclarativeBase):
    """
    classdocs

    """
    __tablename__ = 'example'

    __id = Column(Integer, autoincrement=True, primary_key=True)
    __name = Column(String, unique=True, nullable=False)
    __created = Column(DateTime, default=datetime.now)
    
    exRelation = relation('OtherClass', backref='otherColumn', cascade='all, delete, delete-orphan')
    
    def __init__(self, name):
        '''
        Constructor
        '''
        self.__name = name
        

    def __repr__(self):
        return '<Example: Name=%s>' % self.exName
    

    
class Gage(DeclarativeBase):
    """
    classdocs

    """
    __tablename__ = 'example'

    __id = Column(Integer, autoincrement=True, primary_key=True)
    __name = Column(Unicode(16), unique=True, nullable=False)
    __created = Column(DateTime, default=datetime.now)
    
    exRelation = relation('OtherClass', backref='otherColumn', cascade='all, delete, delete-orphan')
    
    def __init__(self, name):
        '''
        Constructor
        '''
        self.__name = name
        

    def __repr__(self):
        return '<Example: Name=%s>' % self.exName
