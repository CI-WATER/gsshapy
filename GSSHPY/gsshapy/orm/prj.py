'''
********************************************************************************
* Name: ProjectFileModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['ProjectFile',
           'ProjectCard']

import re, shlex

from sqlalchemy import ForeignKey, Column, Table
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase, metadata
from gsshapy.orm.gag import PrecipFile
from gsshapy.orm.cmt import MapTableFile
from gsshapy.orm.cif import ChannelInputFile
from gsshapy.orm.spn import StormPipeNetworkFile

from gsshapy.lib import inputFileReaders as ifr, inputFileWriters as ifw



assocProject = Table('assoc_project_files_options', metadata,
    Column('projectFileID', Integer, ForeignKey('prj_project_files.id')),
    Column('projectCardID', Integer, ForeignKey('prj_project_cards.id'))
    )

class ProjectFile(DeclarativeBase):
    '''
    ProjectFile is the file ORM object that interfaces with the project files directly.
    '''
    __tablename__ = 'prj_project_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    precipFileID = Column(Integer, ForeignKey('gag_precipitation_files.id'))
    mapTableFileID = Column(Integer, ForeignKey('cmt_map_table_files.id'))
    channelInputFileID = Column(Integer, ForeignKey('cif_channel_input_files.id'))
    stormPipeNetworkFileID = Column(Integer, ForeignKey('spn_storm_pipe_network_files.id'))
    hmetFileID = Column(Integer, ForeignKey('hmet_files.id'))
    
    # Relationship Properties
    projectCards = relationship('ProjectCard', secondary=assocProject, back_populates='projectFiles')
    mapTableFile = relationship('MapTableFile', back_populates='projectFile')
    channelInputFile = relationship('ChannelInputFile', back_populates='projectFile')
    precipFile = relationship('PrecipFile', back_populates='projectFile')
    stormPipeNetworkFile = relationship('StormPipeNetworkFile', back_populates='projectFile')
    hmetFile = relationship('HmetFile', back_populates='projectFile')
    
    # Global Properties
    PATH = None
    PROJECT_NAME = None
    DIRECTORY = None
    SESSION = None
    EXTENSION = 'prj'
    
    # File Properties
    INPUT_FILES = {'MAPPING_TABLE':             {'filename': None, 'read': ifr.readMappingTableFile, 'write': ifw.writeMappingTableFile},
                   'ST_MAPPING_TABLE':          {'filename': None, 'read': None, 'write': None},
                   'PRECIP_FILE':               {'filename': None, 'read': ifr.readPrecipitationFile, 'write': ifw.writePrecipitationFile},
                   'CHANNEL_INPUT':             {'filename': None, 'read': ifr.readChannelInputFile, 'write': ifw.writeChannelInputFile},
                   'STREAM_CELL':               {'filename': None, 'read': None, 'write': None},
                   'SECTION_TABLE':             {'filename': None, 'read': None, 'write': None},
                   'SOIL_LAYER_INPUT_FILE':     {'filename': None, 'read': None, 'write': None},
                   'IN_THETA_LOCATION':         {'filename': None, 'read': None, 'write': None},
                   'EXPLIC_HOTSTART':           {'filename': None, 'read': None, 'write': None},
                   'READ_CHAN_HOTSTART':        {'filename': None, 'read': None, 'write': None},
                   'CHAN_POINT_INPUT':          {'filename': None, 'read': None, 'write': None},
                   'BOUND_TS':                  {'filename': None, 'read': None, 'write': None},
                   'IN_HYD_LOCATION':           {'filename': None, 'read': None, 'write': None},
                   'IN_SED_LOC':                {'filename': None, 'read': None, 'write': None},
                   'IN_GWFLUX_LOCATION':        {'filename': None, 'read': None, 'write': None},
                   'HMET_SURFAWAYS':            {'filename': None, 'read': None, 'write': None},
                   'HMET_SAMSON':               {'filename': None, 'read': None, 'write': None},
                   'HMET_WES':                  {'filename': None, 'read': ifr.readHmetWesFile, 'write': None},
                   'NWSRFS_ELEV_SNOW':          {'filename': None, 'read': None, 'write': None},
                   'HMET_OROG_GAGES':           {'filename': None, 'read': None, 'write': None},
                   'HMET_ASCII':                {'filename': None, 'read': None, 'write': None},
                   'GW_FLUXBOUNDTABLE':         {'filename': None, 'read': None, 'write': None},
                   'STORM_SEWER':               {'filename': None, 'read': ifr.readPipeNetworkFile, 'write': ifw.writePipeNetworkFile},
                   'GRID_PIPE':                 {'filename': None, 'read': None, 'write': None},
                   'SUPER_LINK_JUNC_LOCATION':  {'filename': None, 'read': None, 'write': None},
                   'SUPERLINK_NODE_LOCATION':   {'filename': None, 'read': None, 'write': None},
                   'OVERLAND_DEPTH_LOCATION':   {'filename': None, 'read': None, 'write': None},
                   'OVERLAND_WSE_LOCATION':     {'filename': None, 'read': None, 'write': None},
                   'OUT_WELL_LOCATION':         {'filename': None, 'read': None, 'write': None},
                   'REPLACE_PARAMS':            {'filename': None, 'read': None, 'write': None},
                   'REPLACE_VALS':              {'filename': None, 'read': None, 'write': None}}
    
    INPUT_MAPS = {'ELEVATION': None,
                  'WATERSHED_MASK': None,
                  'ROUGHNESS': None,
                  'RETEN_DEPTH': None,
                  'READ_OV_HOTSTART': None,
                  'WRITE_OV_HOTSTART': None,
                  'READ_SM_HOTSTART': None,
                  'WRITE_SM_HOSTART': None,
                  'STORAGE_CAPACITY': None,
                  'INTERCEPTION_COEFF': None,
                  'CONDUCTIVITY': None,
                  'CAPILLARY': None,
                  'POROSITY': None,
                  'MOISTURE': None,
                  'PORE_INDEX': None,
                  'RESIDUAL_SAT': None,
                  'FIELD_CAPACITY': None,
                  'SOIL_TYPE_MAP': None,
                  'WATER_TABLE': None,
                  'ALBEDO': None,
                  'WILTING_POINT': None,
                  'TCOEFF': None,
                  'VHEIGHT': None,
                  'CANOPY': None,
                  'INIT_SWE_DEPTH': None,
                  'WATER_TABLE': None,
                  'AQUIFER_BOTTOM': None,
                  'GW_BOUNDFILE': None,
                  'GW_POROSITY_MAP': None,
                  'GW_HYCOND_MAP': None,
                  'CONTAM_MAP': None}
    
    OUTPUT_FILES = {'SUMMARY': {'filename': None, 'read': None},
                    'OUTLET_HYDRO': {'filename': None, 'read': None},
                    'EXPLIC_BACKWATER': {'filename': None, 'read': None},
                    'WRITE_CHAN_HOTSTART': {'filename': None, 'read': None},
                    'OUT_HYD_LOCATION': {'filename': None, 'read': None},
                    'OUT_DEP_LOCATION': {'filename': None, 'read': None},
                    'OUT_SED_LOC': {'filename': None, 'read': None},
                    'OUT_GWFULX_LOCATION': {'filename': None, 'read': None},
                    'OUT_THETA_LOCATION': {'filename': None, 'read': None},
                    'CHAN_DEPTH': {'filename': None, 'read': None},
                    'CHAN_STAGE': {'filename': None, 'read': None},
                    'CHAN_DISCHARGE': {'filename': None, 'read': None},
                    'CHAN_VELOCITY': {'filename': None, 'read': None},
                    'LAKE_OUTPUT': {'filename': None, 'read': None},
                    'SNOW_SWE_FILE': {'filename': None, 'read': None},
                    'GW_WELL_LEVEL': {'filename': None, 'read': None},
                    'OUTLET_SED_FLUX': {'filename': None, 'read': None},
                    'ADJUST_ELEV': {'filename': None, 'read': None},
                    'OUTLET_SED_TSS': {'filename': None, 'read': None},
                    'OUT_TSS_LOC': {'filename': None, 'read': None},
                    'NET_SED_VOLUME': {'filename': None, 'read': None},
                    'VOL_SED_SUSP': {'filename': None, 'read': None},
                    'OUT_CON_LOCATION': {'filename': None, 'read': None},
                    'OUT_MASS_LOCATION': {'filename': None, 'read': None},
                    'SUPERLINK_JUNC_FLOW': {'filename': None, 'read': None},
                    'SUPERLINK_NODE_FLOW': {'filename': None, 'read': None},
                    'OVERLAND_DEPTHS': {'filename': None, 'read': None},
                    'OVERLAND_WSE': {'filename': None, 'read': None},
                    'OPTIMIZE': {'filename': None, 'read': None}}
    
    OUTPUT_MAPS = {'GW_OUTPUT': {'filename': None, 'read': None},
                   'DISCHARGE': {'filename': None, 'read': None},
                   'DEPTH': {'filename': None, 'read': None},
                   'INF_DEPTH': {'filename': None, 'read': None},
                   'SURF_MOIS': {'filename': None, 'read': None},
                   'RATE_OF_INFIL': {'filename': None, 'read': None},
                   'DIS_RAIN': {'filename': None, 'read': None},
                   'CHAN_DEPTH': {'filename': None, 'read': None},
                   'CHAN_DISCHARGE': {'filename': None, 'read': None},
                   'MAX_SED_FLUX': {'filename': None, 'read': None},
                   'GW_OUTPUT': {'filename': None, 'read': None},
                   'GW_RECHARGE_CUM': {'filename': None, 'read': None},
                   'GW_RECHARGE_INC': {'filename': None, 'read': None}}
    
    
    def __init__(self, path, session):
        self.PATH = path
        self.SESSION = session
        
        if '\\' in path:
            splitPath = path.split('\\')
            self.DIRECTORY = '\\'.join(splitPath[:-1]) + '\\'
            
        elif '/' in path:
            splitPath = path.split('/')
            self.DIRECTORY = '/'.join(splitPath[:-1]) + '/'
        else:
            self.DIRECTORY = '""'
            
        self.PROJECT_NAME = splitPath[-1].split('.')[0]
    
    def read(self):
        '''
        Project File Read from File Method
        '''
        HEADERS = ('GSSHAPROJECT', 'WMS')
        
        with open(self.PATH, 'r') as f:
            for line in f:
                card = {}
                try:
                    card = self._extractCard(line)    
                    
                except:
                    card = self._extractDirectoryCard(line)
                # Now that the cardName and cardValue are separated
                # load them into the gsshapy objects
                if card['name'] not in HEADERS:
                    # Initiate database objects
                    prjCard = ProjectCard(name=card['name'], value=card['value'])
                    self.projectCards.append(prjCard)
                    
                # Assemble list of files for reading
                if card['name'] in self.INPUT_FILES:
                    print 'INPUT_FILE:', card['name'], card['value']
                    if '"' in card['value']:
                        self.INPUT_FILES[card['name']]['filename'] = card['value'].strip('"')
                    else:
                        self.INPUT_FILES[card['name']]['filename'] = card['value']
                
                elif card['name'] in self.INPUT_MAPS:
                    print 'INPUT_MAP:', card['name']
                    
                elif card['name'] in self.OUTPUT_FILES:
                    print 'OUTPUT_FILE:', card['name']
                
                elif card['name'] in self.OUTPUT_MAPS:
                    print 'OUTPUT_MAPS:', card['name']
        
        self.SESSION.add(self)
                     
    def readAll(self):
        '''
        GSSHA Project Read from File Method
        '''
        
        # First read self
        self.read()
        
        # Read Input Files
        self.readInput()
        
        
    def readInput(self):
        '''
        GSSHAPY Project Read All Input Files Method
        '''
        
        # Read ProjectFile
        self.read()
        
        # Read Input Files
        for card, afile in self.INPUT_FILES.iteritems():
            filename = afile['filename']
            read = afile['read']
            if filename != None and read != None:
                read(self, filename)
        
    
    def write(self, session, directory, filename):
        '''
        Project File Write to File Method
        '''
        # Initiate project file
        fullPath = '%s%s' % (directory, filename)
        
        with open(fullPath, 'w') as prjFile:
            prjFile.write('GSSHAPROJECT\n')
        
            # Initiate write on each ProjectCard that belongs to this ProjectFile
            for card in self.projectCards:
                prjFile.write(card.write())
                
                # Assemble list of files for writing
                if card.name in self.INPUT_FILES:
                    print 'INPUT_FILE:', card.name, card.value
                    if '"' in card.value:
                        self.INPUT_FILES[card.name]['filename'] = card.value.strip('"')
                    else:
                        self.INPUT_FILES[card.name]['filename'] = card.value
                
                elif card.name in self.INPUT_MAPS:
                    pass
                    
                elif card.name in self.OUTPUT_FILES:
                    pass
                
                elif card.name in self.OUTPUT_MAPS:
                    pass
                
    def writeAll(self, session, directory, filename):
        '''
        GSSHA Project Write All Files to File Method
        '''
        ## TODO: FIND A WAY TO MAKE CHANGE PROJECT NAME DURING WRITING
        ## TODO: ALSO FIND A WAY TO NOT DOBULE UP ON self.read or self.write statements
        ## For readAll and writeAll methods
        
        # Write Project File
        self.write(session=session, directory=directory, filename=filename)
        
        # Write input files
        self.writeInput(session=session, directory=directory)
        
        
    def writeInput(self, session, directory):
        '''
        GSSHA Project Write Input Files to File Method
        '''
        
        # Write Input Files
        for card, afile in self.INPUT_FILES.iteritems():
            filename = afile['filename']
            write = afile['write']
            if filename != None and write != None:
                write(projectFile=self, filename=filename, directory=directory, session=session)
        
        print 'Hello Write Input'
        
        
    def _extractCard(self, projectLine):
        splitLine = shlex.split(projectLine)
        cardName = splitLine[0]
        # pathSplit will fail on boolean cards (no value
        # = no second parameter in list (currLine[1])
        try:
            # Split the path by / or \\ and retrieve last
            # item to store relative paths as Card Value
            pathSplit = re.split('/|\\\\', splitLine[1])
            
            # Wrap paths in double quotes
            try:
                # If the value is able to be converted to a
                # float (any number) then store value only
                float(pathSplit[-1])
                cardValue = pathSplit[-1]
            except:
                # A string will through an exception with
                # an atempt to convert to float. In this 
                # case wrap the string in double quotes.
                if '.' in pathSplit[-1]:
                    # If the string contains a '.' it is a
                    # path: wrap in double quotes
                    cardValue = '"%s"' % pathSplit[-1]
                elif pathSplit[-1] == '':
                    # For directory cards with unix paths 
                    # use double quotes
                    cardValue = '""'
                else:
                    # Else it is a card name/option
                    # don't wrap in quotes
                    cardValue = pathSplit[-1]
        
        # For boolean cards store the empty string
        except:
            cardValue = None
            
        return {'name': cardName, 'value': cardValue}
    
    def _extractDirectoryCard(self, projectLine):
        PROJECT_PATH = ['PROJECT_PATH']
        
        # Handle special case with directory cards in
        # windows. shlex.split fails because windows 
        # directory cards end with an escape character.
        # e.g.: "this\path\ends\with\escape\"
        currLine = projectLine.strip().split()
        
        # Extract Card Name from the first item in the list
        cardName = currLine[0]
        
        if cardName in PROJECT_PATH:
            cardValue = '""'
        else:
            # TODO: Write code to handle nested directory cards
            cardValue = '""'
        
        return {'name': cardName, 'value': cardValue}
    
class ProjectCard(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'prj_project_cards'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    name = Column(String, nullable=False)
    value = Column(String)
    
    # Relationship Properties
    projectFiles = relationship('ProjectFile', secondary=assocProject, back_populates='projectCards')
    
    def __init__(self, name, value):
        '''
        Constructor
        '''
        self.name = name
        self.value = value
        

    def __repr__(self):
        return '<ProjectCard: Name=%s, Value=%s>' % (self.name, self.value)
    
    def write(self):
        # Determine number of spaces between card and value for nice alignment
        numSpaces = 25 - len(self.name)
        
        # Handle special case of booleans
        if self.value is None:
            line = '%s\n' % (self.name)
        else:
            line ='%s%s%s\n' % (self.name,' '*numSpaces, self.value)
        return line
