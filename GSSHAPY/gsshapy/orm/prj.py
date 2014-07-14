"""
********************************************************************************
* Name: ProjectFileModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

__all__ = ['ProjectFile',
           'ProjectCard']

import re
import shlex
import os

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase
from gsshapy.orm.file_io import *


class ProjectFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    """
    __tablename__ = 'prj_project_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    precipFileID = Column(Integer, ForeignKey('gag_precipitation_files.id'))  #: FK
    mapTableFileID = Column(Integer, ForeignKey('cmt_map_table_files.id'))  #: FK
    channelInputFileID = Column(Integer, ForeignKey('cif_channel_input_files.id'))  #: FK
    stormPipeNetworkFileID = Column(Integer, ForeignKey('spn_storm_pipe_network_files.id'))  #: FK
    hmetFileID = Column(Integer, ForeignKey('hmet_files.id'))  #: FK
    nwsrfsFileID = Column(Integer, ForeignKey('snw_nwsrfs_files.id'))  #: FK
    orthoGageFileID = Column(Integer, ForeignKey('snw_orthographic_gage_files.id'))  #: FK
    gridPipeFileID = Column(Integer, ForeignKey('gpi_grid_pipe_files.id'))  #: FK
    gridStreamFileID = Column(Integer, ForeignKey('gst_grid_stream_files.id'))  #: FK
    projectionFileID = Column(Integer, ForeignKey('pro_projection_files.id'))  #: FK
    replaceParamFileID = Column(Integer, ForeignKey('rep_replace_param_files.id'))  #: FK
    replaceValFileID = Column(Integer, ForeignKey('rep_replace_val_files.id'))  #: FK

    # Value Columns
    srid = Column(Integer)  #: SRID
    name = Column(String, nullable=False)  #: STRING
    mapType = Column(Integer, nullable=False)  #: INTEGER
    fileExtension = Column(String, default='prj')  #: STRING

    # Relationship Properties
    projectCards = relationship('ProjectCard', back_populates='projectFile')  #: RELATIONSHIP

    # Unique File Relationship Properties
    mapTableFile = relationship('MapTableFile', back_populates='projectFile')  #: RELATIONSHIP
    channelInputFile = relationship('ChannelInputFile', back_populates='projectFile')  #: RELATIONSHIP
    precipFile = relationship('PrecipFile', back_populates='projectFile')  #: RELATIONSHIP
    stormPipeNetworkFile = relationship('StormPipeNetworkFile', back_populates='projectFile')  #: RELATIONSHIP
    hmetFile = relationship('HmetFile', back_populates='projectFile')  #: RELATIONSHIP
    nwsrfsFile = relationship('NwsrfsFile', back_populates='projectFile')  #: RELATIONSHIP
    orthoGageFile = relationship('OrthographicGageFile', back_populates='projectFile')  #: RELATIONSHIP
    gridPipeFile = relationship('GridPipeFile', back_populates='projectFile')  #: RELATIONSHIP
    gridStreamFile = relationship('GridStreamFile', back_populates='projectFile')  #: RELATIONSHIP
    projectionFile = relationship('ProjectionFile', back_populates='projectFile')  #: RELATIONSHIP
    replaceParamFile = relationship('ReplaceParamFile', back_populates='projectFile')  #: RELATIONSHIP
    replaceValFile = relationship('ReplaceValFile', back_populates='projectFile')  #: RELATIONSHIP

    # Collection File Relationship Properties
    timeSeriesFiles = relationship('TimeSeriesFile', back_populates='projectFile')  #: RELATIONSHIP
    outputLocationFiles = relationship('OutputLocationFile', back_populates='projectFile')  #: RELATIONSHIP
    maps = relationship('RasterMapFile', back_populates='projectFile')  #: RELATIONSHIP
    linkNodeDatasets = relationship('LinkNodeDatasetFile', back_populates='projectFile')  #: RELATIONSHIP
    genericFiles = relationship('GenericFile', back_populates='projectFile')  #: RELATIONSHIP
    wmsDatasets = relationship('WMSDatasetFile', back_populates='projectFile')  #: RELATIONSHIP

    # File Properties
    MAP_TYPES_SUPPORTED = (1,)
    ALWAYS_READ_AND_WRITE_MAPS = ('ele', 'msk')

    INPUT_FILES = {'#PROJECTION_FILE': ProjectionFile,  # WMS
                   'MAPPING_TABLE': MapTableFile,  # Mapping Table
                   'ST_MAPPING_TABLE': GenericFile,
                   'PRECIP_FILE': PrecipFile,  # Precipitation
                   'CHANNEL_INPUT': ChannelInputFile,  # Channel Routing
                   'STREAM_CELL': GridStreamFile,
                   'SECTION_TABLE': GenericFile,
                   'SOIL_LAYER_INPUT_FILE': GenericFile,  # Infiltration
                   'IN_THETA_LOCATION': OutputLocationFile,
                   'EXPLIC_HOTSTART': GenericFile,
                   'READ_CHAN_HOTSTART': GenericFile,
                   'CHAN_POINT_INPUT': GenericFile,
                   'IN_HYD_LOCATION': OutputLocationFile,
                   'IN_SED_LOC': OutputLocationFile,
                   'IN_GWFLUX_LOCATION': OutputLocationFile,
                   'HMET_SURFAWAYS': GenericFile,  # Continuous Simulation
                   'HMET_SAMSON': GenericFile,  ## TODO: Create support in HmetFile for these formats
                   'HMET_WES': HmetFile,
                   'NWSRFS_ELEV_SNOW': NwsrfsFile,
                   'HMET_OROG_GAGES': OrthographicGageFile,
                   'HMET_ASCII': GenericFile,
                   'GW_FLUXBOUNDTABLE': GenericFile,  # Saturated Groundwater Flow
                   'STORM_SEWER': StormPipeNetworkFile,  # Subsurface Drainage
                   'GRID_PIPE': GridPipeFile,
                   'SUPER_LINK_JUNC_LOCATION': GenericFile,
                   'SUPERLINK_NODE_LOCATION': GenericFile,
                   'OVERLAND_DEPTH_LOCATION': OutputLocationFile,  # Overland Flow (Other Output)
                   'OVERLAND_WSE_LOCATION': OutputLocationFile,
                   'OUT_WELL_LOCATION': OutputLocationFile,
                   'REPLACE_PARAMS': ReplaceParamFile,  # Replacement Cards
                   'REPLACE_VALS': ReplaceValFile}

    INPUT_MAPS = ('ELEVATION',  # Required Inputs
                  'WATERSHED_MASK',
                  'ROUGHNESS',  # Overland Flow
                  'RETEN_DEPTH',
                  'READ_OV_HOTSTART',
                  'STORAGE_CAPACITY',  # Interception
                  'INTERCEPTION_COEFF',
                  'CONDUCTIVITY',  # Infiltration
                  'CAPILLARY',
                  'POROSITY',
                  'MOISTURE',
                  'PORE_INDEX',
                  'RESIDUAL_SAT',
                  'FIELD_CAPACITY',
                  'SOIL_TYPE_MAP',
                  'WATER_TABLE',
                  'READ_SM_HOTSTART',
                  'ALBEDO',  # Continuous Simulation
                  'WILTING_POINT',
                  'TCOEFF',
                  'VHEIGHT',
                  'CANOPY',
                  'INIT_SWE_DEPTH',
                  'WATER_TABLE',  # Saturated Groudwater Flow
                  'AQUIFER_BOTTOM',
                  'GW_BOUNDFILE',
                  'GW_POROSITY_MAP',
                  'GW_HYCOND_MAP',
                  'EMBANKMENT',  # Embankment Structures
                  'DIKE_MASK',
                  'WETLAND',  # Wetlands
                  'CONTAM_MAP')  # Constituent Transport

    OUTPUT_FILES = {'SUMMARY': GenericFile,  # Required Output
                    'OUTLET_HYDRO': TimeSeriesFile,
                    'DEPTH': None,  ## TODO: Binary format? .lel
                    'OUT_THETA_LOCATION': TimeSeriesFile,  # Infiltration
                    'EXPLIC_BACKWATER': GenericFile,  # Channel Routing
                    'WRITE_CHAN_HOTSTART': GenericFile,
                    'OUT_HYD_LOCATION': TimeSeriesFile,
                    'OUT_DEP_LOCATION': TimeSeriesFile,
                    'OUT_SED_LOC': TimeSeriesFile,
                    'CHAN_DEPTH': LinkNodeDatasetFile,
                    'CHAN_STAGE': LinkNodeDatasetFile,
                    'CHAN_DISCHARGE': LinkNodeDatasetFile,
                    'CHAN_VELOCITY': LinkNodeDatasetFile,
                    'LAKE_OUTPUT': GenericFile,  ## TODO: Special format? .lel
                    'SNOW_SWE_FILE': None,  # Continuous Simulation ## TODO: Binary format?
                    'GW_WELL_LEVEL': GenericFile,  # Saturated Groundwater Flow
                    'OUT_GWFULX_LOCATION': TimeSeriesFile,
                    'OUTLET_SED_FLUX': TimeSeriesFile,  # Soil Erosion
                    'ADJUST_ELEV': GenericFile,
                    'OUTLET_SED_TSS': TimeSeriesFile,
                    'OUT_TSS_LOC': TimeSeriesFile,
                    'NET_SED_VOLUME': GenericFile,
                    'VOL_SED_SUSP': GenericFile,
                    'MAX_SED_FLUX': LinkNodeDatasetFile,
                    'OUT_CON_LOCATION': TimeSeriesFile,  # Constituent Transport
                    'OUT_MASS_LOCATION': TimeSeriesFile,
                    'SUPERLINK_JUNC_FLOW': TimeSeriesFile,  # Subsurface Drainage
                    'SUPERLINK_NODE_FLOW': TimeSeriesFile,
                    'OVERLAND_DEPTHS': TimeSeriesFile,
                    'OVERLAND_WSE': TimeSeriesFile,
                    'OPTIMIZE': GenericFile}

    ## TODO: Handle Different Output Map Formats
    OUTPUT_MAPS = ('GW_OUTPUT',  # MAP_TYPE  # Output Files
                   'DISCHARGE',  # MAP_TYPE
                   'INF_DEPTH',  # MAP_TYPE
                   'SURF_MOIS',  # MAP_TYPE
                   'RATE_OF_INFIL',  # MAP_TYPE
                   'DIS_RAIN',  # MAP_TYPE
                   'GW_OUTPUT',  # MAP_TYPE
                   'GW_RECHARGE_CUM',  # MAP_TYPE
                   'GW_RECHARGE_INC',  # MAP_TYPE
                   'WRITE_OV_HOTSTART',  # Overland Flow
                   'WRITE_SM_HOSTART')  # Infiltration

    WMS_DATASETS = ('DEPTH', )

    # Error Messages
    COMMIT_ERROR_MESSAGE = ('Ensure the files listed in the project file '
                            'are not empty and try again.')

    def __init__(self):
        GsshaPyFileObjectBase.__init__(self)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, raster2pgsqlPath):
        """
        Project File Read from File Method
        """
        # Headers to ignore
        HEADERS = ('GSSHAPROJECT')

        with open(path, 'r') as f:
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

        # Assign properties
        self.srid = spatialReferenceID
        self.name = name
        self.fileExtension = extension

    def _write(self, session, openFile):
        """
        Project File Write to File Method
        """
        # Enforce cards that must be written in certain order
        PRIORITY_CARDS = ('WMS', 'MASK_WATERSHED', 'REPLACE_LINE', 'REPLACE_PARAMS', 'REPLACE_VALS', 'REPLACE_FOLDER')

        filename = os.path.split(openFile.name)[1]
        name = filename.split('.')[0]

        # Write lines
        openFile.write('GSSHAPROJECT\n')

        # Write priority lines
        for card_key in PRIORITY_CARDS:
            card = self.getCard(card_key)

            # Write the card
            if card is not None:
                openFile.write(card.write(originalPrefix=self.name, newPrefix=name))

        # Initiate write on each ProjectCard that belongs to this ProjectFile
        for card in self.projectCards:
            if card.name not in PRIORITY_CARDS:
                openFile.write(card.write(originalPrefix=self.name, newPrefix=name))

    def appendDirectory(self, directory, projectFilePath):
        """
        Append directory to relative paths in project file.
        By default, the project files are written with relative paths.
        """

        ## TODO: Test whether this works or not (changed from self.PATH global to projectFilePath parameter)

        lines = []
        with open(projectFilePath, 'r') as original:
            for l in original:
                lines.append(l)

        with open(projectFilePath, 'w') as new:
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
                        rewriteLine = '%s%s%s\n' % (card['name'], ' ' * numSpaces, filePath)

                    elif '"' in card['value']:
                        filename = card['value'].strip('"')
                        filePath = '"%s"' % os.path.join(directory, filename)
                        rewriteLine = '%s%s%s\n' % (card['name'], ' ' * numSpaces, filePath)

                    else:
                        rewriteLine = '%s%s%s\n' % (card['name'], ' ' * numSpaces, card['value'])

                new.write(rewriteLine)

    def readProject(self, directory, projectFileName, session, spatial=False, spatialReferenceID=4236, raster2pgsqlPath='raster2pgsql'):
        """
        Read all files for a GSSHA project into the database.
        """
        # Add project file to session
        session.add(self)

        # First read self
        self.read(directory, projectFileName, session, spatial=spatial, spatialReferenceID=spatialReferenceID,
                  raster2pgsqlPath=raster2pgsqlPath)

        # Read Input Files
        self._readXput(self.INPUT_FILES, directory, session, spatial=spatial, spatialReferenceID=spatialReferenceID,
                       raster2pgsqlPath=raster2pgsqlPath)

        # Read Output Files
        self._readXput(self.OUTPUT_FILES, directory, session, spatial=spatial, spatialReferenceID=spatialReferenceID,
                       raster2pgsqlPath=raster2pgsqlPath)

        # Read Input Map Files
        self._readXputMaps(self.INPUT_MAPS, directory, session, spatial=spatial, spatialReferenceID=spatialReferenceID,
                           raster2pgsqlPath=raster2pgsqlPath)

        # Read Output Map Files
        self._readXputMaps(self.OUTPUT_MAPS, directory, session, spatial=spatial, spatialReferenceID=spatialReferenceID,
                           raster2pgsqlPath=raster2pgsqlPath)

        # Read WMS Dataset Files
        self._readWMSDatasets(self.WMS_DATASETS, directory, session, spatial=spatial, spatialReferenceID=spatialReferenceID)

        # Commit to database
        self._commit(session, self.COMMIT_ERROR_MESSAGE)

    def readInput(self, directory, projectFileName, session, spatial=False, spatialReferenceID=4236, raster2pgsqlPath='raster2pgsql'):
        """
        Read only input files for a GSSHA project into the database.
        """
        # Add project file to session
        session.add(self)

        # Read Project File
        self.read(directory, projectFileName, session, spatial, spatialReferenceID, raster2pgsqlPath)

        # Read Input Files
        self._readXput(self.INPUT_FILES, directory, session, spatial=spatial, spatialReferenceID=spatialReferenceID,
                       raster2pgsqlPath=raster2pgsqlPath)

        # Read Input Map Files
        self._readXputMaps(self.INPUT_MAPS, directory, session, spatial=spatial, spatialReferenceID=spatialReferenceID,
                           raster2pgsqlPath=raster2pgsqlPath)

        # Commit to database
        self._commit(session, self.COMMIT_ERROR_MESSAGE)

    def readOutput(self, directory, projectFileName, session, spatial=False, spatialReferenceID=4236, raster2pgsqlPath='raster2pgsql'):
        """
        Read only output files for a GSSHA project to the database.
        """
        # Add project file to session
        session.add(self)

        # Read Project File
        self.read(directory, projectFileName, session, spatial, spatialReferenceID, raster2pgsqlPath)

        # Read Output Files
        self._readXput(self.OUTPUT_FILES, directory, session, spatial=spatial, spatialReferenceID=spatialReferenceID,
                       raster2pgsqlPath=raster2pgsqlPath)

        # Read Output Map Files
        self._readXputMaps(self.OUTPUT_MAPS, directory, session, spatial=spatial, spatialReferenceID=spatialReferenceID,
                           raster2pgsqlPath=raster2pgsqlPath)

        # Commit to database
        self._commit(session, self.COMMIT_ERROR_MESSAGE)

    def writeProject(self, session, directory, name):
        """
        Write all files for a project from the database to file.


        *session* = SQLAlchemy session object\n
        *directory* = to which directory will the files be written (e.g.: '/example/path')\n
        *name* = project name (e.g.: 'my_project')\n
        """

        # Write Project File
        self.write(session=session, directory=directory, name=name)

        # Write input files
        self._writeXput(session=session, directory=directory, fileCards=self.INPUT_FILES, name=name)

        # Write output files
        self._writeXput(session=session, directory=directory, fileCards=self.OUTPUT_FILES, name=name)

        # Write input map files
        self._writeXputMaps(session=session, directory=directory, mapCards=self.INPUT_MAPS, name=name)

        # Write output map files
        self._writeXputMaps(session=session, directory=directory, mapCards=self.OUTPUT_MAPS, name=name)

        # Write WMS Dataset Files
        self._writeWMSDatasets(session=session, directory=directory, wmsDatasetCards=self.WMS_DATASETS, name=name)

    def writeInput(self, session, directory, name):
        """
        Write only input files for a GSSHA project from the database to file.


        *session* = SQLAlchemy session object\n
        *directory* = to which directory will the files be written (e.g.: '/example/path')\n
        *name* = project name (e.g.: 'my_project')\n
        """
        # Write Project File
        self.write(session=session, directory=directory, name=name)

        # Write input files
        self._writeXput(session=session, directory=directory, fileCards=self.INPUT_FILES, name=name)

        # Write input map files
        self._writeXputMaps(session=session, directory=directory, mapCards=self.INPUT_MAPS, name=name)

    def writeOutput(self, session, directory, name):
        """
        Write only output files for a GSSHA project from the database to file.


        *session* = SQLAlchemy session object\n
        *directory* = to which directory will the files be written (e.g.: '/example/path')\n
        *name* = project name (e.g.: 'my_project')\n
        """
        # Write Project File
        self.write(session=session, directory=directory, name=name)

        # Write output files
        self._writeXput(session=session, directory=directory, fileCards=self.OUTPUT_FILES, name=name)

        # Write output map files
        self._writeXputMaps(session=session, directory=directory, mapCards=self.OUTPUT_MAPS, name=name)

    def getFiles(self):
        """
        Get a list of the files that are loaded
        """
        files = {'project-file': self,
                 'mapping-table-file': self.mapTableFile,
                 'channel-input-file': self.channelInputFile,
                 'precipitation-file': self.precipFile,
                 'storm-pipe-network-file': self.stormPipeNetworkFile,
                 'hmet-file': self.hmetFile,
                 'nwsrfs-file': self.nwsrfsFile,
                 'orthographic-gage-file': self.orthoGageFile,
                 'grid-pipe-file': self.gridPipeFile,
                 'grid-stream-file': self.gridStreamFile,
                 'time-series-file': self.timeSeriesFiles,
                 'projection-file': self.projectionFile,
                 'replace-parameters-file': self.replaceParamFile,
                 'replace-value-file': self.replaceValFile,
                 'output-location-file': self.outputLocationFiles,
                 'maps': self.maps,
                 'link-node-datasets-file': self.linkNodeDatasets}

        files_list = []

        for key, value in files.iteritems():
            if value:
                files_list.append(key)

        return files_list

    def getCard(self, name):
        """
        Get the card object
        """
        cards = self.projectCards

        for card in cards:
            if card.name == name:
                return card

        return None

    def _readXput(self, fileCards, directory, session, spatial=False, spatialReferenceID=4236, raster2pgsqlPath='raster2pgsql'):
        """
        GSSHAPY Project Read Files from File Method
        """
        ## NOTE: This function is dependent on the project file being read first
        # Read Input/Output Files
        for card in self.projectCards:
            if (card.name in fileCards) and self._noneOrNumValue(card.value) and fileCards[card.name]:
                fileIO = fileCards[card.name]
                filename = card.value.strip('"')

                # Invoke read method on each file
                self._invokeRead(fileIO=fileIO,
                                 directory=directory,
                                 filename=filename,
                                 session=session,
                                 spatial=spatial,
                                 spatialReferenceID=spatialReferenceID,
                                 raster2pgsqlPath=raster2pgsqlPath)

    def _readXputMaps(self, mapCards, directory, session, spatial=False, spatialReferenceID=4236, raster2pgsqlPath='raster2pgsql'):
        """
        GSSHA Project Read Map Files from File Method
        """
        if self.mapType in self.MAP_TYPES_SUPPORTED:
            for card in self.projectCards:
                if (card.name in mapCards) and self._noneOrNumValue(card.value):
                    filename = card.value.strip('"')

                    # Invoke read method on each map
                    self._invokeRead(fileIO=RasterMapFile,
                                     directory=directory,
                                     filename=filename,
                                     session=session,
                                     spatial=spatial,
                                     spatialReferenceID=spatialReferenceID,
                                     raster2pgsqlPath=raster2pgsqlPath)
        else:
            for card in self.projectCards:
                if (card.name in mapCards) and self._noneOrNumValue(card.value):
                    filename = card.value.strip('"')
                    fileExtension = filename.split('.')[1]
                    if fileExtension in self.ALWAYS_READ_AND_WRITE_MAPS:
                        # Invoke read method on each map
                        self._invokeRead(fileIO=RasterMapFile,
                                         directory=directory,
                                         filename=filename,
                                         session=session,
                                         spatial=spatial,
                                         spatialReferenceID=spatialReferenceID,
                                         raster2pgsqlPath=raster2pgsqlPath)

            print 'WARNING: Could not read map files. MAP_TYPE', self.mapType, 'not supported.'

    def _readWMSDatasets(self, datasetCards, directory, session, spatial=False, spatialReferenceID=4236):
        """
        Method to handle the special case of WMS Dataset Files. WMS Dataset Files
        cannot be read in independently as other types of file can. They rely on
        the Mask Map file for some parameters.
        """
        if self.mapType in self.MAP_TYPES_SUPPORTED:
            # Get Mask Map dependency
            maskMap = session.query(RasterMapFile).\
                              filter(RasterMapFile.projectFile == self).\
                              filter(RasterMapFile.fileExtension == 'msk').\
                              one()

            for card in self.projectCards:
                if (card.name in datasetCards) and self._noneOrNumValue(card.value):
                    # Get filename from project file
                    filename = card.value.strip('"')

                    wmsDatasetFile = WMSDatasetFile()
                    wmsDatasetFile.projectFile = self
                    wmsDatasetFile.read(directory=directory,
                                        filename=filename,
                                        session=session,
                                        maskMap=maskMap,
                                        spatial=spatial,
                                        spatialReferenceID=spatialReferenceID)

    def _invokeRead(self, fileIO, directory, filename, session, spatial=False, spatialReferenceID=4236, raster2pgsqlPath='raster2pgsql'):
        """
        Invoke File Read Method on Other Files
        """
        instance = fileIO()
        instance.projectFile = self
        instance.read(directory, filename, session, spatial=spatial, spatialReferenceID=spatialReferenceID, raster2pgsqlPath=raster2pgsqlPath)

    def _writeXput(self, session, directory, fileCards, name=None):
        """
        GSSHA Project Write Files to File Method
        """
        for card in self.projectCards:
            if (card.name in fileCards) and self._noneOrNumValue(card.value) and fileCards[card.name]:
                fileIO = fileCards[card.name]
                filename = card.value.strip('"')

                # Determine new filename
                filename = self._replaceNewFilename(filename=filename,
                                                    name=name)

                # Invoke write method on each file
                self._invokeWrite(fileIO=fileIO,
                                  session=session,
                                  directory=directory,
                                  filename=filename)

    def _writeXputMaps(self, session, directory, mapCards, name=None):
        """
        GSSHAPY Project Write Map Files to File Method
        """
        if self.mapType in self.MAP_TYPES_SUPPORTED:
            for card in self.projectCards:
                if (card.name in mapCards) and self._noneOrNumValue(card.value):
                    filename = card.value.strip('"')

                    # Determine new filename
                    filename = self._replaceNewFilename(filename, name)

                    # Write map file
                    self._invokeWrite(fileIO=RasterMapFile,
                                      session=session,
                                      directory=directory,
                                      filename=filename)
        else:
            for card in self.projectCards:
                if (card.name in mapCards) and self._noneOrNumValue(card.value):
                    filename = card.value.strip('"')

                    fileExtension = filename.split('.')[1]

                    if fileExtension in self.ALWAYS_READ_AND_WRITE_MAPS:
                        # Determine new filename
                        filename = self._replaceNewFilename(filename, name)

                        # Write map file
                        self._invokeWrite(fileIO=RasterMapFile,
                                          session=session,
                                          directory=directory,
                                          filename=filename)

            print 'Error: Could not write map files. MAP_TYPE', self.mapType, 'not supported.'

    def _writeWMSDatasets(self, session, directory, wmsDatasetCards, name=None):
        """
        GSSHAPY Project Write WMS Datasets to File Method
        """
        if self.mapType in self.MAP_TYPES_SUPPORTED:
            for card in self.projectCards:
                if (card.name in wmsDatasetCards) and self._noneOrNumValue(card.value):
                    filename = card.value.strip('"')

                    # Determine new filename
                    filename = self._replaceNewFilename(filename, name)

                    # Handle case where fileIO interfaces with multiple files
                    # Retrieve File using FileIO and file extension
                    extension = filename.split('.')[1]

                    try:
                        wmsDataset = session.query(WMSDatasetFile). \
                            filter(WMSDatasetFile.projectFile == self). \
                            filter(WMSDatasetFile.fileExtension == extension). \
                            one()

                    except NoResultFound:
                        # Handle case when there is no file in database but the card is listed in the project file
                        print 'WARNING: {0} listed as card in project file, but the file is not found in the database.'.format(filename)

                    # Get mask map file
                    maskMap = session.query(RasterMapFile).\
                        filter(RasterMapFile.projectFile == self).\
                        filter(RasterMapFile.fileExtension == 'msk').\
                        one()

                    # Initiate Write Method on File
                    if wmsDataset is not None and maskMap is not None:
                        wmsDataset.write(session=session, directory=directory, name=filename, maskMap=maskMap)
        else:
            print 'Error: Could not write WMS Dataset files. MAP_TYPE', self.mapType, 'not supported.'

    def _invokeWrite(self, fileIO, session, directory, filename):
        """
        Invoke File Write Method on Other Files
        """
        # Default value for instance
        instance = None

        try:
            # Handle case where fileIO interfaces with single file
            # Retrieve File using FileIO
            instance = session.query(fileIO). \
                filter(fileIO.projectFile == self). \
                one()

        except:
            # Handle case where fileIO interfaces with multiple files
            # Retrieve File using FileIO and file extension
            extension = filename.split('.')[1]

            try:

                instance = session.query(fileIO). \
                    filter(fileIO.projectFile == self). \
                    filter(fileIO.fileExtension == extension). \
                    one()

            except NoResultFound:
                # Handle case when there is no file in database but the card is listed in the project file
                print 'WARNING: {0} listed as card in project file, but the file is not found in the database.'.format(filename)

        # Initiate Write Method on File
        if instance is not None:
            instance.write(session=session, directory=directory, name=filename)

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
        if name is None:
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
        """
        Check if the value of a card is none or a number.
        """
        if value:
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
        PROJECT_PATH = ('PROJECT_PATH')
        PRESERVE_DIRECTORY = ('REPLACE_FOLDER')

        # Handle special case with directory cards in
        # windows. shlex.split fails because windows 
        # directory cards end with an escape character.
        # e.g.: "this\path\ends\with\escape\"
        currLine = projectLine.strip().split()

        # Extract Card Name from the first item in the list
        cardName = currLine[0]

        if cardName in PROJECT_PATH:
            cardValue = '""'
        elif cardName in PRESERVE_DIRECTORY:
            cardValue = "{0}".format(currLine[1:])
        else:
            # TODO: Write code to handle nested directory cards
            cardValue = '""'

        return {'name': cardName, 'value': cardValue}


class ProjectCard(DeclarativeBase):
    """
    """
    __tablename__ = 'prj_project_cards'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))  #: FK

    # Value Columns
    name = Column(String, nullable=False)  #: STRING
    value = Column(String)  #: STRING

    # Relationship Properties
    projectFile = relationship('ProjectFile', back_populates='projectCards')  #: RELATIONSHIP

    def __init__(self, name, value):
        """
        Constructor
        """
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
                line = '%s%s%s\n' % (self.name, ' ' * numSpaces, self.value)
            elif originalPrefix in self.value:
                line = '%s%s%s\n' % (self.name, ' ' * numSpaces, self.value.replace(originalPrefix, newPrefix))
            else:
                line = '%s%s%s\n' % (self.name, ' ' * numSpaces, self.value)
        return line
