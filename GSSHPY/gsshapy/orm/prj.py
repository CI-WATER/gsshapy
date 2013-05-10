'''
********************************************************************************
* Name: ProjectFileModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['ProjectOption','ProjectCard']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, String, Enum
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase

# Controlled Vocabulary List
valueTypeEnum = Enum('STRING','PATH','INTEGER','FLOAT','DATE','BOOLEAN','TIME', name='prj_card_names')


class ProjectOption(DeclarativeBase):
    """
    classdocs
    """
    __tablename__ = 'prj_project_options'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    modelID = Column(Integer, ForeignKey('model_instances.id'), nullable=False)
    cardID = Column(Integer, ForeignKey('prj_cards_cv.id'), nullable=False)
    
    # Value Columns
    value = Column(String, nullable=False)
    
    # Relationship Properties
    model = relationship('ModelInstance', back_populates='projectOptions')
    card = relationship('ProjectCard', back_populates='values')
    
    def __init__(self, value):
        '''
        Constructor
        '''
        self.value = value
        

    def __repr__(self):
        return '<ProjectOption: Value=%s>' % (self.value) 
    
    
class ProjectCard(DeclarativeBase):
    """
    classdocs

    """
    __tablename__ = 'prj_cards_cv'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    name = Column(String, nullable=False)
    valueType = Column(valueTypeEnum, nullable=False)
    
    # Relationship Properties
    values = relationship('ProjectOption', back_populates='card')
    
    def __init__(self, name, valueType):
        '''
        Constructor
        '''
        self.name = name
        self.valueType = valueType
        

    def __repr__(self):
        return '<ProjectCard: Name=%s, ValueType=%s>' % (self.name, self.valueType)
