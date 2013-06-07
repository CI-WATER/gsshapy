'''
********************************************************************************
* Name: Scenario Tables
* Author: Nathan Swain
* Created On: June 4, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['Scenario',
           'scenarioPrecip',
           'scenarioMapTable',
           'scenarioStreamNetwork',
           'scenarioPipeNetwork',
           'scenarioHMET',
           'scenarioTimeSeries',
           'scenarioNWSRFS',
           'scenarioOrthoGage']

from sqlalchemy import ForeignKey, Column, Table
from sqlalchemy.types import Integer, DateTime, String, Boolean
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase, metadata

# Many-to-many association tables between scenario table and other tables
scenarioPrecip = Table('assoc_scenario_precip', metadata,
    Column('scenarioID', Integer, ForeignKey('scenarios.id')),
    Column('precipEventID', Integer, ForeignKey('gag_events.id'))
    )

scenarioMapTable = Table('assoc_scenario_map_table', metadata,
    Column('scenarioID', Integer, ForeignKey('scenarios.id')),
    Column('mapTableID', Integer, ForeignKey('cmt_map_tables.id'))
    )

scenarioStreamNetwork = Table('assoc_scenario_stream_network', metadata,
    Column('scenarioID', Integer, ForeignKey('scenarios.id')),
    Column('streamNetworkID', Integer, ForeignKey('cif_stream_networks.id'))
    )

scenarioPipeNetwork = Table('assoc_scenario_pipe_network', metadata,
    Column('scenarioID', Integer, ForeignKey('scenarios.id')),
    Column('pipeNetworkID', Integer, ForeignKey('spn_pipe_networks.id'))
    )

scenarioHMET = Table('assoc_scenario_HMET', metadata,
    Column('scenarioID', Integer, ForeignKey('scenarios.id')),
    Column('hmetCollectionID', Integer, ForeignKey('hmet_collections.id'))
    )

scenarioTimeSeries = Table('assoc_scenario_time_series', metadata,
    Column('scenarioID', Integer, ForeignKey('scenarios.id')),
    Column('timeSeriesID', Integer, ForeignKey('time_series.id'))
    )

scenarioNWSRFS = Table('assoc_scenario_nwsrfs', metadata,
    Column('scenarioID', Integer, ForeignKey('scenarios.id')),
    Column('nwsrfsID', Integer, ForeignKey('snw_nwsrfs_records.id'))
    )

scenarioOrthoGage = Table('assoc_scenario_orhto_gage', metadata,
    Column('scenarioID', Integer, ForeignKey('scenarios.id')),
    Column('orthoGageID', Integer, ForeignKey('snw_orthographic_gages.id'))
    )

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
    
    precipEvents = relationship('PrecipEvent', secondary=scenarioPrecip, back_populates='scenarios')
    mapTables = relationship('MapTable', secondary=scenarioMapTable, back_populates='scenarios')
    streamNetworks = relationship('StreamNetwork', secondary=scenarioStreamNetwork, back_populates='scenarios')
    pipeNetworks = relationship('PipeNetwork', secondary=scenarioPipeNetwork, back_populates='scenarios')
    hmetCollections = relationship('HMETCollection', secondary=scenarioHMET, back_populates='scenarios')
    timeSeries = relationship('TimeSeries', secondary=scenarioTimeSeries, back_populates='scenarios')
    nwsrfsRecords = relationship('NWSRFSRecord', secondary=scenarioNWSRFS, back_populates='scenarios')
    orthoGages = relationship('OrthographicGage', secondary=scenarioOrthoGage, back_populates='scenarios')
    
    def __init__(self, name, description, created):
        '''
        Constructor
        '''
        self.name = name
        self.description = description
        self.created = created
        

    def __repr__(self):
        return '<Scenario: ModelID=%s, Name=%s, Description=%s, Created=%s, Base=%s>' % (
                    self.modelID, 
                    self.name, 
                    self.description, 
                    self.created, 
                    self.base)
        

    
