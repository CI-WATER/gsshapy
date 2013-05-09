'''
********************************************************************************
* Name: Template
* Author: Nathan Swain
* Created On: Mar 6, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

import os, sys
from datetime import datetime
__all__ = ['list','of','classes']

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime
from sqlalchemy.orm import relation, synonym

from gsshapy import DeclarativeBase, metadata, DBSession

class Example(DeclarativeBase):
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
    




        