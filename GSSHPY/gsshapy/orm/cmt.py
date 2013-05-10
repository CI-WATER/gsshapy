'''
********************************************************************************
* Name: MappingTablesModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['MapTable','MTValue', 'MTIndex','Contaminant','Sediment']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Enum, Float, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase

# Controlled Vocabulary Lists
mapTableNameEnum = Enum('ROUGHNESS','INTERCEPTION','RETENTION','GREEN_AMPT_INFILTRATION',\
                       'GREEN_AMPT_INITIAL_SOIL_MOISTURE','RICHARDS_EQN_INFILTRATION_BROOKS',\
                       'RICHARDS_EQN_INFILTRATION_HAVERCAMP','EVAPOTRANSPIRATION','WELL_TABLE',\
                       'OVERLAND_BOUNDARY','TIME_SERIES_INDEX','GROUNDWATER','GROUNDWATER_BOUNDARY',\
                       'AREA_REDUCTION','WETLAND_PROPERTIES','MULTI_LAYER_SOIL','SOIL_EROSION_PROPS',\
                       'CONTAMINANT_TRANSPORT','SEDIMENT',\
                       name='cmt_table_names')

varNameEnum = Enum('ROUGH','STOR_CAPY','INTER_COEF','RETENTION_DEPTH','HYDR_COND','CAPIL_HEAD',\
                      'POROSITY','PORE_INDEX','RESID_SAT','FIELD_CAPACITY','WILTING_PT','SOIL_MOISTURE',\
                      'IMPERVIOUS_AREA','HYD_COND','SOIL_MOIST','DEPTH','LAMBDA',\
                      'BUB_PRESS','DELTA_Z','ALPHA','BETA','AHAV','ALBEDO','VEG_HEIGHT','V_RAD_COEFF',\
                      'CANOPY_RESIST','SPLASH_COEFF','DETACH_EXP','DETACH_CRIT','SED_COEF','XSEDIMENTS',\
                      'TC_COEFF','TC_INDEX','TC_CRIT','SPLASH_K','DETACH_ERODE','DETACH_INDEX',\
                      'SED_K','DISPERSION','DECAY','UPTAKE','LOADING','GW_CONC','INIT_CONC',\
                      'SW_PART','SOLUBILITY',\
                      name='cmt_variable_names')


class MapTable(DeclarativeBase):
    """
    classdocs

    """
    __tablename__ = 'cmt_map_tables'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    modelID = Column(Integer, ForeignKey('model_instances.id'), nullable=False)
    idxMapID = Column(Integer, ForeignKey('idx_index_maps.id'), nullable=False)
    
    # Value Columns
    name = Column(mapTableNameEnum, nullable=False)
    numIDs = Column(Integer)
    maxNumCells = Column(Integer)
    numSed = Column(Integer)
    numContam = Column(Integer)
    
    # Relationship Properties
    model = relationship('ModelInstance', back_populates='mapTable')
    indexMap = relationship('IndexMap', back_populates='mapTables')
    values = relationship('MTValue', back_populates='mapTable', cascade='all, delete, delete-orphan')
    sediment = relationship('Sediment', back_populates='mapTable', cascade='all, delete, delete-orphan')
    
    def __init__(self, name, numIDs=None, maxNumCells=None, numSed=None, numContam=None):
        '''
        Constructor
        '''
        self.name = name
        self.numIDs = numIDs
        self.maxNumCells = maxNumCells
        self.numSed = numSed
        self.numContam = numContam

    def __repr__(self):
        return '<MapTable: Name=%s, Index Map=%s, NumIDs=%s>' % (self.name, self.idxMapID, self.numIDs)
    
class MTIndex(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cmt_indexes'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    idxMapID = Column(Integer, ForeignKey('idx_index_maps.id'), nullable=False)
    
    # Value Columns
    index = Column(Integer, nullable=False)
    description1 = Column(String(40))
    description2 = Column(String(40))
    
    # Relationship Properties
    values = relationship('MTValue', back_populates='index')
    indexMap = relationship('IndexMap', back_populates='indices')
    
    
    def __init__(self, index, description1='', description2=''):
        '''
        Constructor
        '''
        self.index = index
        self.description1 = description1
        self.description2 = description2

    def __repr__(self):
        return '<MTIndex: Index=%s, Description1=%s, Description2=%s>' % (self.index, self.description1, self.description2)

class MTValue(DeclarativeBase):
    """
    classdocs

    """
    __tablename__ = 'cmt_map_table_values'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    mapTableID = Column(Integer, ForeignKey('cmt_map_tables.id'), nullable=False)
    mapTableIndexID = Column(Integer, ForeignKey('cmt_indexes.id'), nullable=False)
    contaminantID = Column(Integer, ForeignKey('cmt_contaminants.id'))
    
    # Value Columns
    variable = Column(varNameEnum, nullable=False)
    value = Column(Float, nullable=False)
    
    # Relationship Properties
    mapTable = relationship('MapTable', back_populates='values')
    contaminant = relationship('Contaminant', back_populates='value')
    index = relationship('MTIndex', back_populates='values')
    
    def __init__(self, variable, value=None):
        '''
        Constructor
        '''
        self.variable = variable
        self.value = value
        
    def __repr__(self):
        return '<MTValue: %s=%s>' % (self.variable, self.value)



class Contaminant(DeclarativeBase):
    """
    classdocs

    """
    __tablename__ = 'cmt_contaminants'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    name = Column(String, nullable=False)
    outFile = Column(String, nullable = False)
    precipConc = Column(Float, nullable=False)
    partition = Column(Float, nullable=False)

    # Relationship Properties
    value = relationship('MTValue', back_populates='contaminant')
    
    def __init__(self, name, outFile, precipConc, partition):
        '''
        Constructor
        '''
        self.name = name
        self.outFile = outFile
        self.precipConc = precipConc
        self.partition = partition
        
    def __repr__(self):
        return '<Contaminant: Name=%s, Precipitation Concentration=%s, Partition=%s, OutputFile=%s>' % (self.name, self.precipConc, self.partition, self.outFile)


    
class Sediment(DeclarativeBase):
    """
    classdocs

    """
    __tablename__ = 'cmt_sediments'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    mapTableID = Column(Integer, ForeignKey('cmt_map_tables.id'), nullable=False)
    
    # Value Columns
    description = Column(String, nullable=False)
    specificGravity = Column(Float, nullable=False)
    particleDiameter = Column(Float,nullable=False)
    outFile = Column(String, nullable=False)
    
    # Relationship Properties
    mapTable = relationship('MapTable', back_populates='sediment')
    
    def __init__(self, description, specificGravity, particleDiameter, outputFileName):
        '''
        Constructor
        '''
        self.description = description
        self.specificGravity = specificGravity
        self.particleDiameter = particleDiameter
        self.outFile = outputFileName
    
    def __repr__(self):
        return '<Sediment: Name=%s>' % (self.description, self.specificGravity, self.particleDiameter, self.outFile)