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

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase
from gsshapy.orm.file_object_imports import *
from gsshapy.lib import io_writers as iow

class ProjectFile(DeclarativeBase, GsshaPyFileObjectBase):
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
    projectionFileID = Column(Integer, ForeignKey('pro_projection_files.id'))
    replaceParamFileID = Column(Integer, ForeignKey('rep_replace_param_files.id'))
    replaceValFileID = Column(Integer, ForeignKey('rep_replace_val_files.id'))
    
    # Value Columns
    name = Column(String, nullable=False)
    
    # Relationship Properties
    projectCards = relationship('ProjectCard', back_populates='projectFile')
    
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
    projectionFile = relationship('ProjectionFile', back_populates='projectFile')
    replaceParamFile = relationship('ReplaceParamFile', back_populates='projectFile')
    replaceValFile = relationship('ReplaceValFile', back_populates='projectFile')
    outputLocationFiles = relationship('OutputLocationFile', back_populates='projectFile')
    maps = relationship('RasterMapFile', back_populates='projectFile')
    
    # File Properties
    INPUT_FILES = {'#PROJECTION_FILE':          {'filename': None, 'fileio': ProjectionFile, 'write': iow.writeProjectionFile},         # WMS
                   'MAPPING_TABLE':             {'filename': None, 'fileio': MapTableFile, 'write': iow.writeMappingTableFile},         # Mapping Table
                   'ST_MAPPING_TABLE':          {'filename': None, 'fileio': None, 'write': None},
                   'PRECIP_FILE':               {'filename': None, 'fileio': PrecipFile, 'write': iow.writePrecipitationFile},          # Precipitation
                   'CHANNEL_INPUT':             {'filename': None, 'fileio': ChannelInputFile, 'write': iow.writeChannelInputFile},     # Channel Routing
                   'STREAM_CELL':               {'filename': None, 'fileio': GridStreamFile, 'write': iow.writeGridStreamFile},
                   'SECTION_TABLE':             {'filename': None, 'fileio': None, 'write': None},
                   'SOIL_LAYER_INPUT_FILE':     {'filename': None, 'fileio': None, 'write': None},                                      # Infiltration
                   'IN_THETA_LOCATION':         {'filename': None, 'fileio': OutputLocationFile, 'write': iow.writeOutputLocationFile},
                   'EXPLIC_HOTSTART':           {'filename': None, 'fileio': None, 'write': None},
                   'READ_CHAN_HOTSTART':        {'filename': None, 'fileio': None, 'write': None},
                   'CHAN_POINT_INPUT':          {'filename': None, 'fileio': None, 'write': None},
                   'IN_HYD_LOCATION':           {'filename': None, 'fileio': OutputLocationFile, 'write': iow.writeOutputLocationFile},
                   'IN_SED_LOC':                {'filename': None, 'fileio': OutputLocationFile, 'write': iow.writeOutputLocationFile},
                   'IN_GWFLUX_LOCATION':        {'filename': None, 'fileio': OutputLocationFile, 'write': iow.writeOutputLocationFile},
                   'HMET_SURFAWAYS':            {'filename': None, 'fileio': None, 'write': None},                                      # Continuous Simulation
                   'HMET_SAMSON':               {'filename': None, 'fileio': None, 'write': None},
                   'HMET_WES':                  {'filename': None, 'fileio': HmetFile, 'write': iow.writeHmetFile},
                   'NWSRFS_ELEV_SNOW':          {'filename': None, 'fileio': NwsrfsFile, 'write': iow.writeNwsrfsFile},
                   'HMET_OROG_GAGES':           {'filename': None, 'fileio': OrthographicGageFile, 'write': iow.writeOrthoGageFile},
                   'HMET_ASCII':                {'filename': None, 'fileio': None, 'write': None},
                   'GW_FLUXBOUNDTABLE':         {'filename': None, 'fileio': None, 'write': None},                                      # Saturated Groundwater Flow
                   'STORM_SEWER':               {'filename': None, 'fileio': StormPipeNetworkFile, 'write': iow.writePipeNetworkFile},  # Subsurface Drainage
                   'GRID_PIPE':                 {'filename': None, 'fileio': GridPipeFile, 'write': iow.writeGridPipeFile},
                   'SUPER_LINK_JUNC_LOCATION':  {'filename': None, 'fileio': None, 'write': None},
                   'SUPERLINK_NODE_LOCATION':   {'filename': None, 'fileio': None, 'write': None},
                   'OVERLAND_DEPTH_LOCATION':   {'filename': None, 'fileio': OutputLocationFile, 'write': iow.writeOutputLocationFile}, # Overland Flow (Other Output)
                   'OVERLAND_WSE_LOCATION':     {'filename': None, 'fileio': OutputLocationFile, 'write': iow.writeOutputLocationFile},
                   'OUT_WELL_LOCATION':         {'filename': None, 'fileio': OutputLocationFile, 'write': iow.writeOutputLocationFile},
                   'REPLACE_PARAMS':            {'filename': None, 'fileio': ReplaceParamFile, 'write': iow.writeReplaceParamFile},     # Replacement Cards
                   'REPLACE_VALS':              {'filename': None, 'fileio': ReplaceValFile, 'write': iow.writeFile}}
    
    INPUT_MAPS = {'ELEVATION':              {'filename': None}, # Required Inputs
                  'WATERSHED_MASK':         {'filename': None}, 
                  'ROUGHNESS':              {'filename': None}, # Overland Flow
                  'RETEN_DEPTH':            {'filename': None},
                  'READ_OV_HOTSTART':       {'filename': None},
                  'STORAGE_CAPACITY':       {'filename': None}, # Interception
                  'INTERCEPTION_COEFF':     {'filename': None},
                  'CONDUCTIVITY':           {'filename': None}, # Infiltration
                  'CAPILLARY':              {'filename': None},
                  'POROSITY':               {'filename': None},
                  'MOISTURE':               {'filename': None},
                  'PORE_INDEX':             {'filename': None},
                  'RESIDUAL_SAT':           {'filename': None},
                  'FIELD_CAPACITY':         {'filename': None},
                  'SOIL_TYPE_MAP':          {'filename': None},
                  'WATER_TABLE':            {'filename': None},
                  'READ_SM_HOTSTART':       {'filename': None},
                  'ALBEDO':                 {'filename': None}, # Continuous Simulation
                  'WILTING_POINT':          {'filename': None},
                  'TCOEFF':                 {'filename': None},
                  'VHEIGHT':                {'filename': None},
                  'CANOPY':                 {'filename': None},
                  'INIT_SWE_DEPTH':         {'filename': None},
                  'WATER_TABLE':            {'filename': None}, # Saturated Groudwater Flow
                  'AQUIFER_BOTTOM':         {'filename': None},
                  'GW_BOUNDFILE':           {'filename': None},
                  'GW_POROSITY_MAP':        {'filename': None},
                  'GW_HYCOND_MAP':          {'filename': None},
                  'CONTAM_MAP':             {'filename': None}} # Constituent Transport
    
    OUTPUT_FILES = {'SUMMARY':              {'filename': None, 'fileio': None, 'write': None},                                  # Required Output
                    'OUTLET_HYDRO':         {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'OUT_THETA_LOCATION':   {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},     # Infiltration
                    'EXPLIC_BACKWATER':     {'filename': None, 'fileio': None, 'write': None},                                  # Channel Routing
                    'WRITE_CHAN_HOTSTART':  {'filename': None, 'fileio': None, 'write': None},
                    'OUT_HYD_LOCATION':     {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'OUT_DEP_LOCATION':     {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'OUT_SED_LOC':          {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'CHAN_DEPTH':           {'filename': None, 'fileio': None, 'write': None}, # Link/Node Format .cdp
                    'CHAN_STAGE':           {'filename': None, 'fileio': None, 'write': None}, # Link/Node Format .cds
                    'CHAN_DISCHARGE':       {'filename': None, 'fileio': None, 'write': None}, # Link/Node Format .cdq
                    'CHAN_VELOCITY':        {'filename': None, 'fileio': None, 'write': None}, # Link/Node Format .cdv
                    'LAKE_OUTPUT':          {'filename': None, 'fileio': None, 'write': None}, # Special? .lel
                    'SNOW_SWE_FILE':        {'filename': None, 'fileio': None, 'write': None},                                  # Continuous Simulation
                    'GW_WELL_LEVEL':        {'filename': None, 'fileio': None, 'write': None},                                  # Saturated Groundwater Flow
                    'OUT_GWFULX_LOCATION':  {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'OUTLET_SED_FLUX':      {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},     # Soil Erosion
                    'ADJUST_ELEV':          {'filename': None, 'fileio': None, 'write': None},
                    'OUTLET_SED_TSS':       {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'OUT_TSS_LOC':          {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'NET_SED_VOLUME':       {'filename': None, 'fileio': None, 'write': None},
                    'VOL_SED_SUSP':         {'filename': None, 'fileio': None, 'write': None},
                    'MAX_SED_FLUX':         {'filename': None, 'fileio': None, 'write': None}, # Link/Node Format
                    'OUT_CON_LOCATION':     {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},     # Constituent Transport
                    'OUT_MASS_LOCATION':    {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'SUPERLINK_JUNC_FLOW':  {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},     # Subsurface Drainage
                    'SUPERLINK_NODE_FLOW':  {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'OVERLAND_DEPTHS':      {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'OVERLAND_WSE':         {'filename': None, 'fileio': TimeSeriesFile, 'write': iow.writeTimeSeriesFile},
                    'OPTIMIZE':             {'filename': None, 'fileio': None, 'write': None}}
    ## TODO: Handle Different Output Map Formats
    OUTPUT_MAPS = {'GW_OUTPUT':         {'filename': None}, # MAP_TYPE # Output Files
                   'DISCHARGE':         {'filename': None}, # MAP_TYPE
                   'DEPTH':             {'filename': None}, # MAP_TYPE
                   'WRITE_OV_HOTSTART': {'filename': None},             # Overland Flow
                   'WRITE_SM_HOSTART':  {'filename': None},             # Infiltration
                   'INF_DEPTH':         {'filename': None}, # MAP_TYPE  # Output Files
                   'SURF_MOIS':         {'filename': None}, # MAP_TYPE
                   'RATE_OF_INFIL':     {'filename': None}, # MAP_TYPE
                   'DIS_RAIN':          {'filename': None}, # MAP_TYPE
                   'GW_OUTPUT':         {'filename': None}, # MAP_TYPE
                   'GW_RECHARGE_CUM':   {'filename': None}, # MAP_TYPE
                   'GW_RECHARGE_INC':   {'filename': None}} # MAP_TYPE
    
    
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
                    # Create GSSHAPY Project Card object
                    prjCard = ProjectCard(name=card['name'], value=card['value'])
                    
                    # Associate ProjectCard with ProjectFile
                    prjCard.projectFile = self
                
                  
                # Assemble list of files for reading
                if card['name'] in self.INPUT_FILES:
                    if self._noneOrNumValue(card['value']):
                        value = card['value'].strip('"')
                        self.INPUT_FILES[card['name']]['filename'] = value
                
                elif card['name'] in self.INPUT_MAPS:
                    if self._noneOrNumValue(card['value']):
                        value = card['value'].strip('"')
                        self.INPUT_MAPS[card['name']]['filename'] = value
                    
                elif card['name'] in self.OUTPUT_FILES:
                    if self._noneOrNumValue(card['value']):
                        value = card['value'].strip('"')
                        self.OUTPUT_FILES[card['name']]['filename'] = value
                
                elif card['name'] in self.OUTPUT_MAPS:
                    if self._noneOrNumValue(card['value']):
                        value = card['value'].strip('"')
                        self.OUTPUT_MAPS[card['name']]['filename'] = value
        
        self.SESSION.add(self)
               
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
                    
                    if self._noneOrNumValue(value):
                        self.INPUT_FILES[card.name]['filename'] = value
                    
                elif card.name in self.INPUT_MAPS:
                    value = card.value.strip('"')
                    
                    if self._noneOrNumValue(value):
                        self.INPUT_MAPS[card.name]['filename'] = value
                    
                elif card.name in self.OUTPUT_FILES:
                    value = card.value.strip('"')
                    
                    if self._noneOrNumValue(value):
                        self.OUTPUT_FILES[card.name]['filename'] = value
                
                elif card.name in self.OUTPUT_MAPS:
                    value = card.value.strip('"')
                    
                    if self._noneOrNumValue(value):
                        self.OUTPUT_MAPS[card.name]['filename'] = value
                     
    def readAll(self):
        '''
        Front Facing GSSHA Project Read from File Method
        '''
        
        # First read self
        self.read()
        
        # Read Input Files
        self._readXput(self.INPUT_FILES)
        
        # Read Output Files
        self._readXput(self.OUTPUT_FILES)
        
        # Read Input Map Files
        self._readXputMaps(self.INPUT_MAPS)
        
        # Read Output Map Files
        self._readXputMaps(self.OUTPUT_MAPS)
        

    def writeAll(self, session, directory, newName=None):
        '''
        Frong Facing GSSHA Project Write All Files to File Method
        '''
        
        # Write Project File
        self.write(session=session, directory=directory, newName=newName)
        
        # Write input files
        self._writeXput(session=session, directory=directory, fileDict=self.INPUT_FILES, newName=newName)
        
        # Write output files
        self._writeXput(session=session, directory=directory, fileDict=self.OUTPUT_FILES, newName=newName)
        
        # Write input map files
        self._writeXputMaps(session=session, directory=directory, fileDict=self.INPUT_MAPS, newName=newName)
        
        # Write output map files
        self._writeXputMaps(session=session, directory=directory, fileDict=self.OUTPUT_MAPS, newName=newName)
        
    def readInput(self):
        '''
        Front Facing GSSHA Read All Input Files Method
        '''
        # Read Project File
        self.read()
        
        # Read Input Files
        self._readXput(self.INPUT_FILES)
        
        # Read Input Map Files
        self._readXputMaps(self.INPUT_MAPS)
        
    def writeInput(self, session, directory, newName=None):
        '''
        Front Facing GSSHA Write All Input Files Method
        '''
        # Write Project File
        self.write(session=session, directory=directory, newName=newName)
        
        # Write input files
        self._writeXput(session=session, directory=directory, fileDict=self.INPUT_FILES, newName=newName)
        
        # Write input map files
        self._writeXputMaps(session=session, directory=directory, fileDict=self.INPUT_MAPS, newName=newName)
        
    def readOutput(self):
        '''
        Front Facing GSSHA Read All Output Files Method
        '''
        # Read Project File
        self.read()
        
        # Read Output Files
        self._readXput(self.OUTPUT_FILES)
        
        # Read Output Map Files
        self._readXputMaps(self.OUTPUT_MAPS)
    
    def writeOutput(self, session, directory, newName=None):
        '''
        Front Facing GSSHA Write All Output Files Method
        '''
        # Write Project File
        self.write(session=session, directory=directory, newName=newName)
        
        # Write output files
        self._writeXput(session=session, directory=directory, fileDict=self.OUTPUT_FILES, newName=newName)
        
        # Write output map files
        self._writeXputMaps(session=session, directory=directory, fileDict=self.OUTPUT_MAPS, newName=newName)
        
        
    def _readXput(self, fileDict):
        '''
        GSSHAPY Project Read Files from File Method
        '''
        ## NOTE: This function is depenedent on the project file being read first
        # Read Input/Output Files
        for card, afile in fileDict.iteritems():
            filename = afile['filename']
            fileio = afile['fileio']

            if (filename != None) and (fileio != None):
                # Initiate read method on each file
                self._readFile(fileIO=fileio,
                               filename=filename)
                
    def _writeXput(self, session, directory, fileDict, newName=None):
        '''
        GSSHA Project Write Files to File Method
        '''
        # Write Input/Output Files
        for card, afile in fileDict.iteritems():
            if afile['filename'] != None:
                # Determine new filename
                filename = self._replaceNewFilename(afile['filename'], newName)
                
                # Extract write funtion from fileDict
                write = afile['write']
                
                # Execute write function if not None
                if write != None:
                    write(projectFile=self,
                          directory=directory,
                          session=session,
                          filename=filename)
                    
    def _readXputMaps(self, fileDict):
        '''
        GSSHA Project Read Map Files from File Method
        '''
        for card, afile in fileDict.iteritems():
            filename = afile['filename']
            
            if filename != None:
                # Create GSSHAPY RasterMapFile object
                self._readFile(fileIO=RasterMapFile,
                               filename=filename)
                
    def _writeXputMaps(self, session, directory, fileDict, newName=None):
        '''
        GSSHAPY Project Write Map Files to File Method
        '''
        for card, afile in fileDict.iteritems():
            if afile['filename'] != None:
                
                # Determine new filename
                filename = self._replaceNewFilename(afile['filename'], newName)
                
                # Write map file
                iow.writeRasterMapFile(projectFile=self,
                                       session=session,
                                       directory=directory,
                                       filename=filename)
                
    def _readFile(self, fileIO, filename):
        '''
        Initiate File Read Method on Other Files
        '''
        instance = fileIO(directory=self.DIRECTORY, filename=filename, session=self.SESSION)
        instance.projectFile = self
        instance.read()
        print 'File Read:', filename
        
    def _replaceNewFilename(self, filename, newName):
        pro = False
        originalProjectName = self.name
        originalFilename = filename
        originalPrefix = originalFilename.split('.')[0]
        extension = originalFilename.split('.')[1]
        
        # Special case with projection file
        if '_' in originalPrefix:
            originalPrefix = originalPrefix.split('_')[0]
            pro = True
        
        # Handle new name
        if newName == None:
            # The project name is not changed and file names
            # stay the same
            filename = originalFilename
        
        elif originalPrefix == originalProjectName and pro:
            # Handle renaming of projection file
            filename = '%s_prj.%s' % (newName, extension)
            
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
            
        return filename
    
    def _noneOrNumValue(self, value):
        '''
        Check if the value of a card is none or a number.
        '''
        if value != None:
            try:
                float(value)
                # If the value is a number, return false
                return False
            except:
                # If the value is not a number or none return true
                return True
        # If the value is a None type, then return false
        return False
        
        
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
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))
    
    # Value Columns
    name = Column(String, nullable=False)
    value = Column(String)
    
    # Relationship Properties
    projectFile = relationship('ProjectFile', back_populates='projectCards')
    
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
