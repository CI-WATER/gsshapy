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

import re, shlex, os

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase
from gsshapy.orm.file_io import *

class ProjectFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    '''
    __tablename__ = 'prj_project_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    precipFileID = Column(Integer, ForeignKey('gag_precipitation_files.id')) #: FK
    mapTableFileID = Column(Integer, ForeignKey('cmt_map_table_files.id')) #: FK
    channelInputFileID = Column(Integer, ForeignKey('cif_channel_input_files.id')) #: FK
    stormPipeNetworkFileID = Column(Integer, ForeignKey('spn_storm_pipe_network_files.id')) #: FK
    hmetFileID = Column(Integer, ForeignKey('hmet_files.id')) #: FK
    nwsrfsFileID = Column(Integer, ForeignKey('snw_nwsrfs_files.id')) #: FK
    orthoGageFileID = Column(Integer, ForeignKey('snw_orthographic_gage_files.id')) #: FK
    gridPipeFileID = Column(Integer, ForeignKey('gpi_grid_pipe_files.id')) #: FK
    gridStreamFileID = Column(Integer, ForeignKey('gst_grid_stream_files.id')) #: FK
    projectionFileID = Column(Integer, ForeignKey('pro_projection_files.id')) #: FK
    replaceParamFileID = Column(Integer, ForeignKey('rep_replace_param_files.id')) #: FK
    replaceValFileID = Column(Integer, ForeignKey('rep_replace_val_files.id')) #: FK
    
    # Value Columns
    name = Column(String, nullable=False) #: STRING
    mapType = Column(Integer, nullable=False) #: INTEGER
    
    # Relationship Properties
    projectCards = relationship('ProjectCard', back_populates='projectFile') #: RELATIONSHIP
    
    # File Relationship Properties
    mapTableFile = relationship('MapTableFile', back_populates='projectFile') #: RELATIONSHIP
    channelInputFile = relationship('ChannelInputFile', back_populates='projectFile') #: RELATIONSHIP
    precipFile = relationship('PrecipFile', back_populates='projectFile') #: RELATIONSHIP
    stormPipeNetworkFile = relationship('StormPipeNetworkFile', back_populates='projectFile') #: RELATIONSHIP
    hmetFile = relationship('HmetFile', back_populates='projectFile') #: RELATIONSHIP
    nwsrfsFile = relationship('NwsrfsFile', back_populates='projectFile') #: RELATIONSHIP
    orthoGageFile = relationship('OrthographicGageFile', back_populates='projectFile') #: RELATIONSHIP
    gridPipeFile = relationship('GridPipeFile', back_populates='projectFile') #: RELATIONSHIP
    gridStreamFile = relationship('GridStreamFile', back_populates='projectFile') #: RELATIONSHIP
    timeSeriesFiles = relationship('TimeSeriesFile', back_populates='projectFile') #: RELATIONSHIP
    projectionFile = relationship('ProjectionFile', back_populates='projectFile') #: RELATIONSHIP
    replaceParamFile = relationship('ReplaceParamFile', back_populates='projectFile') #: RELATIONSHIP
    replaceValFile = relationship('ReplaceValFile', back_populates='projectFile') #: RELATIONSHIP
    outputLocationFiles = relationship('OutputLocationFile', back_populates='projectFile') #: RELATIONSHIP
    maps = relationship('RasterMapFile', back_populates='projectFile') #: RELATIONSHIP
    linkNodeDatasets = relationship('LinkNodeDatasetFile', back_populates='projectFile') #: RELATIONSHIP
    
    # File Properties
    EXTENSION = 'prj'
    MAP_TYPES_SUPPORTED = (1,)
    
    INPUT_FILES = {'#PROJECTION_FILE':          {'filename': None, 'fileio': ProjectionFile},       # WMS
                   'MAPPING_TABLE':             {'filename': None, 'fileio': MapTableFile},         # Mapping Table
                   'ST_MAPPING_TABLE':          {'filename': None, 'fileio': None},
                   'PRECIP_FILE':               {'filename': None, 'fileio': PrecipFile},           # Precipitation
                   'CHANNEL_INPUT':             {'filename': None, 'fileio': ChannelInputFile},     # Channel Routing
                   'STREAM_CELL':               {'filename': None, 'fileio': GridStreamFile},
                   'SECTION_TABLE':             {'filename': None, 'fileio': None},
                   'SOIL_LAYER_INPUT_FILE':     {'filename': None, 'fileio': None},                 # Infiltration
                   'IN_THETA_LOCATION':         {'filename': None, 'fileio': OutputLocationFile},
                   'EXPLIC_HOTSTART':           {'filename': None, 'fileio': None},
                   'READ_CHAN_HOTSTART':        {'filename': None, 'fileio': None},
                   'CHAN_POINT_INPUT':          {'filename': None, 'fileio': None},
                   'IN_HYD_LOCATION':           {'filename': None, 'fileio': OutputLocationFile},
                   'IN_SED_LOC':                {'filename': None, 'fileio': OutputLocationFile},
                   'IN_GWFLUX_LOCATION':        {'filename': None, 'fileio': OutputLocationFile},
                   'HMET_SURFAWAYS':            {'filename': None, 'fileio': None},                 # Continuous Simulation
                   'HMET_SAMSON':               {'filename': None, 'fileio': None},
                   'HMET_WES':                  {'filename': None, 'fileio': HmetFile},
                   'NWSRFS_ELEV_SNOW':          {'filename': None, 'fileio': NwsrfsFile},
                   'HMET_OROG_GAGES':           {'filename': None, 'fileio': OrthographicGageFile},
                   'HMET_ASCII':                {'filename': None, 'fileio': None},
                   'GW_FLUXBOUNDTABLE':         {'filename': None, 'fileio': None},                 # Saturated Groundwater Flow
                   'STORM_SEWER':               {'filename': None, 'fileio': StormPipeNetworkFile}, # Subsurface Drainage
                   'GRID_PIPE':                 {'filename': None, 'fileio': GridPipeFile},
                   'SUPER_LINK_JUNC_LOCATION':  {'filename': None, 'fileio': None},
                   'SUPERLINK_NODE_LOCATION':   {'filename': None, 'fileio': None},
                   'OVERLAND_DEPTH_LOCATION':   {'filename': None, 'fileio': OutputLocationFile},   # Overland Flow (Other Output)
                   'OVERLAND_WSE_LOCATION':     {'filename': None, 'fileio': OutputLocationFile},
                   'OUT_WELL_LOCATION':         {'filename': None, 'fileio': OutputLocationFile},
                   'REPLACE_PARAMS':            {'filename': None, 'fileio': ReplaceParamFile},     # Replacement Cards
                   'REPLACE_VALS':              {'filename': None, 'fileio': ReplaceValFile}}
    
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
                  'EMBANKMENT':             {'filename': None}, # Embankment Structures
                  'DIKE_MASK':              {'filename': None},
                  'WETLAND':                {'filename': None}, # Wetlands
                  'CONTAM_MAP':             {'filename': None}} # Constituent Transport
    
    OUTPUT_FILES = {'SUMMARY':              {'filename': None, 'fileio': None},                 # Required Output
                    'OUTLET_HYDRO':         {'filename': None, 'fileio': TimeSeriesFile},
                    'DEPTH':                {'filename': None, 'fileio': None},
                    'OUT_THETA_LOCATION':   {'filename': None, 'fileio': TimeSeriesFile},       # Infiltration
                    'EXPLIC_BACKWATER':     {'filename': None, 'fileio': None},                 # Channel Routing
                    'WRITE_CHAN_HOTSTART':  {'filename': None, 'fileio': None},
                    'OUT_HYD_LOCATION':     {'filename': None, 'fileio': TimeSeriesFile},
                    'OUT_DEP_LOCATION':     {'filename': None, 'fileio': TimeSeriesFile},
                    'OUT_SED_LOC':          {'filename': None, 'fileio': TimeSeriesFile},
                    'CHAN_DEPTH':           {'filename': None, 'fileio': LinkNodeDatasetFile},
                    'CHAN_STAGE':           {'filename': None, 'fileio': LinkNodeDatasetFile},
                    'CHAN_DISCHARGE':       {'filename': None, 'fileio': LinkNodeDatasetFile},
                    'CHAN_VELOCITY':        {'filename': None, 'fileio': LinkNodeDatasetFile},
                    'LAKE_OUTPUT':          {'filename': None, 'fileio': None},  ## TODO: Special format? .lel
                    'SNOW_SWE_FILE':        {'filename': None, 'fileio': None},                 # Continuous Simulation
                    'GW_WELL_LEVEL':        {'filename': None, 'fileio': None},                 # Saturated Groundwater Flow
                    'OUT_GWFULX_LOCATION':  {'filename': None, 'fileio': TimeSeriesFile},
                    'OUTLET_SED_FLUX':      {'filename': None, 'fileio': TimeSeriesFile},       # Soil Erosion
                    'ADJUST_ELEV':          {'filename': None, 'fileio': None},
                    'OUTLET_SED_TSS':       {'filename': None, 'fileio': TimeSeriesFile},
                    'OUT_TSS_LOC':          {'filename': None, 'fileio': TimeSeriesFile},
                    'NET_SED_VOLUME':       {'filename': None, 'fileio': None},
                    'VOL_SED_SUSP':         {'filename': None, 'fileio': None},
                    'MAX_SED_FLUX':         {'filename': None, 'fileio': LinkNodeDatasetFile},
                    'OUT_CON_LOCATION':     {'filename': None, 'fileio': TimeSeriesFile},       # Constituent Transport
                    'OUT_MASS_LOCATION':    {'filename': None, 'fileio': TimeSeriesFile},
                    'SUPERLINK_JUNC_FLOW':  {'filename': None, 'fileio': TimeSeriesFile},       # Subsurface Drainage
                    'SUPERLINK_NODE_FLOW':  {'filename': None, 'fileio': TimeSeriesFile},
                    'OVERLAND_DEPTHS':      {'filename': None, 'fileio': TimeSeriesFile},
                    'OVERLAND_WSE':         {'filename': None, 'fileio': TimeSeriesFile},
                    'OPTIMIZE':             {'filename': None, 'fileio': None}}
    ## TODO: Handle Different Output Map Formats
    OUTPUT_MAPS = {'GW_OUTPUT':         {'filename': None}, # MAP_TYPE  # Output Files
                   'DISCHARGE':         {'filename': None}, # MAP_TYPE
                   'INF_DEPTH':         {'filename': None}, # MAP_TYPE
                   'SURF_MOIS':         {'filename': None}, # MAP_TYPE
                   'RATE_OF_INFIL':     {'filename': None}, # MAP_TYPE
                   'DIS_RAIN':          {'filename': None}, # MAP_TYPE
                   'GW_OUTPUT':         {'filename': None}, # MAP_TYPE
                   'GW_RECHARGE_CUM':   {'filename': None}, # MAP_TYPE
                   'GW_RECHARGE_INC':   {'filename': None}, # MAP_TYPE
                   'WRITE_OV_HOTSTART': {'filename': None},             # Overland Flow
                   'WRITE_SM_HOSTART':  {'filename': None}}             # Infiltration
    
    # Error Messages
    COMMIT_ERROR_MESSAGE = ('Ensure the files listed in the project file '
                            'are not empty and try again.')
    
    
    def __init__(self, directory, filename, session):
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
        self.name = filename.split('.')[0]
    
    
    def _readWithoutCommit(self):
        '''
        Project File Read from File Method
        '''
        HEADERS = ('GSSHAPROJECT')
        
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
                    
                    # Extract MAP_TYPE card value for convenience working
                    # with output maps
                    if card['name'] == 'MAP_TYPE':
                        self.mapType = int(card['value'])
                
                ## TODO: Consider refactoring how the lists of files to read and write are compiled
                ##       i.e.: Don't want this to run when project file is read alone.  
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
        
        
               
    def _writeToOpenFile(self, session, openFile):
        '''
        Project File Write to File Method
        '''
        # Write lines
        openFile.write('GSSHAPROJECT\n')
        filename = os.path.split(openFile.name)[1]
        name = filename.split('.')[0]
    
        # Initiate write on each ProjectCard that belongs to this ProjectFile
        for card in self.projectCards:
            openFile.write(card.write(originalPrefix=self.name, newPrefix=name))
            
            # Assemble list of files for writing
            if card.name in self.INPUT_FILES:
                value = card.value.strip('"')
                
                if self._noneOrNumValue(value):
                    self.INPUT_FILES[card.name]['filename'] = value
                
            elif card.name in self.INPUT_MAPS:
                try:
                    value = card.value.strip('"')
                    
                    if self._noneOrNumValue(value):
                        self.INPUT_MAPS[card.name]['filename'] = value
                except:
                    '''DO NOTHING'''
                
                
                
            elif card.name in self.OUTPUT_FILES:
                value = card.value.strip('"')
                
                if self._noneOrNumValue(value):
                    self.OUTPUT_FILES[card.name]['filename'] = value
            
            elif card.name in self.OUTPUT_MAPS:
                value = card.value.strip('"')
                
                if self._noneOrNumValue(value):
                    self.OUTPUT_MAPS[card.name]['filename'] = value
        
#         print 'File Written:', filename

    def appendDirectory(self, directory):
        '''
        Append directory to relative paths in project file.
        By default, the project files are written with relative paths.
        '''
        lines = []
        with open(self.PATH, 'r') as original:
            for l in original:
                lines.append(l)
                
                
        with open(self.PATH, 'w') as new:
            for line in lines:
                card = {}
                try:
                    card = self._extractCard(line)    
                    
                except:
                    card = self._extractDirectoryCard(line)
                
                # Determine number of spaces between card and value for nice alignment
                numSpaces = 25 - len(card['name'])
                
                if card['value'] is None:
                    rewriteLine = '%s\n' % (card['name'])
                else:
                    if card['name'] == 'WMS':
                        rewriteLine = '%s %s\n' % (card['name'], card['value'])
                    elif card['name'] == 'PROJECT_PATH':
                        filePath = '"%s"' % os.path.normpath(directory)
                        rewriteLine ='%s%s%s\n' % (card['name'],' '*numSpaces, filePath)
                    elif '"' in card['value']:
                        filename = card['value'].strip('"')
                        filePath = '"%s"' % os.path.join(directory, filename)
                        rewriteLine ='%s%s%s\n' % (card['name'],' '*numSpaces, filePath)
                    else:
                        rewriteLine ='%s%s%s\n' % (card['name'],' '*numSpaces, card['value'])
                
                new.write(rewriteLine)
            
            
        
                     
    def readProject(self):
        '''
        Read all files for a GSSHA project into the database.
        '''
        # Add project file to session
        self.SESSION.add(self)
        
        # First read self
        self._readWithoutCommit()
        
        # Read Input Files
        self._readXput(self.INPUT_FILES)
        
        # Read Output Files
        self._readXput(self.OUTPUT_FILES)
        
        # Read Input Map Files
        self._readXputMaps(self.INPUT_MAPS)
        
        # Read Output Map Files
        self._readXputMaps(self.OUTPUT_MAPS)
        
        # Commit to database
        self._commit(self.COMMIT_ERROR_MESSAGE)
        
        # Feedback
#         print 'SUCCESS: Project successfully read to database.'
        

    def writeProject(self, session, directory, name):
        '''
        Write all files for a project from the database to file.
        
        
        *session* = SQLAlchemy session object\n
        *directory* = to which directory will the files be written (e.g.: '/example/path')\n
        *name* = project name (e.g.: 'my_project')\n
        '''
        
        # Write Project File
        self.write(session=session, directory=directory, name=name)
        
        # Write input files
        self._writeXput(session=session, directory=directory, fileDict=self.INPUT_FILES, name=name)
        
        # Write output files
        self._writeXput(session=session, directory=directory, fileDict=self.OUTPUT_FILES, name=name)
        
        # Write input map files
        self._writeXputMaps(session=session, directory=directory, fileDict=self.INPUT_MAPS, name=name)
        
        # Write output map files
        self._writeXputMaps(session=session, directory=directory, fileDict=self.OUTPUT_MAPS, name=name)
        
#         print 'SUCCESS: Project successfully written to file.'
        
    def readInput(self):
        '''
        Read only input files for a GSSHA project into the database.
        '''
        # Add project file to session
        self.SESSION.add(self)
        
        # Read Project File
        self._readWithoutCommit()
        
        # Read Input Files
        self._readXput(self.INPUT_FILES)
        
        # Read Input Map Files
        self._readXputMaps(self.INPUT_MAPS)
        
        # Commit to database
        self._commit(self.COMMIT_ERROR_MESSAGE)
        
    def writeInput(self, session, directory, name):
        '''
        Write only input files for a GSSHA project from the database to file.
        
        
        *session* = SQLAlchemy session object\n
        *directory* = to which directory will the files be written (e.g.: '/example/path')\n
        *name* = project name (e.g.: 'my_project')\n
        '''
        # Write Project File
        self.write(session=session, directory=directory, name=name)
        
        # Write input files
        self._writeXput(session=session, directory=directory, fileDict=self.INPUT_FILES, name=name)
        
        # Write input map files
        self._writeXputMaps(session=session, directory=directory, fileDict=self.INPUT_MAPS, name=name)
        
    def readOutput(self):
        '''
        Read only output files for a GSSHA project to the database.
        '''
        # Add project file to session
        self.SESSION.add(self)
        
        # Read Project File
        self.read()
        
        # Read Output Files
        self._readXput(self.OUTPUT_FILES)
        
        # Read Output Map Files
        self._readXputMaps(self.OUTPUT_MAPS)
        
        # Commit to database
        self._commit(self.COMMIT_ERROR_MESSAGE)
    
    def writeOutput(self, session, directory, name):
        '''
        Write only output files for a GSSHA project from the database to file.
        
        
        *session* = SQLAlchemy session object\n
        *directory* = to which directory will the files be written (e.g.: '/example/path')\n
        *name* = project name (e.g.: 'my_project')\n
        '''
        # Write Project File
        self.write(session=session, directory=directory, name=name)
        
        # Write output files
        self._writeXput(session=session, directory=directory, fileDict=self.OUTPUT_FILES, name=name)
        
        # Write output map files
        self._writeXputMaps(session=session, directory=directory, fileDict=self.OUTPUT_MAPS, name=name)
        
        
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
                self._invokeRead(fileIO=fileio,
                                 filename=filename)
                
    def _writeXput(self, session, directory, fileDict, name=None):
        '''
        GSSHA Project Write Files to File Method
        '''
        # Write Input/Output Files
        for card, afile in fileDict.iteritems():
            filename = afile['filename']
            fileIO = afile['fileio']
            
            if (filename != None) and (fileIO != None):
                # Determine new filename
                filename = self._replaceNewFilename(afile['filename'], name)
                
                # Initiate write method on each file
                self._invokeWrite(fileIO=fileIO,
                                  session=session,
                                  directory=directory,
                                  filename=filename)
                    
    def _readXputMaps(self, fileDict):
        '''
        GSSHA Project Read Map Files from File Method
        '''
        if self.mapType in self.MAP_TYPES_SUPPORTED:
            for card, afile in fileDict.iteritems():
                filename = afile['filename']
                
                if filename != None:
                    # Create GSSHAPY RasterMapFile object
                    self._invokeRead(fileIO=RasterMapFile,
                                     filename=filename)
        else:
            print 'Error: Could not read map files. MAP_TYPE', self.mapType, 'not supported.'
                
    def _writeXputMaps(self, session, directory, fileDict, name=None):
        '''
        GSSHAPY Project Write Map Files to File Method
        '''
        if self.mapType in self.MAP_TYPES_SUPPORTED:
            for card, afile in fileDict.iteritems():
                if afile['filename'] != None:
                    
                    # Determine new filename
                    filename = self._replaceNewFilename(afile['filename'], name)
                    
                    # Write map file
                    self._invokeWrite(fileIO=RasterMapFile,
                                      session=session,
                                      directory=directory,
                                      filename=filename)
        else:
            print 'Error: Could not write map files. MAP_TYPE', self.mapType, 'not supported.'
            
    def _invokeRead(self, fileIO, filename):
        '''
        Invoke File Read Method on Other Files
        '''
        instance = fileIO(directory=self.DIRECTORY, filename=filename, session=self.SESSION)
        instance.projectFile = self
        instance._readWithoutCommit()
#         print 'File Read:', filename
        
    def _invokeWrite(self, fileIO, session, directory, filename):
        '''
        Invoke File Write Method on Other Files
        '''
        try:
            # Handle case where fileIO interfaces with single file
            # Retrieve File using FileIO
            instance = session.query(fileIO).\
                        filter(fileIO.projectFile == self).\
                        one()
                        
        except:
            # Handle case where fileIO interfaces with multiple files
            # Retrieve File using FileIO and file extension
            extension = filename.split('.')[1]
            
            instance = session.query(fileIO).\
                        filter(fileIO.projectFile == self).\
                        filter(fileIO.fileExtension == extension).\
                        one()
            
            
        # Initiate Write Method on File
        instance.write(session=session, directory=directory, name=filename)

        
#         print 'File Written:', filename
        
    def _replaceNewFilename(self, filename, name):
        # Variables
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
        if name == None:
            # The project name is not changed and file names
            # stay the same
            filename = originalFilename
        
        elif originalPrefix == originalProjectName and pro:
            # Handle renaming of projection file
            filename = '%s_prj.%s' % (name, extension)
            
        elif originalPrefix == originalProjectName:
            # This check is necessary because not all filenames are 
            # prefixed with the project name. Thus the file prefix
            # is only changed for files that are prefixed with the 
            # project name
            filename = '%s.%s' % (name, extension)
        
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
            
            try:
                # If the value is able to be converted to a
                # float (any number) then store value only.
                # Store all values if there are multiple.
                float(pathSplit[-1])
                cardValue = ' '.join(splitLine[1:])
            except:
                # A string will throw an exception with
                # an atempt to convert to float. In this 
                # case wrap the string in double quotes.
                if cardName == 'WMS':
                    cardValue = ' '.join(splitLine[1:])
                elif '.' in pathSplit[-1]:
                    if cardName == '#INDEXGRID_GUID':
                        try:
                            # Get WMS ID for Index Map as part of value
                            cardValue = '"%s" "%s"' % (pathSplit[-1], splitLine[2])
                        except:
                            # Like normal if the ID isn't there
                            cardValue = '"%s"' % pathSplit[-1]
                    else:
                        # If the string contains a '.' it is a
                        # path: wrap in double quotes
                        cardValue = '"%s"' % pathSplit[-1]
                elif pathSplit[-1] == '':
                    # For directory cards with unix paths 
                    # use double quotes (all paths will be
                    # stored as relative).
                    cardValue = '""'
                else:
                    # Else it is a card name/option
                    # don't wrap in quotes
                    cardValue = pathSplit[-1]
        
        # For boolean cards store None
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
    '''
    __tablename__ = 'prj_project_cards'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True) #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id')) #: FK
    
    # Value Columns
    name = Column(String, nullable=False) #: STRING
    value = Column(String) #: STRING
    
    # Relationship Properties
    projectFile = relationship('ProjectFile', back_populates='projectCards') #: RELATIONSHIP
    
    def __init__(self, name, value):
        '''
        Constructor
        '''
        self.name = name
        self.value = value
        

    def __repr__(self):
        return '<ProjectCard: Name=%s, Value=%s>' % (self.name, self.value)
    
    def write(self, originalPrefix, newPrefix=None):
        # Determine number of spaces between card and value for nice alignment
        numSpaces = 25 - len(self.name)
        
        # Handle special case of booleans
        if self.value is None:
            line = '%s\n' % (self.name)
        else:
            if self.name == 'WMS':
                line = '%s %s\n' % (self.name, self.value)
            elif newPrefix == None:
                line ='%s%s%s\n' % (self.name,' '*numSpaces, self.value)
            elif originalPrefix in self.value:
                line ='%s%s%s\n' % (self.name,' '*numSpaces, self.value.replace(originalPrefix, newPrefix))
            else:
                line ='%s%s%s\n' % (self.name,' '*numSpaces, self.value)
        return line
