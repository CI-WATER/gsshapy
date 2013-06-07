'''
********************************************************************************
* Name: Scenario Tables
* Author: Nathan Swain
* Created On: June 4, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['Scenario']

from sqlalchemy import ForeignKey, Column, Table
from sqlalchemy.types import Integer, DateTime, String, Boolean
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase, metadata


class Scenario(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'scenarios'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    modelID = Column(Integer, ForeignKey('model_instances.id'))
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))
    
    # Value Columns
    name = Column(String, nullable=False)
    description = Column(String)
    created = Column(DateTime, nullable=False)
    
    # Relationship Properties
    model = relationship('ModelInstance', back_populates='scenarios')
    projectFile = relationship('ProjectFile', back_populates='scenarios')
    
    def __init__(self, name, description, created):
        '''
        Constructor
        '''
        self.name = name
        self.description = description
        self.created = created
        

    def __repr__(self):
        return '<Scenario: Model Name=%s, Name=%s, Description=%s, Created=%s, Base=%s>' % (
                    self.model.name, 
                    self.name, 
                    self.description, 
                    self.created, 
                    self.base)
        

    
