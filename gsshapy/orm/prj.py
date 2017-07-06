"""
********************************************************************************
* Name: ProjectFileModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from __future__ import unicode_literals

__all__ = ['ProjectFile',
           'ProjectCard']

import json
import logging
import os
import re
import sys

import numpy as np
from osgeo import ogr, osr
from pyproj import Proj, transform
from pytz import timezone
from shapely.wkb import loads as shapely_loads
import shlex
from gazar.grid import GDALGrid
from timezonefinder import TimezoneFinder
import xml.etree.ElementTree as ET

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from . import DeclarativeBase
from ..base.file_base import GsshaPyFileObjectBase
from .file_io import *
from ..util.context import tmp_chdir

log = logging.getLogger(__name__)


class ProjectFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for the Project File.

    The project file is the main configuration file for GSSHA models. As such, the project file object is different than
    most of the other file objects. In addition to providing read and write methods for the project file, a project file
    instance also provides methods for reading and writing the GSSHA project as a whole. These methods should be the
    primary interface for working with GSSHA models.

    The project file is composed of a series of cards and values. Each card in the project file is read into a
    supporting object: :class:`.ProjectCard`.

    See: http://www.gsshawiki.com/Project_File:Project_File
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
    orographicGageFileID = Column(Integer, ForeignKey('snw_orographic_gage_files.id'))  #: FK
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
    project_directory = Column(String)

    # Relationship Properties
    projectCards = relationship('ProjectCard', back_populates='projectFile')  #: RELATIONSHIP

    # Unique File Relationship Properties
    mapTableFile = relationship('MapTableFile', back_populates='projectFile')  #: RELATIONSHIP
    channelInputFile = relationship('ChannelInputFile', back_populates='projectFile')  #: RELATIONSHIP
    precipFile = relationship('PrecipFile', back_populates='projectFile')  #: RELATIONSHIP
    stormPipeNetworkFile = relationship('StormPipeNetworkFile', back_populates='projectFile')  #: RELATIONSHIP
    hmetFile = relationship('HmetFile', back_populates='projectFile')  #: RELATIONSHIP
    nwsrfsFile = relationship('NwsrfsFile', back_populates='projectFile')  #: RELATIONSHIP
    orographicGageFile = relationship('OrographicGageFile', back_populates='projectFile')  #: RELATIONSHIP
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
    projectFileEventManager = relationship('ProjectFileEventManager', uselist=False)  #: RELATIONSHIP

    # File Properties
    MAP_TYPES_SUPPORTED = (1,)
    ALWAYS_READ_AND_WRITE_MAPS = ('ele', 'msk')
    OUTPUT_DIRECTORIES_SUPPORTED = ('REPLACE_FOLDER',)

    INPUT_FILES = {'#PROJECTION_FILE': ProjectionFile,  # WMS
                   '#CHANNEL_POINT_INPUT_WMS': GenericFile,
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
                   'HMET_OROG_GAGES': OrographicGageFile,
                   'HMET_ASCII': GenericFile,
                   'GW_FLUXBOUNDTABLE': GenericFile,  # Saturated Groundwater Flow
                   'STORM_SEWER': StormPipeNetworkFile,  # Subsurface Drainage
                   'GRID_PIPE': GridPipeFile,
                   'SUPER_LINK_JUNC_LOCATION': GenericFile,
                   'SUPERLINK_NODE_LOCATION': GenericFile,
                   'OVERLAND_DEPTH_LOCATION': OutputLocationFile,  # Overland Flow (Other Output)
                   'OVERLAND_WSE_LOCATION': OutputLocationFile,
                   'OUT_WELL_LOCATION': OutputLocationFile,
                   'SIMULATION_INPUT': GenericFile,
                   '#GSSHAPY_EVENT_YML': ProjectFileEventManager,
                   }

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
                    'LAKE_OUTPUT': GenericFile,
                    'FLOOD_STREAM': LinkNodeDatasetFile,
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

    WMS_DATASETS = ('DEPTH',
                    'SNOW_SWE_FILE',
                    'DISCHARGE',
                    'INF_DEPTH',
                    'SURF_MOIS',
                    'RATE_OF_INFIL',
                    'DIS_RAIN',
                    'GW_OUTPUT',
                    'GW_RECHARGE_CUM',
                    'GW_RECHARGE_INC',
                    'FLOOD_GRID')

    # Error Messages
    COMMIT_ERROR_MESSAGE = ('Ensure the files listed in the project file '
                            'are not empty and try again.')

    def __init__(self, name=None, map_type=None, project_directory=None):
        GsshaPyFileObjectBase.__init__(self)
        self.fileExtension = 'prj'
        if name is not None:
            self.name = name
        if map_type is not None:
            self.mapType = map_type
            self.setCard(name='MAP_TYPE', value=str(map_type))
        self.project_directory = project_directory

        # object Properties
        self._tz = None # grid timezone

    def _read(self, directory, filename, session, path, name, extension,
              spatial, spatialReferenceID, replaceParamFile,
              force_relative=True):
        """
        Project File Read from File Method
        """
        self.project_directory = directory
        with tmp_chdir(directory):
            # Headers to ignore
            HEADERS = ('GSSHAPROJECT',)

            # WMS Cards to include (don't discount as comments)
            WMS_CARDS = ('#INDEXGRID_GUID', '#PROJECTION_FILE', '#LandSoil',
                         '#CHANNEL_POINT_INPUT_WMS')

            GSSHAPY_CARDS = ('#GSSHAPY_EVENT_YML', )

            with open(path, 'r') as f:
                for line in f:
                    if not line.strip():
                        # Skip empty lines
                        continue

                    elif '#' in line.split()[0] and line.split()[0] \
                            not in WMS_CARDS + GSSHAPY_CARDS:
                        # Skip comments designated by the hash symbol
                        # (with the exception of WMS_CARDS and GSSHAPY_CARDS)
                        continue

                    try:
                        card = self._extractCard(line, force_relative)

                    except:
                        card = self._extractDirectoryCard(line, force_relative)

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

    def _write(self, session, openFile, replaceParamFile):
        """
        Project File Write to File Method
        """
        # Enforce cards that must be written in certain order
        PRIORITY_CARDS = ('WMS', 'MASK_WATERSHED', 'REPLACE_LINE',
                          'REPLACE_PARAMS', 'REPLACE_VALS', 'REPLACE_FOLDER')

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
        Append directory to relative paths in project file. By default, the project file paths are read and written as
        relative paths. Use this method to prepend a directory to all the paths in the project file.

        Args:
            directory (str): Directory path to prepend to file paths in project file.
            projectFilePath (str): Path to project file that will be modified.
        """
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
                numSpaces = max(2, 25 - len(card['name']))

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

    def readProject(self, directory, projectFileName, session, spatial=False, spatialReferenceID=None):
        """
        Read all files for a GSSHA project into the database.

        This method will read all the files, both input and output files, that are supported by GsshaPy into a database.
        To use GsshaPy more efficiently, it is recommended that you use the readInput method when performing
        pre-processing tasks and readOutput when performing post-processing tasks.

        Args:
            directory (str): Directory containing all GSSHA model files. This method assumes that all files are located
                in the same directory.
            projectFileName (str): Name of the project file for the GSSHA model which will be read (e.g.: 'example.prj').
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            spatial (bool, optional): If True, spatially enabled objects will be read in as PostGIS spatial objects.
                Defaults to False.
            spatialReferenceID (int, optional): Integer id of spatial reference system for the model. If no id is
                provided GsshaPy will attempt to automatically lookup the spatial reference ID. If this process fails,
                default srid will be used (4326 for WGS 84).
        """
        self.project_directory = directory
        with tmp_chdir(directory):
            # Add project file to session
            session.add(self)

            # First read self
            self.read(directory, projectFileName, session, spatial=spatial, spatialReferenceID=spatialReferenceID)

            # Get the batch directory for output
            batchDirectory = self._getBatchDirectory(directory)

            # Automatically derive the spatial reference system, if possible
            if spatialReferenceID is None:
                spatialReferenceID = self._automaticallyDeriveSpatialReferenceId(directory)

            # Read in replace param file
            replaceParamFile = self._readReplacementFiles(directory, session, spatial, spatialReferenceID)

            # Read Input Files
            self._readXput(self.INPUT_FILES, directory, session, spatial=spatial, spatialReferenceID=spatialReferenceID, replaceParamFile=replaceParamFile)

            # Read Output Files
            self._readXput(self.OUTPUT_FILES, batchDirectory, session, spatial=spatial, spatialReferenceID=spatialReferenceID, replaceParamFile=replaceParamFile)

            # Read Input Map Files
            self._readXputMaps(self.INPUT_MAPS, directory, session, spatial=spatial, spatialReferenceID=spatialReferenceID, replaceParamFile=replaceParamFile)

            # Read WMS Dataset Files
            self._readWMSDatasets(self.WMS_DATASETS, batchDirectory, session, spatial=spatial, spatialReferenceID=spatialReferenceID)

            # Commit to database
            self._commit(session, self.COMMIT_ERROR_MESSAGE)

    def readInput(self, directory, projectFileName, session, spatial=False, spatialReferenceID=None):
        """
        Read only input files for a GSSHA project into the database.

        Use this method to read a project when only pre-processing tasks need to be performed.

        Args:
            directory (str): Directory containing all GSSHA model files. This method assumes that all files are located
                in the same directory.
            projectFileName (str): Name of the project file for the GSSHA model which will be read (e.g.: 'example.prj').
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            spatial (bool, optional): If True, spatially enabled objects will be read in as PostGIS spatial objects.
                Defaults to False.
            spatialReferenceID (int, optional): Integer id of spatial reference system for the model. If no id is
                provided GsshaPy will attempt to automatically lookup the spatial reference ID. If this process fails,
                default srid will be used (4326 for WGS 84).
        """
        self.project_directory = directory
        with tmp_chdir(directory):
            # Add project file to session
            session.add(self)

            # Read Project File
            self.read(directory, projectFileName, session, spatial, spatialReferenceID)

            # Automatically derive the spatial reference system, if possible
            if spatialReferenceID is None:
                spatialReferenceID = self._automaticallyDeriveSpatialReferenceId(directory)

            # Read in replace param file
            replaceParamFile = self._readReplacementFiles(directory, session, spatial, spatialReferenceID)

            # Read Input Files
            self._readXput(self.INPUT_FILES, directory, session, spatial=spatial, spatialReferenceID=spatialReferenceID, replaceParamFile=replaceParamFile)

            # Read Input Map Files
            self._readXputMaps(self.INPUT_MAPS, directory, session, spatial=spatial, spatialReferenceID=spatialReferenceID, replaceParamFile=replaceParamFile)

            # Commit to database
            self._commit(session, self.COMMIT_ERROR_MESSAGE)

    def readOutput(self, directory, projectFileName, session, spatial=False, spatialReferenceID=None):
        """
        Read only output files for a GSSHA project to the database.

        Use this method to read a project when only post-processing tasks need to be performed.

        Args:
            directory (str): Directory containing all GSSHA model files. This method assumes that all files are located
                in the same directory.
            projectFileName (str): Name of the project file for the GSSHA model which will be read (e.g.: 'example.prj').
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            spatial (bool, optional): If True, spatially enabled objects will be read in as PostGIS spatial objects.
                Defaults to False.
            spatialReferenceID (int, optional): Integer id of spatial reference system for the model. If no id is
                provided GsshaPy will attempt to automatically lookup the spatial reference ID. If this process fails,
                default srid will be used (4326 for WGS 84).
        """
        self.project_directory = directory
        with tmp_chdir(directory):
            # Add project file to session
            session.add(self)

            # Read Project File
            self.read(directory, projectFileName, session, spatial, spatialReferenceID)

            # Get the batch directory for output
            batchDirectory = self._getBatchDirectory(directory)

            # Read Mask (dependency of some output files)
            maskMap = WatershedMaskFile()
            maskMapFilename = self.getCard('WATERSHED_MASK').value.strip('"')
            maskMap.read(session=session, directory=directory, filename=maskMapFilename, spatial=spatial)
            maskMap.projectFile = self

            # Automatically derive the spatial reference system, if possible
            if spatialReferenceID is None:
                spatialReferenceID = self._automaticallyDeriveSpatialReferenceId(directory)

            # Read Output Files
            self._readXput(self.OUTPUT_FILES, batchDirectory, session, spatial=spatial, spatialReferenceID=spatialReferenceID)

            # Read WMS Dataset Files
            self._readWMSDatasets(self.WMS_DATASETS, batchDirectory, session, spatial=spatial, spatialReferenceID=spatialReferenceID)

            # Commit to database
            self._commit(session, self.COMMIT_ERROR_MESSAGE)

    def _readXputFile(self, file_cards, card_name, directory, session,
                      spatial=False, spatialReferenceID=None,
                      replaceParamFile=None, **kwargs):
        """
        Read specific IO file for a GSSHA project to the database.
        """
        # Automatically derive the spatial reference system, if possible
        if spatialReferenceID is None:
            spatialReferenceID = self._automaticallyDeriveSpatialReferenceId(directory)

        card = self.getCard(card_name)
        if card:
            fileIO = file_cards[card.name]
            filename = card.value.strip('"').strip("'")

            # Invoke read method on each file
            return self._invokeRead(fileIO=fileIO,
                                    directory=directory,
                                    filename=filename,
                                    session=session,
                                    spatial=spatial,
                                    spatialReferenceID=spatialReferenceID,
                                    replaceParamFile=replaceParamFile,
                                    **kwargs)

    def readInputFile(self, card_name, directory, session, spatial=False,
                      spatialReferenceID=None, **kwargs):
        """
        Read specific input file for a GSSHA project to the database.

        Args:
            card_name(str): Name of GSSHA project card.
            directory (str): Directory containing all GSSHA model files. This method assumes that all files are located
                in the same directory.
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            spatial (bool, optional): If True, spatially enabled objects will be read in as PostGIS spatial objects.
                Defaults to False.
            spatialReferenceID (int, optional): Integer id of spatial reference system for the model. If no id is
                provided GsshaPy will attempt to automatically lookup the spatial reference ID. If this process fails,
                default srid will be used (4326 for WGS 84).

        Returns:
            file object
        """
        self.project_directory = directory
        with tmp_chdir(directory):
            # Read in replace param file
            replaceParamFile = self._readReplacementFiles(directory, session, spatial, spatialReferenceID)
            return self._readXputFile(self.INPUT_FILES, card_name, directory,
                                      session, spatial, spatialReferenceID,
                                      replaceParamFile, **kwargs)

    def readOutputFile(self, card_name, directory, session, spatial=False,
                      spatialReferenceID=None, **kwargs):
        """
        Read specific input file for a GSSHA project to the database.

        Args:
            card_name(str): Name of GSSHA project card.
            directory (str): Directory containing all GSSHA model files. This method assumes that all files are located
                in the same directory.
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            spatial (bool, optional): If True, spatially enabled objects will be read in as PostGIS spatial objects.
                Defaults to False.
            spatialReferenceID (int, optional): Integer id of spatial reference system for the model. If no id is
                provided GsshaPy will attempt to automatically lookup the spatial reference ID. If this process fails,
                default srid will be used (4326 for WGS 84).

        Returns:
            file object
        """
        self.project_directory = directory
        with tmp_chdir(directory):
            return self._readXputFile(self.OUTPUT_FILES, card_name, directory,
                                      session, spatial, spatialReferenceID, **kwargs)

    def writeProject(self, session, directory, name):
        """
        Write all files for a project from the database to file.

        Use this method to write all GsshaPy supported files back into their native file formats. If writing to execute
        the model, increase efficiency by using the writeInput method to write only the file needed to run the model.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            directory (str): Directory where the files will be written.
            name (str): Name that will be given to project when written (e.g.: 'example'). Files that follow the project
                naming convention will be given this name with the appropriate extension (e.g.: 'example.prj',
                'example.cmt', and 'example.gag'). Files that do not follow this convention will retain their original
                file names.
        """
        self.project_directory = directory
        with tmp_chdir(directory):
            # Get the batch directory for output
            batchDirectory = self._getBatchDirectory(directory)

            # Get param file for writing
            replaceParamFile = self.replaceParamFile

            # Write the replacement files
            self._writeReplacementFiles(session=session, directory=directory, name=name)

            # Write Project File
            self.write(session=session, directory=directory, name=name)

            # Write input files
            self._writeXput(session=session, directory=directory, fileCards=self.INPUT_FILES, name=name, replaceParamFile=replaceParamFile)

            # Write output files
            self._writeXput(session=session, directory=batchDirectory, fileCards=self.OUTPUT_FILES, name=name)

            # Write input map files
            self._writeXputMaps(session=session, directory=directory, mapCards=self.INPUT_MAPS, name=name, replaceParamFile=replaceParamFile)

            # Write WMS Dataset Files
            self._writeWMSDatasets(session=session, directory=batchDirectory, wmsDatasetCards=self.WMS_DATASETS, name=name)

    def writeInput(self, session, directory, name):
        """
        Write only input files for a GSSHA project from the database to file.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            directory (str): Directory where the files will be written.
            name (str): Name that will be given to project when written (e.g.: 'example'). Files that follow the project
                naming convention will be given this name with the appropriate extension (e.g.: 'example.prj',
                'example.cmt', and 'example.gag'). Files that do not follow this convention will retain their original
                file names.
        """
        self.project_directory = directory
        with tmp_chdir(directory):
            # Get param file for writing
            replaceParamFile = self.replaceParamFile

            # Write Project File
            self.write(session=session, directory=directory, name=name)

            # Write input files
            self._writeXput(session=session, directory=directory, fileCards=self.INPUT_FILES, name=name, replaceParamFile=replaceParamFile)

            # Write input map files
            self._writeXputMaps(session=session, directory=directory, mapCards=self.INPUT_MAPS, name=name, replaceParamFile=replaceParamFile)



    def writeOutput(self, session, directory, name):
        """
        Write only output files for a GSSHA project from the database to file.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            directory (str): Directory where the files will be written.
            name (str): Name that will be given to project when written (e.g.: 'example'). Files that follow the project
                naming convention will be given this name with the appropriate extension (e.g.: 'example.prj',
                'example.cmt', and 'example.gag'). Files that do not follow this convention will retain their original
                file names.
        """
        self.project_directory = directory
        with tmp_chdir(directory):
            # Get the batch directory for output
            batchDirectory = self._getBatchDirectory(directory)

            # Write the replacement files
            self._writeReplacementFiles(session=session, directory=directory, name=name)

            # Write Project File
            self.write(session=session, directory=directory, name=name)

            # Write output files
            self._writeXput(session=session, directory=batchDirectory, fileCards=self.OUTPUT_FILES, name=name)

            # Write WMS Dataset Files
            self._writeWMSDatasets(session=session, directory=batchDirectory, wmsDatasetCards=self.WMS_DATASETS, name=name)

    def getFileKeys(self):
        """
        Retrieve a list of file keys that have been read into the database.

        This is a utility method that can be used to programmatically access the GsshaPy file objects. Use these keys
        in conjunction with the dictionary returned by the getFileObjects method.

        Returns:
            list: List of keys representing file objects that have been read into the database.
        """
        files = self.getFileObjects()

        files_list = []

        for key, value in files.iteritems():
            if value:
                files_list.append(key)

        return files_list

    def getFileObjects(self):
        """
        Retrieve a dictionary of file objects.

        This is a utility method that can be used to programmatically access the GsshaPy file objects. Use this method
        in conjunction with the getFileKeys method to access only files that have been read into the database.

        Returns:
            dict: Dictionary with human readable keys and values of GsshaPy file object instances. Files that have not
            been read into the database will have a value of None.
        """

        files = {'project-file': self,
                 'mapping-table-file': self.mapTableFile,
                 'channel-input-file': self.channelInputFile,
                 'precipitation-file': self.precipFile,
                 'storm-pipe-network-file': self.stormPipeNetworkFile,
                 'hmet-file': self.hmetFile,
                 'nwsrfs-file': self.nwsrfsFile,
                 'orographic-gage-file': self.orographicGageFile,
                 'grid-pipe-file': self.gridPipeFile,
                 'grid-stream-file': self.gridStreamFile,
                 'time-series-file': self.timeSeriesFiles,
                 'projection-file': self.projectionFile,
                 'replace-parameters-file': self.replaceParamFile,
                 'replace-value-file': self.replaceValFile,
                 'output-location-file': self.outputLocationFiles,
                 'maps': self.maps,
                 'link-node-datasets-file': self.linkNodeDatasets}

        return files

    def getCard(self, name):
        """
        Retrieve card object for given card name.

        Args:
            name (str): Name of card to be retrieved.

        Returns:
            :class:`.ProjectCard` or None: Project card object. Will return None if the card is not available.
        """
        cards = self.projectCards

        for card in cards:
            if card.name.upper() == name.upper():
                return card

        return None

    def setCard(self, name, value, add_quotes=False):
        """
        Adds/updates card for gssha project file

        Args:
            name (str): Name of card to be updated/added.
            value (str): Value to attach to the card.
            add_quotes (Optional[bool]): If True, will add quotes around string. Default is False.
        """
        gssha_card = self.getCard(name)

        if add_quotes:
            value = '"{0}"'.format(value)

        if gssha_card is None:
            # add new card
            new_card = ProjectCard(name=name, value=value)
            new_card.projectFile = self
        else:
            gssha_card.value = value

    def deleteCard(self, card_name, db_session):
        """
        Removes card from gssha project file
        """
        card_name = card_name.upper()
        gssha_card = self.getCard(card_name)
        if gssha_card is not None:
            db_session.delete(gssha_card)
            db_session.commit()

    def getModelSummaryAsKml(self, session, path=None, documentName=None, withStreamNetwork=True, withNodes=False, styles={}):
        """
        Retrieve a KML representation of the model. Includes polygonized mask map and vector stream network.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            path (str, optional): Path to file where KML file will be written. Defaults to None.
            documentName (str, optional): Name of the KML document. This will be the name that appears in the legend.
                Defaults to 'Stream Network'.
            withStreamNetwork (bool, optional): Include stream network. Defaults to True.
            withNodes (bool, optional): Include nodes. Defaults to False.
            styles (dict, optional): Custom styles to apply to KML geometry. Defaults to empty dictionary.

                Valid keys (styles) include:
                   * streamLineColor: tuple/list of RGBA integers (0-255) e.g.: (255, 0, 0, 128)
                   * streamLineWidth: float line width in pixels
                   * nodeIconHref: link to icon image (PNG format) to represent nodes (see: http://kml4earth.appspot.com/icons.html)
                   * nodeIconScale: scale of the icon image
                   * maskLineColor: tuple/list of RGBA integers (0-255) e.g.: (255, 0, 0, 128)
                   * maskLineWidth: float line width in pixels
                   * maskFillColor: tuple/list of RGBA integers (0-255) e.g.: (255, 0, 0, 128)

        Returns:
            str: KML string
        """
        # Get mask map
        watershedMaskCard = self.getCard('WATERSHED_MASK')
        maskFilename = watershedMaskCard.value
        maskExtension = maskFilename.strip('"').split('.')[1]

        maskMap = session.query(RasterMapFile).\
                          filter(RasterMapFile.projectFile == self).\
                          filter(RasterMapFile.fileExtension == maskExtension).\
                          one()

        # Get mask map as a KML polygon
        statement = """
                    SELECT val, ST_AsKML(geom) As polygon
                    FROM (
                    SELECT (ST_DumpAsPolygons({0})).*
                    FROM {1} WHERE id={2}
                    ) As foo
                    ORDER BY val;
                    """.format('raster', maskMap.tableName, maskMap.id)

        result = session.execute(statement)

        maskMapKmlPolygon = ''
        for row in result:
            maskMapKmlPolygon = row.polygon

        # Set Default Styles
        streamLineColorValue = (255, 255, 0, 0)  # Blue
        streamLineWidthValue = 2
        nodeIconHrefValue = 'http://maps.google.com/mapfiles/kml/paddle/red-circle.png'
        nodeIconScaleValue = 1
        maskLineColorValue = (255, 0, 0, 255)
        maskFillColorValue = (128, 64, 64, 64)
        maskLineWidthValue = 2

        # Validate
        if 'streamLineColor' in styles:
            if len(styles['streamLineColor']) < 4:
                log.warn('streamLineColor style must be a list or a tuple of '
                         'four elements representing integer RGBA values.')
            else:
                userLineColor = styles['streamLineColor']
                streamLineColorValue = (userLineColor[3], userLineColor[2], userLineColor[1], userLineColor[0])

        if 'streamLineWidth' in styles:
            try:
                float(styles['streamLineWidth'])
                streamLineWidthValue = styles['streamLineWidth']

            except ValueError:
                log.warn('streamLineWidth must be a valid '
                         'number representing the width of the line in pixels.')

        if 'nodeIconHref' in styles:
            nodeIconHrefValue = styles['nodeIconHref']

        if 'nodeIconScale' in styles:
            try:
                float(styles['nodeIconScale'])
                nodeIconScaleValue = styles['nodeIconScale']

            except ValueError:
                log.warn('nodeIconScaleValue must be a valid number representing'
                         ' the width of the line in pixels.')

        if 'maskLineColor' in styles:
            if len(styles['maskLineColor']) < 4:
                log.warn('maskLineColor style must be a list or a tuple of four '
                         'elements representing integer RGBA values.')
            else:
                userLineColor = styles['maskLineColor']
                maskLineColorValue = (userLineColor[3], userLineColor[2], userLineColor[1], userLineColor[0])

        if 'maskFillColor' in styles:
            if len(styles['maskFillColor']) < 4:
                log.warn('maskFillColor style must be a list or a tuple of four '
                         'elements representing integer RGBA values.')
            else:
                userLineColor = styles['maskFillColor']
                maskFillColorValue = (userLineColor[3], userLineColor[2], userLineColor[1], userLineColor[0])

        if 'maskLineWidth' in styles:
            try:
                float(styles['maskLineWidth'])
                maskLineWidthValue = styles['maskLineWidth']

            except ValueError:
                log.warn('maskLineWidth must be a valid number representing '
                         'the width of the line in pixels.')

        if not documentName:
            documentName = self.name

        # Initialize KML Document
        kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
        document = ET.SubElement(kml, 'Document')
        docName = ET.SubElement(document, 'name')
        docName.text = documentName

        # Mask Map
        maskPlacemark = ET.SubElement(document, 'Placemark')
        maskPlacemarkName = ET.SubElement(maskPlacemark, 'name')
        maskPlacemarkName.text = 'Mask Map'

        # Mask Styles
        maskStyles = ET.SubElement(maskPlacemark, 'Style')

        # Set polygon line style
        maskLineStyle = ET.SubElement(maskStyles, 'LineStyle')

        # Set polygon line color and width
        maskLineColor = ET.SubElement(maskLineStyle, 'color')
        maskLineColor.text = '%02X%02X%02X%02X' % maskLineColorValue
        maskLineWidth = ET.SubElement(maskLineStyle, 'width')
        maskLineWidth.text = str(maskLineWidthValue)

        # Set polygon fill color
        maskPolyStyle = ET.SubElement(maskStyles, 'PolyStyle')
        maskPolyColor = ET.SubElement(maskPolyStyle, 'color')
        maskPolyColor.text = '%02X%02X%02X%02X' % maskFillColorValue

        # Mask Geometry
        maskPolygon = ET.fromstring(maskMapKmlPolygon)
        maskPlacemark.append(maskPolygon)

        if withStreamNetwork:
            # Get the channel input file for the stream network
            channelInputFile = self.channelInputFile

            # Retrieve Stream Links
            links = channelInputFile.getFluvialLinks()

            # Stream Network
            for link in links:
                placemark = ET.SubElement(document, 'Placemark')
                placemarkName = ET.SubElement(placemark, 'name')
                placemarkName.text = 'Stream Link {0}'.format(str(link.linkNumber))

                # Create style tag and setup styles
                styles = ET.SubElement(placemark, 'Style')

                # Set line style
                lineStyle = ET.SubElement(styles, 'LineStyle')
                lineColor = ET.SubElement(lineStyle, 'color')
                lineColor.text = '%02X%02X%02X%02X' % streamLineColorValue
                lineWidth = ET.SubElement(lineStyle, 'width')
                lineWidth.text = str(streamLineWidthValue)

                # Add the geometry to placemark
                linkKML = link.getAsKml(session)
                if linkKML:
                    lineString = ET.fromstring(linkKML)
                    placemark.append(lineString)
                else:
                    log.warning("No geometry found for link with id {0}".format(link.id))

                if withNodes:
                    # Create the node styles
                    nodeStyles = ET.SubElement(document, 'Style', id='node_styles')

                    # Hide labels
                    nodeLabelStyle = ET.SubElement(nodeStyles, 'LabelStyle')
                    nodeLabelScale = ET.SubElement(nodeLabelStyle, 'scale')
                    nodeLabelScale.text = str(0)

                    # Style icon
                    nodeIconStyle = ET.SubElement(nodeStyles, 'IconStyle')

                    # Set icon
                    nodeIcon = ET.SubElement(nodeIconStyle, 'Icon')
                    iconHref = ET.SubElement(nodeIcon, 'href')
                    iconHref.text = nodeIconHrefValue

                    # Set icon scale
                    iconScale = ET.SubElement(nodeIconStyle, 'scale')
                    iconScale.text = str(nodeIconScaleValue)

                    for node in link.nodes:
                        # New placemark for each node
                        nodePlacemark = ET.SubElement(document, 'Placemark')
                        nodePlacemarkName = ET.SubElement(nodePlacemark, 'name')
                        nodePlacemarkName.text = str(node.nodeNumber)

                        # Styles for the node
                        nodeStyleUrl = ET.SubElement(nodePlacemark, 'styleUrl')
                        nodeStyleUrl.text = '#node_styles'

                        nodeString = ET.fromstring(node.getAsKml(session))
                        nodePlacemark.append(nodeString)

        kmlString = ET.tostring(kml)

        if path:
            with open(path, 'w') as f:
                f.write(kmlString)

        return kmlString

    def getModelSummaryAsWkt(self, session, withStreamNetwork=True, withNodes=False):
        """
        Retrieve a Well Known Text representation of the model. Includes polygonized mask map and vector stream network.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            withStreamNetwork (bool, optional): Include stream network. Defaults to True.
            withNodes (bool, optional): Include nodes. Defaults to False.

        Returns:
            str: Well Known Text string
        """
        # Get mask map
        watershedMaskCard = self.getCard('WATERSHED_MASK')
        maskFilename = watershedMaskCard.value
        maskExtension = maskFilename.strip('"').split('.')[1]

        maskMap = session.query(RasterMapFile).\
                          filter(RasterMapFile.projectFile == self).\
                          filter(RasterMapFile.fileExtension == maskExtension).\
                          one()

        # Get mask map as a KML polygon
        statement = """
                    SELECT val, ST_AsText(geom) As polygon
                    FROM (
                    SELECT (ST_DumpAsPolygons({0})).*
                    FROM {1} WHERE id={2}
                    ) As foo
                    ORDER BY val;
                    """.format('raster', maskMap.tableName, maskMap.id)

        result = session.execute(statement)

        maskMapTextPolygon = ''
        for row in result:
            maskMapTextPolygon = row.polygon

        # Default WKT model representation string is a geometry collection with the mask map polygon
        wktString = 'GEOMCOLLECTION ({0})'.format(maskMapTextPolygon)

        if withStreamNetwork:
            # Get the channel input file for the stream network
            channelInputFile = self.channelInputFile

            # Some models may not have streams enabled
            if channelInputFile is not None:
                # Use the existing method on the channel input file to generate the stream network WKT
                wktStreamNetwork = channelInputFile.getStreamNetworkAsWkt(session=session, withNodes=withNodes)

                # Strip off the "GEOMCOLLECTION" identifier
                wktStreamNetwork = wktStreamNetwork.replace('GEOMCOLLECTION (', '')

                # Replace the WKT model representation string with a geometry collection with mask map
                # and all stream network components
                wktString = 'GEOMCOLLECTION ({0}, {1}'.format(maskMapTextPolygon, wktStreamNetwork)

        return wktString

    def getModelSummaryAsGeoJson(self, session, withStreamNetwork=True, withNodes=False):
        """
        Retrieve a GeoJSON representation of the model. Includes vectorized mask map and stream network.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database
            withStreamNetwork (bool, optional): Include stream network. Defaults to True.
            withNodes (bool, optional): Include nodes. Defaults to False.

        Returns:
            str: GeoJSON string
        """
        # Get mask map
        watershedMaskCard = self.getCard('WATERSHED_MASK')
        maskFilename = watershedMaskCard.value
        maskExtension = maskFilename.strip('"').split('.')[1]

        maskMap = session.query(RasterMapFile).\
                          filter(RasterMapFile.projectFile == self).\
                          filter(RasterMapFile.fileExtension == maskExtension).\
                          one()

        # Get mask map as a KML polygon
        statement = """
                    SELECT val, ST_AsGeoJSON(geom) As polygon
                    FROM (
                    SELECT (ST_DumpAsPolygons({0})).*
                    FROM {1} WHERE id={2}
                    ) As foo
                    ORDER BY val;
                    """.format('raster', maskMap.tableName, maskMap.id)

        result = session.execute(statement)

        maskMapJsonPolygon = ''
        for row in result:
            maskMapJsonPolygon = row.polygon

        jsonString = maskMapJsonPolygon

        if withStreamNetwork:
            # Get the channel input file for the stream network
            channelInputFile = self.channelInputFile

            if channelInputFile is not None:
                # Use the existing method on the channel input file to generate the stream network GeoJson
                jsonStreamNetwork = channelInputFile.getStreamNetworkAsGeoJson(session=session, withNodes=withNodes)

                # Convert to json Python objects
                featureCollection = json.loads(jsonStreamNetwork)
                jsonMaskMapObjects = json.loads(maskMapJsonPolygon)

                # Create a mask feature
                maskFeature = {"type": "Feature",
                               "geometry": jsonMaskMapObjects,
                               "properties": {},
                               "id": maskMap.id}

                # Add mask map to feature collection
                tempFeatures = featureCollection['features']
                tempFeatures.append(maskFeature)
                featureCollection['features'] = tempFeatures

                # Dump to string
                jsonString = json.dumps(featureCollection)

        return jsonString

    def getGridByCard(self, gssha_card_name):
        """
        Returns GDALGrid object of GSSHA grid

        Paramters:
            gssha_card_name(str): Name of GSSHA project card for grid.

        Returns:
            GDALGrid
        """
        with tmp_chdir(self.project_directory):
            if gssha_card_name not in (self.INPUT_MAPS+self.WMS_DATASETS):
                raise ValueError("Card {0} not found in valid grid cards ..."
                                 .format(gssha_card_name))

            gssha_grid_card = self.getCard(gssha_card_name)
            if gssha_grid_card is None:
                raise ValueError("{0} card not found ...".format(gssha_card_name))

            gssha_pro_card = self.getCard("#PROJECTION_FILE")
            if gssha_pro_card is None:
                raise ValueError("#PROJECTION_FILE card not found ...")

            # return gssha grid
            return GDALGrid(gssha_grid_card.value.strip('"').strip("'"),
                            gssha_pro_card.value.strip('"').strip("'"))

    def getGrid(self, use_mask=True):
        """
        Returns GDALGrid object of GSSHA model bounds

        Paramters:
            use_mask(bool): If True, uses watershed mask. Otherwise, it uses the elevaiton grid.

        Returns:
            GDALGrid

        """
        grid_card_name = "WATERSHED_MASK"
        if not use_mask:
            grid_card_name = "ELEVATION"

        return self.getGridByCard(grid_card_name)

    def getIndexGrid(self, name):
        """
        Returns GDALGrid object of index map

        Paramters:
            name(str): Name of index map in 'cmt' file.

        Returns:
            GDALGrid
        """
        index_map = self.mapTableFile.indexMaps.filter_by(name=name).one()

        gssha_pro_card = self.getCard("#PROJECTION_FILE")
        if gssha_pro_card is None:
            raise ValueError("#PROJECTION_FILE card not found ...")

        with tmp_chdir(self.project_directory):
            # return gssha grid
            return GDALGrid(index_map.filename,
                            gssha_pro_card.value.strip('"').strip("'"))

    def getWkt(self):
        """
        Returns GSSHA projection WKT string
        """
        gssha_pro_card = self.getCard("#PROJECTION_FILE")
        if gssha_pro_card is None:
            raise ValueError("#PROJECTION_FILE card not found ...")

        with tmp_chdir(self.project_directory):
            gssha_prj_file = gssha_pro_card.value.strip('"').strip("'")
            with open(gssha_prj_file) as pro_file:
                wkt_string = pro_file.read()
            return wkt_string

    def getOutlet(self):
        """
        Gets the outlet latitude and longitude.

        Returns:
            latitude(float): Latitude of grid cell center.
            longitude(float): Longitude of grid cell center.
        """
        # OUTROW, OUTCOL
        outrow = int(self.getCard(name='OUTROW').value)-1
        outcol = int(self.getCard(name='OUTCOL').value)-1
        gssha_grid = self.getGrid()
        return gssha_grid.pixel2lonlat(outcol, outrow)

    def setOutlet(self, col, row, outslope=None):
        """
        Sets the outlet grid cell information in the project file.

        Parameters:
            col(float): 1-based column index.
            row(float): 1-based row index.
            outslope(Optional[float]): River slope at outlet.
        """
        #OUTROW, OUTCOL, OUTSLOPE
        gssha_grid = self.getGrid()
        # col, row = gssha_grid.lonlat2pixel(longitude, latitude)
        # add 1 to row & col becasue GSSHA is 1-based
        self.setCard(name='OUTROW', value=str(row))
        self.setCard(name='OUTCOL', value=str(col))
        if outslope is None:
            self.calculateOutletSlope()
        else:
            self.setCard(name='OUTSLOPE', value=str(outslope))

    def findOutlet(self, shapefile_path):
        """
        Calculate outlet location
        """
        # determine outlet from shapefile
        # by getting outlet from first point in polygon
        shapefile = ogr.Open(shapefile_path)
        source_layer = shapefile.GetLayer(0)
        source_lyr_proj = source_layer.GetSpatialRef()
        osr_geographic_proj = osr.SpatialReference()
        osr_geographic_proj.ImportFromEPSG(4326)
        proj_transform = osr.CoordinateTransformation(source_lyr_proj,
                                                      osr_geographic_proj)
        boundary_feature = source_layer.GetFeature(0)
        feat_geom = boundary_feature.GetGeometryRef()
        feat_geom.Transform(proj_transform)
        polygon = shapely_loads(feat_geom.ExportToWkb())

        # make lowest point on boundary outlet
        mask_grid = self.getGrid()
        elevation_grid = self.getGrid(use_mask=False)
        elevation_array = elevation_grid.np_array()
        ma_elevation_array = np.ma.array(elevation_array,
                                         mask=mask_grid.np_array()==0)
        min_elevation = sys.maxsize
        outlet_pt = None
        for coord in list(polygon.exterior.coords):
            try:
                col, row = mask_grid.lonlat2pixel(*coord)
            except IndexError:
                # out of bounds
                continue

            elevation_value = ma_elevation_array[row, col]
            if elevation_value is np.ma.masked:
                # search for closest value in mask to this point
                # elevation within 5 pixels in any direction
                actual_value = elevation_array[row, col]
                max_diff = sys.maxsize
                nrow = None
                ncol = None
                nval = None
                for row_ix in range(max(row-5, 0), min(row+5, mask_grid.y_size)):
                    for col_ix in range(max(col-5, 0), min(col+5, mask_grid.x_size)):
                        val = ma_elevation_array[row_ix, col_ix]
                        if not val is np.ma.masked:
                            val_diff = abs(val-actual_value)
                            if val_diff < max_diff:
                                max_diff = val_diff
                                nval = val
                                nrow = row_ix
                                ncol = col_ix

                if None not in (nrow, ncol, nval):
                    row = nrow
                    col = ncol
                    elevation_value = nval

            if elevation_value < min_elevation:
                min_elevation = elevation_value
                outlet_pt = (col, row)

        if outlet_pt is None:
            raise IndexError('No valid outlet points found on boundary ...')

        outcol, outrow = outlet_pt
        self.setOutlet(col=outcol+1, row=outrow+1)

    def calculateOutletSlope(self):
        """
        Attempt to determine the slope at the OUTLET
        """
        try:
            mask_grid = self.getGrid()
            elevation_grid = self.getGrid(use_mask=False)

            outrow = int(self.getCard("OUTROW").value)-1
            outcol = int(self.getCard("OUTCOL").value)-1
            cell_size = float(self.getCard("GRIDSIZE").value)

            min_row = max(0, outrow-1)
            max_row = min(mask_grid.x_size, outrow+2)
            min_col = max(0, outcol-1)
            max_col = min(mask_grid.y_size, outcol+2)

            mask_array = mask_grid.np_array()
            mask_array[outrow, outcol] = 0
            mask_array = mask_array[min_row:max_row, min_col:max_col]
            mask_array = (mask_array==0)

            elevation_array = elevation_grid.np_array()
            original_elevation = elevation_array[outrow, outcol]
            elevation_array = elevation_array[min_row:max_row, min_col:max_col]

            slope_calc_array = (elevation_array-original_elevation)/cell_size
            #NOTE: Ignoring distance to cells at angles. Assuming to small to matter
            mask_array[slope_calc_array<=0] = True

            slope_mask_array = np.ma.array(slope_calc_array, mask=mask_array)
            outslope = slope_mask_array.mean()
            if outslope is np.ma.masked or outslope < 0.001:
                outslope = 0.001

        except ValueError:
            outslope = 0.001

        self.setCard("OUTSLOPE", str(outslope))

    @property
    def timezone(self):
        """
        timezone of GSSHA model
        """
        if self._tz is None:
            # GET CENTROID FROM GSSHA GRID
            cen_lat, cen_lon = self.centerLatLon()
            # update time zone
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lng=cen_lon, lat=cen_lat)

            self._tz = timezone(tz_name)
        return self._tz

    def centerLatLon(self):
        """
        Get the center lat/lon of model
        """
        # GET CENTROID FROM GSSHA GRID
        gssha_grid = self.getGrid()

        min_x, max_x, min_y, max_y = gssha_grid.bounds()
        x_ext, y_ext = transform(gssha_grid.proj,
                                 Proj(init='epsg:4326'),
                                 [min_x, max_x, min_x, max_x],
                                 [min_y, max_y, max_y, min_y],
                                 )
        return np.mean(y_ext), np.mean(x_ext)

    def _automaticallyDeriveSpatialReferenceId(self, directory):
        """
        This method is used to automatically lookup the spatial reference ID of the GSSHA project. This method is a
        wrapper for the ProjectionFile class method lookupSpatialReferenceID(). It requires an internet connection
        (the lookup uses a web service) and the projection file to be present and the appropriate card in the project
        file pointing to the projection file (#PROJECTION_FILE). If the process fails, it defaults to SRID 4326 which is
        the id for WGS 84.
        """
        # Only do automatic look up if spatial reference is not specified by the user
        DEFAULT_SPATIAL_REFERENCE_ID = 4236
        # Lookup the projection card in the project file
        projectionCard = self.getCard('#PROJECTION_FILE')

        if projectionCard is not None:
            # Use lookup service
            srid = ProjectionFile.lookupSpatialReferenceID(directory=directory,
                                                           filename=projectionCard.value.strip('"'))

            try:
                # Verify the resulting srid is a number
                int(srid)
                self.srid = srid
                spatialReferenceID = srid
                log.info("Automatic spatial reference ID lookup succeded. Using id: {0}".format(spatialReferenceID))
            except:
                # Otherwise, use the default id
                spatialReferenceID = DEFAULT_SPATIAL_REFERENCE_ID
                log.warn("Automatic spatial reference ID lookup failed. Using default id: {0}".format(DEFAULT_SPATIAL_REFERENCE_ID))
        else:
            # If there is no projection card in the project file, use default
            spatialReferenceID = DEFAULT_SPATIAL_REFERENCE_ID
            log.warn("Automatic spatial reference ID lookup failed. Using default id: {0}".format(DEFAULT_SPATIAL_REFERENCE_ID))

        return spatialReferenceID

    def _getBatchDirectory(self, projectRootDirectory):
        """
        Check the project file for the REPLACE_FOLDER card. If it exists, append it's value to create the batch directory path.
        This is the directory output is written to when run in batch mode.
        """
        # Set output directory to main directory as default
        batchDirectory = projectRootDirectory

        # Get the replace folder card
        replaceFolderCard = self.getCard('REPLACE_FOLDER')

        if replaceFolderCard:
            replaceDir = replaceFolderCard.value.strip('"')
            batchDirectory = os.path.join(batchDirectory, replaceDir)

        # Create directory if it doesn't exist
        if not os.path.isdir(batchDirectory):
            os.mkdir(batchDirectory)
            log.info('Creating directory for batch output: {0}'.format(batchDirectory))

        return batchDirectory

    def _readXput(self, fileCards, directory, session, spatial=False, spatialReferenceID=4236, replaceParamFile=None):
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
                                 replaceParamFile=replaceParamFile)

    def _readXputMaps(self, mapCards, directory, session, spatial=False, spatialReferenceID=4236, replaceParamFile=None):
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
                                     replaceParamFile=replaceParamFile)
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
                                         replaceParamFile=replaceParamFile)

            log.warn('Could not read map files. '
                     'MAP_TYPE {0} not supported.'.format(self.mapType))

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
                    path = os.path.join(directory, filename)

                    if os.path.isfile(path):
                        wmsDatasetFile = WMSDatasetFile()
                        wmsDatasetFile.projectFile = self
                        wmsDatasetFile.read(directory=directory,
                                            filename=filename,
                                            session=session,
                                            maskMap=maskMap,
                                            spatial=spatial,
                                            spatialReferenceID=spatialReferenceID)
                    else:
                        self._readBatchOutputForFile(directory, WMSDatasetFile, filename, session, spatial,
                                                     spatialReferenceID, maskMap=maskMap)

    def _readReplacementFiles(self, directory, session, spatial, spatialReferenceID):
        """
        Check for the parameter replacement file cards
        (REPLACE_PARAMS and REPLACE_VALS) and read the files into
        database if they exist.

        Returns:
            replaceParamFile or None if it doesn't exist
        """
        # Set default
        replaceParamFile = None

        # Check for REPLACE_PARAMS card
        replaceParamCard = self.getCard('REPLACE_PARAMS')

        # Read the file if it exists
        if replaceParamCard is not None:
            filename = replaceParamCard.value.strip('"')
            replaceParamFile = ReplaceParamFile()
            replaceParamFile.read(directory=directory,
                                  filename=filename,
                                  session=session,
                                  spatial=spatial,
                                  spatialReferenceID=spatialReferenceID)
            replaceParamFile.projectFile = self

        # Check for the REPLACE_VALS card
        replaceValsCard = self.getCard('REPLACE_VALS')

        # Read the file if it exists
        if replaceValsCard is not None:
            filename = replaceValsCard.value.strip('"')
            replaceValsCard = ReplaceValFile()
            replaceValsCard.read(directory=directory,
                                 filename=filename,
                                 session=session,
                                 spatial=spatial,
                                 spatialReferenceID=spatialReferenceID)
            replaceValsCard.projectFile = self

        return replaceParamFile

    def _readBatchOutputForFile(self, directory, fileIO, filename, session, spatial, spatialReferenceID,
                                replaceParamFile=None, maskMap=None):
        """
        When batch mode is run in GSSHA, the files of the same type are
        prepended with an integer to avoid filename conflicts.
        This will attempt to read files in this format and
        throw warnings if the files aren't found.
        """
        # Get contents of directory
        directoryList = os.listdir(directory)

        # Compile a list of files with that include the filename in them
        batchFiles = []
        for thing in directoryList:
            if filename in thing:
                batchFiles.append(thing)

        numFilesRead = 0

        for batchFile in batchFiles:
            instance = fileIO()
            instance.projectFile = self

            if isinstance(instance, WMSDatasetFile):
                instance.read(directory=directory, filename=batchFile, session=session, maskMap=maskMap, spatial=spatial,
                              spatialReferenceID=spatialReferenceID)
            else:
                instance.read(directory, batchFile, session, spatial=spatial, spatialReferenceID=spatialReferenceID,
                              replaceParamFile=replaceParamFile)
            # Increment runCounter for next file
            numFilesRead += 1

        # Issue warnings
        if '[' in filename or ']' in filename:
            log.info('A file cannot be read, because the path to the '
                     'file in the project file has been replaced with '
                     'replacement variable {0}.'.format(filename))

        elif numFilesRead == 0:
            log.warn('{0} listed in project file, but no such '
                     'file exists.'.format(filename))

        else:
            log.info('Batch mode output detected. {0} files read '
                     'for file {1}'.format(numFilesRead, filename))

    def _invokeRead(self, fileIO, directory, filename, session, spatial=False,
                    spatialReferenceID=4236, replaceParamFile=None, **kwargs):
        """
        Invoke File Read Method on Other Files
        """
        path = os.path.join(directory, filename)

        if os.path.isfile(path):
            instance = fileIO()
            instance.projectFile = self
            instance.read(directory, filename, session, spatial=spatial,
                          spatialReferenceID=spatialReferenceID,
                          replaceParamFile=replaceParamFile, **kwargs)
            return instance
        else:
            self._readBatchOutputForFile(directory, fileIO, filename, session,
                                         spatial, spatialReferenceID, replaceParamFile)


    def _writeXput(self, session, directory, fileCards,
                   name=None, replaceParamFile=None):
        """
        GSSHA Project Write Files to File Method
        """
        for card in self.projectCards:
            if (card.name in fileCards) and self._noneOrNumValue(card.value) \
                    and fileCards[card.name]:
                fileIO = fileCards[card.name]
                filename = card.value.strip('"')

                # Check for replacement variables
                if '[' in filename or ']' in filename:
                    log.info('The file for project card {0} cannot be '
                             'written, because the path has been replaced '
                             'with replacement variable {1}.'.format(card.name, filename))
                    return

                # Determine new filename
                filename = self._replaceNewFilename(filename=filename,
                                                    name=name)

                # Invoke write method on each file
                self._invokeWrite(fileIO=fileIO,
                                  session=session,
                                  directory=directory,
                                  filename=filename,
                                  replaceParamFile=replaceParamFile)

    def _writeXputMaps(self, session, directory, mapCards,
                       name=None, replaceParamFile=None):
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
                                      filename=filename,
                                      replaceParamFile=replaceParamFile)
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
                                          filename=filename,
                                          replaceParamFile=replaceParamFile)

            log.error('Could not write map files. MAP_TYPE {0} '
                      'not supported.'.format(self.mapType))

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

                    # Get mask map file
                    maskMap = session.query(RasterMapFile).\
                        filter(RasterMapFile.projectFile == self).\
                        filter(RasterMapFile.fileExtension == 'msk').\
                        one()

                    # Default wms dataset
                    wmsDataset = None

                    try:
                        wmsDataset = session.query(WMSDatasetFile). \
                            filter(WMSDatasetFile.projectFile == self). \
                            filter(WMSDatasetFile.fileExtension == extension). \
                            one()

                    except NoResultFound:
                        # Handle case when there is no file in database but
                        # the card is listed in the project file
                        log.warn('{0} listed as card in project file, '
                                 'but the file is not found in the database.'.format(filename))

                    except MultipleResultsFound:
                        # Write all instances
                        self._invokeWriteForMultipleOfType(directory, extension,
                                                           WMSDatasetFile, filename,
                                                           session, maskMap=maskMap)
                        return

                    # Initiate Write Method on File
                    if wmsDataset is not None and maskMap is not None:
                        wmsDataset.write(session=session, directory=directory,
                                         name=filename, maskMap=maskMap)
        else:
            log.error('Could not write WMS Dataset files. '
                      'MAP_TYPE {0} not supported.'.format(self.mapType))

    def _writeReplacementFiles(self, session, directory, name):
        """
        Write the replacement files
        """
        if self.replaceParamFile:
            self.replaceParamFile.write(session=session, directory=directory,
                                        name=name)

        if self.replaceValFile:
            self.replaceValFile.write(session=session, directory=directory,
                                      name=name)

    def _invokeWriteForMultipleOfType(self, directory, extension, fileIO,
                                      filename, session, replaceParamFile=None,
                                      maskMap=None):
        # Write all instances
        instances = session.query(fileIO). \
            filter(fileIO.projectFile == self). \
            filter(fileIO.fileExtension == extension). \
            all()

        index = 0
        for index, instance in enumerate(instances):
            if instance is not None:
                # Prefix each file with an integer representing the run
                prefix = '{0:04d}_'.format(index + 1)
                prefixFilename = prefix + filename

                if isinstance(instance, WMSDatasetFile):
                    instance.write(session=session, directory=directory,
                                   name=prefixFilename, maskMap=maskMap)
                else:
                    instance.write(session=session, directory=directory,
                                   name=prefixFilename,
                                   replaceParamFile=replaceParamFile)

        log.info('Batch mode output detected. {1} files written '
                 'having extension {0}.'.format(extension, index + 1))

    def _invokeWrite(self, fileIO, session, directory, filename, replaceParamFile):
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
                # Handle case when there is no file in database but the
                # card is listed in the project file
                log.warn('{0} listed as card in project file, but '
                         'the file is not found in the database.'.format(filename))
            except MultipleResultsFound:
                self._invokeWriteForMultipleOfType(directory, extension, fileIO,
                                                   filename, session,
                                                   replaceParamFile=replaceParamFile)
                return

        # Initiate Write Method on File
        if instance is not None:
            instance.write(session=session, directory=directory, name=filename,
                           replaceParamFile=replaceParamFile)

    def _replaceNewFilename(self, filename, name):
        # Variables
        pro = False
        originalProjectName = self.name
        originalFilename = filename
        originalPrefix = originalFilename.split('.')[0]
        extension = originalFilename.split('.')[1]

        # Special case with projection file
        if '_prj' in originalPrefix:
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

        elif originalProjectName in originalPrefix:
            filename = '%s%s.%s' % (name, originalPrefix.replace(originalProjectName, ''), extension)

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

    def _extractCard(self, projectLine, force_relative=True):
        DIRECTORY_PATHS = ('REPLACE_FOLDER',)

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
                # A string will throw an exception with an attempt to
                # convert to float. In this case wrap the string
                # in double quotes.
                if cardName == 'WMS' or not force_relative:
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
                        # If the string contains a '.' it is a path: wrap in double quotes
                        cardValue = '"%s"' % pathSplit[-1]
                elif pathSplit[-1] == '':
                    # For directory cards with unix run through
                    # _extractDirectoryCard() method to extract relative
                    # path to the directory.
                    cardValue = self._extractDirectoryCard(projectLine)['value']

                elif cardName in DIRECTORY_PATHS:
                    cardValue = '"%s"' % pathSplit[-1]
                else:
                    # Else it is a card name/option don't wrap in quotes
                    cardValue = pathSplit[-1]

        # For boolean cards store None
        except:
            cardValue = None

        return {'name': cardName, 'value': cardValue}

    def _extractDirectoryCard(self, projectLine, force_relative=True):
        PROJECT_PATH = ('PROJECT_PATH')

        # Handle special case with directory cards in windows.
        # shlex.split fails because windows directory cards end
        # with an escape character. (e.g.: "this\path\ends\with\escape\")
        currLine = projectLine.strip().split()

        # Extract Card Name from the first item in the list
        cardName = currLine[0]
        preValue = currLine[1].strip('"').strip("'")

        if not force_relative:
            cardValue = preValue
        else:
            if cardName in PROJECT_PATH:
                # Project as relative is the current directory (empty string)
                cardValue = '""'
            else:
                # Pull only the last directory to make it relative
                if preValue.endswith('/'):
                    splath = preValue.split('/')
                    dirname = splath[-2]

                elif preValue.endswith('\\\\'):
                    splath = preValue.split('\\\\')
                    dirname = splath[-2]

                elif preValue.endswith('\\'):
                    splath = preValue.split('\\')
                    dirname = splath[-2]

                else:
                    dirname = os.path.basename(preValue)

                # Eliminate slashes to make it OS agnostic
                basename = dirname.replace('\\', '')
                cardValue = '"%s"' % basename.replace('/', '')

        return {'name': cardName, 'value': cardValue}


class ProjectCard(DeclarativeBase):
    """
    Object containing data for a single card in the project file.
    """
    __tablename__ = 'prj_project_cards'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))  #: FK

    # Value Columns
    name = Column(String)  #: STRING
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
        """
        Write project card to string.

        Args:
            originalPrefix (str): Original name to give to files that follow the project naming convention
                (e.g: prefix.gag).
            newPrefix (str, optional): If new prefix is desired, pass in this parameter. Defaults to None.

        Returns:
            str: Card and value as they would be written to the project file.
        """
        # Determine number of spaces between card and value for nice alignment
        numSpaces = max(2, 25 - len(self.name))

        # Handle special case of booleans
        if self.value is None:
            line = '%s\n' % self.name
        else:
            if self.name == 'WMS':
                line = '%s %s\n' % (self.name, self.value)
            elif newPrefix is None:
                line = '%s%s%s\n' % (self.name, ' ' * numSpaces, self.value)
            elif originalPrefix in self.value:
                line = '%s%s%s\n' % (self.name, ' ' * numSpaces, self.value.replace(originalPrefix, newPrefix))
            else:
                line = '%s%s%s\n' % (self.name, ' ' * numSpaces, self.value)
        return line
