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

from gsshapy.lib import io_readers as ior, io_writers as iow



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
    nwsrfsFileID = Column(Integer, ForeignKey('snw_nwsrfs_files.id'))
    orthoGageFileID = Column(Integer, ForeignKey('snw_orthographic_gage_files.id'))
    gridPipeFileID = Column(Integer, ForeignKey('gpi_grid_pipe_files.id'))
    gridStreamFileID = Column(Integer, ForeignKey('gst_grid_stream_files.id'))
    
    # Value Columns
    name = Column(String, nullable=False)
    
    # Relationship Properties
    projectCards = relationship('ProjectCard', secondary=assocProject, back_populates='projectFiles')
    
    # File Relationship Properties
    mapTableFile = relationship('MapTableFile', back_populates='projectFile')
    channelInputFile = relationship('ChannelInputFile', back_populates='projectFile')
    precipFile = relationship('PrecipFile', back_populates='projectFile')
    stormPipeNetworkFile = relationship('StormPipeNetworkFile', back_populates='projectFile')
    hmetFile = relationship('HmetFile', back_populates='projectFile')
    nwsrfsFile = relationship('NwsrfsFile', back_populates='projectFile')
    orthoGageFile = relationship('OrthographicGageFile', back_populates='projectFile')
    gridPipeFile = relationship('GridPipeFile', back_populates='projectFile')
    gridStreamFile = relationship('GridStreamFile', back_populates='projectFile')
    timeSeriesFiles = relationship('TimeSeriesFile', back_populates='projectFile')
    outputLocationFiles = relationship('OutputLocationFile', back_populates='projectFile')
    
    # Global Properties
    PATH = None
    PROJECT_NAME = None
    DIRECTORY = None
    SESSION = None
    EXTENSION = 'prj'
    
    # File Properties
    INPUT_FILES = {'MAPPING_TABLE':             {'filename': None, 'read': ior.readMappingTableFile, 'write': iow.writeMappingTableFile},
                   'ST_MAPPING_TABLE':          {'filename': None, 'read': None, 'write': None},
                   'PRECIP_FILE':               {'filename': None, 'read': ior.readPrecipitationFile, 'write': iow.writePrecipitationFile},
                   'CHANNEL_INPUT':             {'filename': None, 'read': ior.readChannelInputFile, 'write': iow.writeChannelInputFile},
                   'STREAM_CELL':               {'filename': None, 'read': ior.readGridStreamFile, 'write': iow.writeGridStreamFile},
                   'SECTION_TABLE':             {'filename': None, 'read': None, 'write': None},
                   'SOIL_LAYER_INPUT_FILE':     {'filename': None, 'read': None, 'write': None},
                   'IN_THETA_LOCATION':         {'filename': None, 'read': None, 'write': None},
                   'EXPLIC_HOTSTART':           {'filename': None, 'read': None, 'write': None},
                   'READ_CHAN_HOTSTART':        {'filename': None, 'read': None, 'write': None},
                   'CHAN_POINT_INPUT':          {'filename': None, 'read': None, 'write': None},
                   'BOUND_TS':                  {'filename': None, 'read': None, 'write': None},
                   'IN_HYD_LOCATION':           {'filename': None, 'read': ior.readOutputLocationFile, 'write': iow.writeOutputLocationFile},
                   'IN_SED_LOC':                {'filename': None, 'read': None, 'write': None},
                   'IN_GWFLUX_LOCATION':        {'filename': None, 'read': None, 'write': None},
                   'HMET_SURFAWAYS':            {'filename': None, 'read': None, 'write': None},
                   'HMET_SAMSON':               {'filename': None, 'read': None, 'write': None},
                   'HMET_WES':                  {'filename': None, 'read': ior.readHmetWesFile, 'write': iow.writeHmetFile},
                   'NWSRFS_ELEV_SNOW':          {'filename': None, 'read': ior.readNwsrfsFile, 'write': iow.writeNwsrfsFile},
                   'HMET_OROG_GAGES':           {'filename': None, 'read': ior.readOrthoGageFile, 'write': iow.writeOrthoGageFile},
                   'HMET_ASCII':                {'filename': None, 'read': None, 'write': None},
                   'GW_FLUXBOUNDTABLE':         {'filename': None, 'read': None, 'write': None},
                   'STORM_SEWER':               {'filename': None, 'read': ior.readPipeNetworkFile, 'write': iow.writePipeNetworkFile},
                   'GRID_PIPE':                 {'filename': None, 'read': ior.readGridPipeFile, 'write': iow.writeGridPipeFile},
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
    
    OUTPUT_FILES = {'SUMMARY':              {'filename': None, 'read': None, 'write': None},
                    'OUTLET_HYDRO':         {'filename': None, 'read': ior.readTimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'EXPLIC_BACKWATER':     {'filename': None, 'read': None, 'write': None},
                    'WRITE_CHAN_HOTSTART':  {'filename': None, 'read': None, 'write': None},
                    'OUT_HYD_LOCATION':     {'filename': None, 'read': ior.readTimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'OUT_DEP_LOCATION':     {'filename': None, 'read': None, 'write': None},
                    'OUT_SED_LOC':          {'filename': None, 'read': None, 'write': None},
                    'OUT_GWFULX_LOCATION':  {'filename': None, 'read': None, 'write': None},
                    'OUT_THETA_LOCATION':   {'filename': None, 'read': None, 'write': None},
                    'CHAN_DEPTH':           {'filename': None, 'read': None, 'write': None},
                    'CHAN_STAGE':           {'filename': None, 'read': None, 'write': None},
                    'CHAN_DISCHARGE':       {'filename': None, 'read': None, 'write': None},
                    'CHAN_VELOCITY':        {'filename': None, 'read': None, 'write': None},
                    'LAKE_OUTPUT':          {'filename': None, 'read': None, 'write': None},
                    'SNOW_SWE_FILE':        {'filename': None, 'read': None, 'write': None},
                    'GW_WELL_LEVEL':        {'filename': None, 'read': None, 'write': None},
                    'OUTLET_SED_FLUX':      {'filename': None, 'read': None, 'write': None},
                    'ADJUST_ELEV':          {'filename': None, 'read': None, 'write': None},
                    'OUTLET_SED_TSS':       {'filename': None, 'read': ior.readTimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'OUT_TSS_LOC':          {'filename': None, 'read': None, 'write': None},
                    'NET_SED_VOLUME':       {'filename': None, 'read': None, 'write': None},
                    'VOL_SED_SUSP':         {'filename': None, 'read': None, 'write': None},
                    'OUT_CON_LOCATION':     {'filename': None, 'read': ior.readTimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'OUT_MASS_LOCATION':    {'filename': None, 'read': ior.readTimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'SUPERLINK_JUNC_FLOW':  {'filename': None, 'read': None, 'write': None},
                    'SUPERLINK_NODE_FLOW':  {'filename': None, 'read': None, 'write': None},
                    'OVERLAND_DEPTHS':      {'filename': None, 'read': None, 'write': None},
                    'OVERLAND_WSE':         {'filename': None, 'read': None, 'write': None},
                    'OPTIMIZE':             {'filename': None, 'read': None, 'write': None}}
    
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
        self.name = self.PROJECT_NAME.strip('"')
    
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
                    print 'INPUT_FILE:', card['name'], card['value'].strip('"')
                    self.INPUT_FILES[card['name']]['filename'] = card['value'].strip('"')
                
                elif card['name'] in self.INPUT_MAPS:
                    print 'INPUT_MAP:', card['name'], card['value'].strip('"')
                    
                elif card['name'] in self.OUTPUT_FILES:
                    print 'OUTPUT_FILE:', card['name'], card['value'].strip('"')
                    self.OUTPUT_FILES[card['name']]['filename'] = card['value'].strip('"')
                
                elif card['name'] in self.OUTPUT_MAPS:
                    print 'OUTPUT_MAPS:', card['name'], card['value'].strip('"')
        
        self.SESSION.add(self)
                     
    def readAll(self):
        '''
        GSSHA Project Read from File Method
        '''
        
        # First read self
        self.read()
        
        # Read Input Files
        self._readInput()
        
        # Read Output Files
        self._readOutput()
        
        
    def _readInput(self):
        '''
        GSSHAPY Project Read All Input Files Method
        '''
        ## NOTE: This function is depenedent on the project file being read first
        # Read Input Files
        for card, afile in self.INPUT_FILES.iteritems():
            filename = afile['filename']
            read = afile['read']
            if filename != None and read != None:
                read(self, filename)
                
    def _readOutput(self):
        '''
        GSSHAPY Project Read All Output Files Method
        '''
        ## NOTE: This function is depenedent on the project file being read first
        # Read Input Files
        for card, afile in self.OUTPUT_FILES.iteritems():
            filename = afile['filename']
            read = afile['read']
            if filename != None and read != None:
                read(self, filename)
    
    def write(self, session, directory, newName=None):
        '''
        Project File Write to File Method
        '''
        # Change name of project
        if newName != None:
            self.PROJECT_NAME = newName
        else:
            self.PROJECT_NAME = self.name
        
        # Initiate project file
        fullPath = '%s%s.%s' % (directory, self.PROJECT_NAME, self.EXTENSION)
        
        with open(fullPath, 'w') as prjFile:
            prjFile.write('GSSHAPROJECT\n')
        
            # Initiate write on each ProjectCard that belongs to this ProjectFile
            for card in self.projectCards:
                prjFile.write(card.write(originalPrefix = self.name, newPrefix=self.PROJECT_NAME))
                
                # Assemble list of files for writing
                if card.name in self.INPUT_FILES:
                    value = card.value.strip('"')
                    self.INPUT_FILES[card.name]['filename'] = value
                    
                elif card.name in self.INPUT_MAPS:
                    pass
                    
                elif card.name in self.OUTPUT_FILES:
                    value = card.value.strip('"')
                    self.OUTPUT_FILES[card.name]['filename'] = value
                
                elif card.name in self.OUTPUT_MAPS:
                    pass
                
    def writeAll(self, session, directory, newName=None):
        '''
        GSSHA Project Write All Files to File Method
        '''
        
        # Write Project File
        self.write(session=session, directory=directory, newName=newName)
        
        # Write input files
        self._writeXput(session=session, directory=directory, fileDict=self.INPUT_FILES, newName=newName)
        
        # Write output files
        self._writeXput(session=session, directory=directory, fileDict=self.OUTPUT_FILES, newName=newName)
        
        
    def _writeXput(self, session, directory, fileDict, newName=None):
        '''
        GSSHA Project Write Input Files to File Method
        '''
        # Write Input/Output Files
        for card, afile in fileDict.iteritems():
            if afile['filename'] != None:
                originalProjectName = self.name
                originalFilename = afile['filename']
                originalPrefix = originalFilename.split('.')[0]
                extension = originalFilename.split('.')[1]
                
                # Handle new name
                if newName == None:
                    # The project name is not changed and file names
                    # stay the same
                    filename = originalFilename
                    
                elif originalPrefix == originalProjectName:
                    # This check is necessary because not all filenames are 
                    # prefixed with the project name. Thus the file prefix
                    # is only changed for files that are prefixed with the 
                    # project name
                    filename = '%s.%s' % (newName, extension)
                
                else:
                    # Filename doesn't change for files that don't share the 
                    # project prefix. e.g.: hmet.hmt
                    filename = originalFilename
                
                # Extract write funtion from fileDict
                write = afile['write']
                
                # Execute write function if not None
                if write != None:
                    write(projectFile=self, directory=directory, session=session, filename=filename)
        
        
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
    
    def write(self, originalPrefix, newPrefix):
        # Determine number of spaces between card and value for nice alignment
        numSpaces = 25 - len(self.name)
        
        # Handle special case of booleans
        if self.value is None:
            line = '%s\n' % (self.name)
        else:
            if originalPrefix in self.value and newPrefix != originalPrefix:
                line ='%s%s%s\n' % (self.name,' '*numSpaces, self.value.replace(originalPrefix, newPrefix))
            else:
                line ='%s%s%s\n' % (self.name,' '*numSpaces, self.value)
        return line
