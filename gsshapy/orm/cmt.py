"""
********************************************************************************
* Name: MappingTablesModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from __future__ import unicode_literals

__all__ = ['MapTableFile',
           'MapTable',
           'MTValue',
           'MTIndex',
           'MTContaminant',
           'MTSediment']

from io import open as io_open
import os
import logging

from future.utils import iteritems
import numpy as np
import pandas as pd
from osgeo import gdalconst
from gazar.grid import resample_grid
from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float, String
from sqlalchemy.orm import relationship

from . import DeclarativeBase
from .lnd import LinkNodeDatasetFile
from ..base.file_base import GsshaPyFileObjectBase
from .idx import IndexMap
from ..lib import parsetools as pt
from ..lib import cmt_chunk as mtc
from ..lib.parsetools import valueReadPreprocessor as vrp, valueWritePreprocessor as vwp
from ..util.context import tmp_chdir

log = logging.getLogger(__name__)


class MapTableFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for the Mapping Table File.

    Hydrological parameters are distributed spatially in GSSHA through mapping tables and index maps. Index maps are
    raster maps of integers. The mapping tables define the hydrological values for each unique index on a map. Most of the
    mapping tables are abstracted into three objects representing three different parts of the table. :class:`.MapTable`
    contains the data for the mapping table header, :class:`.MTIndex` contains the data for the indexes defined by the
    mapping table, and :class:`.MTValue` contains the actual value of the hydrological parameters defined by the mapping
    table.

    In addition, there are two special mapping tables that break the common format: Contaminant/Constituent Transport
    and Sediment Transport. The data for these mapping tables is contained in the :class:`.MTContaminant` and
    :class:`.Sediment` objects, respectively.

    The GSSHA documentation used to design this object can be found by following these links:
    http://www.gsshawiki.com/Mapping_Table:Mapping_Table_File
    """
    __tablename__ = 'cmt_map_table_files'
    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK

    # Value Columns
    fileExtension = Column(String, default='cmt')  #: STRING

    # Relationship Properties
    indexMaps = relationship('IndexMap', back_populates='mapTableFile', lazy='dynamic')  #: RELATIONSHIP
    mapTables = relationship('MapTable', back_populates='mapTableFile')  #: RELATIONSHIP
    projectFile = relationship('ProjectFile', uselist=False, back_populates='mapTableFile')  #: RELATIONSHIP

    def __init__(self, project_file=None):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)
        # add to project_file
        self.projectFile = project_file
        # Set file extension property
        self.fileExtension = 'cmt'

    def _read(self, directory, filename, session, path, name, extension,
              spatial=False, spatialReferenceID=4236, replaceParamFile=None,
              readIndexMaps=True):
        """
        Mapping Table Read from File Method
        """
        # Set file extension property
        self.fileExtension = extension

        # Dictionary of keywords/cards and parse function names
        KEYWORDS = {'INDEX_MAP': mtc.indexMapChunk,
                    'ROUGHNESS': mtc.mapTableChunk,
                    'INTERCEPTION': mtc.mapTableChunk,
                    'RETENTION': mtc.mapTableChunk,
                    'GREEN_AMPT_INFILTRATION': mtc.mapTableChunk,
                    'GREEN_AMPT_INITIAL_SOIL_MOISTURE': mtc.mapTableChunk,
                    'RICHARDS_EQN_INFILTRATION_BROOKS': mtc.mapTableChunk,
                    'RICHARDS_EQN_INFILTRATION_HAVERCAMP': mtc.mapTableChunk,
                    'EVAPOTRANSPIRATION': mtc.mapTableChunk,
                    'WELL_TABLE': mtc.mapTableChunk,
                    'OVERLAND_BOUNDARY': mtc.mapTableChunk,
                    'TIME_SERIES_INDEX': mtc.mapTableChunk,
                    'GROUNDWATER': mtc.mapTableChunk,
                    'GROUNDWATER_BOUNDARY': mtc.mapTableChunk,
                    'AREA_REDUCTION': mtc.mapTableChunk,
                    'WETLAND_PROPERTIES': mtc.mapTableChunk,
                    'MULTI_LAYER_SOIL': mtc.mapTableChunk,
                    'SOIL_EROSION_PROPS': mtc.mapTableChunk,
                    'CONTAMINANT_TRANSPORT': mtc.contamChunk,
                    'SEDIMENTS': mtc.sedimentChunk}

        indexMaps = dict()
        mapTables = []

        # Parse file into chunks associated with keywords/cards
        with io_open(path, 'r') as f:
            chunks = pt.chunk(KEYWORDS, f)

        # Parse chunks associated with each key
        for key, chunkList in iteritems(chunks):
            # Parse each chunk in the chunk list
            for chunk in chunkList:
                # Call chunk specific parsers for each chunk
                result = KEYWORDS[key](key, chunk)

                # Index Map handler
                if key == 'INDEX_MAP':

                    # Create GSSHAPY IndexMap object from result object
                    indexMap = IndexMap(name=result['idxName'])

                    # Dictionary used to map index maps to mapping tables
                    indexMaps[result['idxName']] = indexMap

                    # Associate IndexMap with MapTableFile
                    indexMap.mapTableFile = self

                    if readIndexMaps:
                        # Invoke IndexMap read method
                        indexMap.read(directory=directory, filename=result['filename'], session=session,
                                      spatial=spatial, spatialReferenceID=spatialReferenceID)
                    else:
                        # add path to file
                        indexMap.filename = result['filename']

                # Map Table handler
                else:
                    # Create a list of all the map tables in the file
                    if result:
                        mapTables.append(result)

        # Create GSSHAPY ORM objects with the resulting objects that are
        # returned from the parser functions
        self._createGsshaPyObjects(mapTables, indexMaps, replaceParamFile, directory, session, spatial, spatialReferenceID)

    def _write(self, session, openFile, replaceParamFile=None, writeIndexMaps=True):
        """
        Map Table Write to File Method
        """
        # Extract directory
        directory = os.path.split(openFile.name)[0]

        # Derive a Unique Set of Contaminants
        for mapTable in self.getOrderedMapTables(session):
            if mapTable.name == 'CONTAMINANT_TRANSPORT':
                contaminantList = []
                for mtValue in mapTable.values:
                    if mtValue.contaminant not in contaminantList:
                        contaminantList.append(mtValue.contaminant)

                contaminants = sorted(contaminantList, key=lambda x: (x.indexMap.name, x.name))

        # Write first line to file
        openFile.write('GSSHA_INDEX_MAP_TABLES\n')

        # Write list of index maps
        for indexMap in self.indexMaps:
            # Write to map table file
            openFile.write('INDEX_MAP%s"%s" "%s"\n' % (' ' * 16, indexMap.filename, indexMap.name))

            if writeIndexMaps:
                # Initiate index map write
                indexMap.write(directory, session=session)

        for mapTable in self.getOrderedMapTables(session):
            if mapTable.name == 'SEDIMENTS':
                self._writeSedimentTable(session=session,
                                         fileObject=openFile,
                                         mapTable=mapTable,
                                         replaceParamFile=replaceParamFile)
            elif mapTable.name == 'CONTAMINANT_TRANSPORT':
                self._writeContaminantTable(session=session,
                                            fileObject=openFile,
                                            mapTable=mapTable,
                                            contaminants=contaminants,
                                            replaceParamFile=replaceParamFile)
            else:
                self._writeMapTable(session=session,
                                    fileObject=openFile,
                                    mapTable=mapTable,
                                    replaceParamFile=replaceParamFile)

    def getOrderedMapTables(self, session):
        """
        Retrieve the map tables ordered by name
        """
        return session.query(MapTable).filter(MapTable.mapTableFile == self).order_by(MapTable.name).all()

    def deleteMapTable(self, name, session):
        """
        Remove duplicate map table if it exists
        """

        duplicate_map_tables = session.query(MapTable).filter(MapTable.mapTableFile == self).filter(MapTable.name == name).all()
        for duplicate_map_table in duplicate_map_tables:
            if duplicate_map_table.indexMap:
                session.delete(duplicate_map_table.indexMap)
            session.delete(duplicate_map_table)
            session.commit()

    def _createGsshaPyObjects(self, mapTables, indexMaps, replaceParamFile, directory, session, spatial, spatialReferenceID):
        """
        Create GSSHAPY Mapping Table ORM Objects Method
        """
        for mt in mapTables:
            # Create GSSHAPY MapTable object
            try:
                # Make sure the index map name listed with the map table is in the list of
                # index maps read from the top of the mapping table file (Note that the index maps for the sediment
                # and contaminant tables will have names of None, so we skip these cases.
                if mt['indexMapName'] is not None:
                    indexMaps[mt['indexMapName']]

                mapTable = MapTable(name=mt['name'],
                                    numIDs=mt['numVars']['NUM_IDS'],
                                    maxNumCells=mt['numVars']['MAX_NUMBER_CELLS'],
                                    numSed=mt['numVars'].get('NUM_SED'),
                                    numContam=mt['numVars'].get('NUM_CONTAM'),
                                    maxSoilID=mt['numVars'].get('MAX_SOIL_ID'))

                # Associate MapTable with this MapTableFile and IndexMaps
                mapTable.mapTableFile = self

                ## NOTE: Index maps are associated wth contaminants for CONTAMINANT_TRANSPORT map
                ## tables. The SEDIMENTS map table are associated with index maps via the
                ## SOIL_EROSION_PROPS map table.
                if mt['indexMapName']:
                    mapTable.indexMap = indexMaps[mt['indexMapName']]


                # CONTAMINANT_TRANSPORT map table handler
                if mt['name'] == 'CONTAMINANT_TRANSPORT':
                    for contam in mt['contaminants']:
                        # Preprocess the contaminant output paths to be relative
                        outputBaseFilename = self._preprocessContaminantOutFilePath(contam['outPath'])

                        # Initialize GSSHAPY MTContaminant object
                        contaminant = MTContaminant(name=contam['name'],
                                                    outputFilename=outputBaseFilename,
                                                    precipConc=vrp(contam['contamVars']['PRECIP_CONC'], replaceParamFile),
                                                    partition=vrp(contam['contamVars']['PARTITION'], replaceParamFile),
                                                    numIDs=contam['contamVars']['NUM_IDS'])

                        # Associate MTContaminant with appropriate IndexMap
                        indexMap = indexMaps[contam['indexMapName']]
                        contaminant.indexMap = indexMap

                        self._createValueObjects(contam['valueList'], contam['varList'], mapTable, indexMap,
                                                 contaminant, replaceParamFile)

                        # Read any output files if they are present
                        self._readContaminantOutputFiles(directory, outputBaseFilename, session, spatial, spatialReferenceID)

                # SEDIMENTS map table handler
                elif mt['name'] == 'SEDIMENTS':
                    for line in mt['valueList']:
                        # Create GSSHAPY MTSediment object
                        sediment = MTSediment(description=line[0],
                                              specificGravity=vrp(line[1], replaceParamFile),
                                              particleDiameter=vrp(line[2], replaceParamFile),
                                              outputFilename=line[3])

                        # Associate the MTSediment with the MapTable
                        sediment.mapTable = mapTable

                # All other map table handler
                else:
                    indexMap = indexMaps[mt['indexMapName']]

                    # Create MTValue and MTIndex objects
                    self._createValueObjects(mt['valueList'], mt['varList'], mapTable, indexMap, None, replaceParamFile)

            except KeyError:
                log.info(('Index Map "%s" for Mapping Table "%s" not found in list of index maps in the mapping '
                          'table file. The Mapping Table was not read into the database.') % (
                          mt['indexMapName'], mt['name']))

    def _createValueObjects(self, valueList, varList, mapTable, indexMap, contaminant, replaceParamFile):
        """
        Populate GSSHAPY MTValue and MTIndex Objects Method
        """
        def assign_values_to_table(value_list, layer_id):
            for i, value in enumerate(value_list):
                value = vrp(value, replaceParamFile)
                # Create MTValue object and associate with MTIndex and MapTable
                mtValue = MTValue(variable=varList[i], value=float(value))
                mtValue.index = mtIndex
                mtValue.mapTable = mapTable
                mtValue.layer_id = layer_id

                # MTContaminant handler (associate MTValue with MTContaminant)
                if contaminant:
                    mtValue.contaminant = contaminant

        for row in valueList:
            # Create GSSHAPY MTIndex object and associate with IndexMap
            mtIndex = MTIndex(index=row['index'], description1=row['description1'], description2=row['description2'])
            mtIndex.indexMap = indexMap
            if len(np.shape(row['values'])) == 2:
                # this is for ids with multiple layers
                for layer_id, values in enumerate(row['values']):
                    assign_values_to_table(values, layer_id)
            else:
                assign_values_to_table(row['values'], 0)

    def _readContaminantOutputFiles(self, directory, baseFileName, session, spatial, spatialReferenceID):
        """
        Read any contaminant output files if available
        """
        if not os.path.isdir(directory):
            return
        if baseFileName == '':
            return

        # Look for channel output files denoted by the ".chan" after the base filename
        chanBaseFileName = '.'.join([baseFileName, 'chan'])

        # Get contents of directory
        directoryList = os.listdir(directory)

        # Compile a list of files with "basename.chan" in them
        chanFiles = []
        for thing in directoryList:
            if chanBaseFileName in thing:
                chanFiles.append(thing)

        # Assume all "chan" files are link node dataset files and try to read them
        for chanFile in chanFiles:
            linkNodeDatasetFile = LinkNodeDatasetFile()
            linkNodeDatasetFile.projectFile = self.projectFile

            try:
                linkNodeDatasetFile.read(directory=directory,
                                         filename=chanFile,
                                         session=session,
                                         spatial=spatial,
                                         spatialReferenceID=spatialReferenceID)
            except:
                log.warning('Attempted to read Contaminant Transport Output file {0}, but failed.'.format(chanFile))

    def _writeMapTable(self, session, fileObject, mapTable, replaceParamFile):
        """
        Write Generic Map Table Method

        This method writes a mapping table in the generic format to file. The method will handle
        both empty and filled cases of generic formatted mapping tables.

        session = SQLAlchemy session object for retrieving data from the database
        fileObject = The file object to write to
        mapTable = The GSSHAPY MapTable object to write
        """

        # Write mapping name
        fileObject.write('%s "%s"\n' % (mapTable.name, mapTable.indexMap.name))

        # Write mapping table global variables
        if mapTable.numIDs:
            fileObject.write('NUM_IDS %s\n' % (mapTable.numIDs))

        if mapTable.maxNumCells:
            fileObject.write('MAX_NUMBER_CELLS %s\n' % (mapTable.maxNumCells))

        if mapTable.numSed:
            fileObject.write('NUM_SED %s\n' % (mapTable.numSed))

        if mapTable.maxSoilID:
            fileObject.write('MAX_SOIL_ID %s\n' % (mapTable.maxSoilID))

        # Write value lines from the database
        self._writeValues(session, fileObject, mapTable, None, replaceParamFile)


    def _writeContaminantTable(self, session, fileObject, mapTable, contaminants, replaceParamFile):
        """
        This method writes the contaminant transport mapping table case.
        """
        # Write the contaminant mapping table header
        fileObject.write('%s\n' % (mapTable.name))
        fileObject.write('NUM_CONTAM %s\n' % (mapTable.numContam))

        # Write out each contaminant and it's values
        for contaminant in contaminants:
            fileObject.write(
                '"%s"  "%s"  %s\n' % (contaminant.name, contaminant.indexMap.name, contaminant.outputFilename))

            # Add trailing zeros to values / replacement parameter
            precipConcString = vwp(contaminant.precipConc, replaceParamFile)
            partitionString = vwp(contaminant.partition, replaceParamFile)
            try:
                precipConc = '%.2f' % precipConcString
            except:
                precipConc = '%s' % precipConcString

            try:
                partition = '%.2f' % partitionString
            except:
                partition = '%s' % partitionString

            # Write global variables for the contaminant
            fileObject.write('PRECIP_CONC%s%s\n' % (' ' * 10, precipConc))
            fileObject.write('PARTITION%s%s\n' % (' ' * 12, partition))
            fileObject.write('NUM_IDS %s\n' % contaminant.numIDs)

            # Write value lines
            self._writeValues(session, fileObject, mapTable, contaminant, replaceParamFile)


    def _writeSedimentTable(self, session, fileObject, mapTable, replaceParamFile):
        """
        Write Sediment Mapping Table Method

        This method writes the sediments special mapping table case.
        """

        # Write the sediment mapping table header
        fileObject.write('%s\n' % (mapTable.name))
        fileObject.write('NUM_SED %s\n' % (mapTable.numSed))

        # Write the value header line
        fileObject.write(
            'Sediment Description%sSpec. Grav%sPart. Dia%sOutput Filename\n' % (' ' * 22, ' ' * 3, ' ' * 5))

        # Retrive the sediment mapping table values
        sediments = session.query(MTSediment). \
            filter(MTSediment.mapTable == mapTable). \
            order_by(MTSediment.id). \
            all()

        # Write sediments out to file
        for sediment in sediments:
            # Determine spacing for aesthetics
            space1 = 42 - len(sediment.description)

            # Pad values with zeros / Get replacement variable
            specGravString = vwp(sediment.specificGravity, replaceParamFile)
            partDiamString = vwp(sediment.particleDiameter, replaceParamFile)

            try:
                specGrav = '%.6f' % specGravString
            except:
                specGrav = '%s' % specGravString

            try:
                partDiam = '%.6f' % partDiamString
            except:
                partDiam = '%s' % partDiamString


            fileObject.write('%s%s%s%s%s%s%s\n' % (
                sediment.description, ' ' * space1, specGrav, ' ' * 5, partDiam, ' ' * 6, sediment.outputFilename))

    def _valuePivot(self, session, mapTable, contaminant, replaceParaFile):
        """
        This function retrieves the values of a mapping table from the database and pivots them into the format that is
        required by the mapping table file. This function returns a list of strings that can be printed to the file
        directly.
        """
        # Retrieve the indices for the current mapping table and mapping table file
        indexes = session.query(MTIndex). \
            join(MTValue.index). \
            filter(MTValue.mapTable == mapTable). \
            filter(MTValue.contaminant == contaminant). \
            order_by(MTIndex.index). \
            all()

        # determine number of layers
        layer_indices = [0]
        if mapTable.name in ('MULTI_LAYER_SOIL', 'RICHARDS_EQN_INFILTRATION_BROOKS'):
            layer_indices = range(3)

        # ----------------------------------------
        # Construct each line in the mapping table
        #-----------------------------------------

        # All lines will be compiled into this list
        lines = []
        values = {}
        for idx in indexes:
            for layer_index in layer_indices:
                # Retrieve values for the current index
                values = session.query(MTValue). \
                         filter(MTValue.mapTable == mapTable). \
                         filter(MTValue.contaminant == contaminant). \
                         filter(MTValue.index == idx). \
                         filter(MTValue.layer_id == layer_index). \
                         order_by(MTValue.id). \
                         all()

                # NOTE: The second order_by modifier in the query above handles the special ordering of XSEDIMENT columns
                # in soil erosion properties table (i.e. these columns must be in the same order as the sediments in the
                # sediments table. Accomplished by using the sedimentID field). Similarly, the contaminant filter is only
                # used in the case of the contaminant transport table. Values that don't belong to a contaminant will have
                # a contaminant attribute equal to None. Compare usage of this function by _writeMapTable and
                # _writeContaminant.

                #Value string
                valString = ''

                # Define valString
                for val in values:
                    if val.value <= -9999:
                        continue
                    # Format value with trailing zeros up to 6 digits
                    processedValue = vwp(val.value, replaceParaFile)
                    try:
                        numString = '%.6f' % processedValue
                    except:
                        numString = '%s' % processedValue

                    valString = '%s%s%s' % (valString, numString, ' ' * 3)

                # Determine spacing for aesthetics (so each column lines up)
                spacing1 = max(1, 6 - len(str(idx.index)))
                spacing2 = max(1, 40 - len(idx.description1))
                spacing3 = max(1, 40 - len(idx.description2))

                # Compile each mapping table line
                if layer_index == 0:
                    line = '%s%s%s%s%s%s%s\n' % (
                        idx.index, ' ' * spacing1, idx.description1, ' ' * spacing2, idx.description2, ' ' * spacing3, valString)
                else:
                    num_prepend_spaces = len(str(idx.index)) + spacing1 + len(idx.description1) \
                                         + spacing2 + len(idx.description2) + spacing3
                    line = '{0}{1}\n'.format(' ' * num_prepend_spaces, valString)

                # Compile each lines into a list
                lines.append(line)

        #-----------------------------
        # Define the value header line
        #-----------------------------

        # Define varString for the header line
        varString = ''

        # Compile list of variables (from MTValue object list) into a single string of variables
        for idx, val in enumerate(values):
            if val.variable == 'XSEDIMENT':  # Special case for XSEDIMENT variable
                if idx >= len(values) - 1:
                    varString = '%s%s%s%s' % (varString, mapTable.numSed, ' SEDIMENTS....', ' ' * 2)
            else:
                varString = '%s%s%s' % (varString, val.variable, ' ' * 2)

        # Compile the mapping table header
        header = 'ID%sDESCRIPTION1%sDESCRIPTION2%s%s\n' % (' ' * 4, ' ' * 28, ' ' * 28, varString)

        # Prepend the header line to the list of lines
        lines.insert(0, header)

        # Return the list of lines
        return lines

    def _writeValues(self, session, fileObject, mapTable, contaminant, replaceParamFile):

        valueLines = self._valuePivot(session, mapTable, contaminant, replaceParamFile)

        # Write map table value lines to file
        for valLine in valueLines:
            fileObject.write(valLine)

    @staticmethod
    def _preprocessContaminantOutFilePath(outPath):
        """
        Preprocess the contaminant output file path to a relative path.
        """
        if '/' in outPath:
            splitPath = outPath.split('/')

        elif '\\' in outPath:
            splitPath = outPath.split('\\')

        else:
            splitPath = [outPath, ]

        if splitPath[-1] == '':
            outputFilename = splitPath[-2]

        else:
            outputFilename = splitPath[-1]

        if '.' in outputFilename:
            outputFilename = outputFilename.split('.')[0]

        return outputFilename

    def addRoughnessMapFromLandUse(self, name,
                                         session,
                                         land_use_grid,
                                         land_use_to_roughness_table=None,
                                         land_use_grid_id=None,

                                         ):
        """
        Adds a roughness map from land use file

        Example::

            from gsshapy.orm import ProjectFile
            from gsshapy.lib import db_tools as dbt

            from os import path, chdir

            gssha_directory = '/gsshapy/tests/grid_standard/gssha_project'
            land_use_grid = 'LC_5min_global_2012.tif'
            land_use_to_roughness_table = ''/gsshapy/gridtogssha/land_cover/land_cover_glcf_modis.txt'

            # Create Test DB
            sqlalchemy_url, sql_engine = dbt.init_sqlite_memory()

            # Create DB Sessions
            db_session = dbt.create_session(sqlalchemy_url, sql_engine)

            # Instantiate GSSHAPY object for reading to database
            project_manager = ProjectFile()

            # Call read method
            project_manager.readInput(directory=gssha_directory,
                                      projectFileName='grid_standard.prj',
                                      session=db_session)

            project_manager.mapTableFile.addRoughnessMapFromLandUse("roughness",
                                                                    db_session,
                                                                    land_use_to_roughness_table,
                                                                    land_use_grid,
                                                                    )
            # WRITE OUT UPDATED GSSHA PROJECT FILE
            project_manager.writeInput(session=db_session,
                                       directory=gssha_directory,
                                       name='grid_standard')

        """
        LAND_USE_GRID_TABLES = {
                                 'nga'  : 'land_cover_nga.txt',
                                 'glcf' : 'land_cover_glcf_modis.txt',
                                 'nlcd' : 'land_cover_nlcd.txt',
                                }

        # read in table
        if isinstance(land_use_to_roughness_table, pd.DataFrame):
            df = land_use_to_roughness_table
        else:
            if land_use_to_roughness_table is None:
                if land_use_grid_id is None:
                    raise ValueError("Must have land_use_to_roughness_table or land_use_grid_id set ...")

                land_use_to_roughness_table = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                           '..', 'grid',
                                                           'land_cover',
                                                           LAND_USE_GRID_TABLES[land_use_grid_id])

            # make sure paths are absolute as the working directory changes
            land_use_to_roughness_table = os.path.abspath(land_use_to_roughness_table)

            df = pd.read_table(land_use_to_roughness_table, delim_whitespace=True,
                               header=None, skiprows=1,
                               names=('id', 'description', 'roughness'),
                               dtype={'id':'int', 'description':'str', 'roughness':'float'},
                               )

        # make sure paths are absolute as the working directory changes
        land_use_grid = os.path.abspath(land_use_grid)

        # resample land use grid to gssha grid
        land_use_resampled = resample_grid(land_use_grid,
                                           self.projectFile.getGrid(),
                                           resample_method=gdalconst.GRA_NearestNeighbour,
                                           as_gdal_grid=True)

        unique_land_use_ids = np.unique(land_use_resampled.np_array())

        # only add ids in index map subset
        df = df[df.id.isin(unique_land_use_ids)]

        # make sure all needed land use IDs exist
        for land_use_id in unique_land_use_ids:
            if land_use_id not in df.id.values:
                raise IndexError("Land use ID {0} not found in table.".format(land_use_id))

        # delete duplicate/old tables with same name if they exist
        self.deleteMapTable("ROUGHNESS", session)

        # get num ids
        mapTable = MapTable(name="ROUGHNESS",
                            numIDs=len(df.index),
                            maxNumCells=0,
                            numSed=0,
                            numContam=0)

        # Create GSSHAPY IndexMap object from result object
        indexMap = IndexMap(name=name)
        indexMap.mapTableFile = self
        mapTable.indexMap = indexMap

        # Associate MapTable with this MapTableFile and IndexMaps
        mapTable.mapTableFile = self
        # add values to table
        for row in df.itertuples():
            idx = MTIndex(str(row.id), row.description, '')
            idx.indexMap = indexMap
            val = MTValue('ROUGH', row.roughness)
            val.index = idx
            val.mapTable = mapTable

        # remove MANNING_N card becasue it is mutually exclusive
        manningn_card = self.projectFile.getCard('MANNING_N')
        if manningn_card:
            session.delete(manningn_card)
            session.commit()

        mapTable.indexMap.filename = '{0}.idx'.format(name)
        # write file
        with tmp_chdir(self.projectFile.project_directory):
            land_use_resampled.to_grass_ascii(mapTable.indexMap.filename,
                                              print_nodata=False)

        # update project card
        if not self.projectFile.getCard('MAPPING_TABLE'):
            self.projectFile.setCard('MAPPING_TABLE',
                                     '{0}.cmt'.format(self.projectFile.name),
                                     add_quotes=True)

class MapTable(DeclarativeBase):
    """
    Object containing header data for a mapping table.

    See: http://www.gsshawiki.com/Mapping_Table:Mapping_Tables
         http://www.gsshawiki.com/Mapping_Table:Index_Maps
    """
    __tablename__ = 'cmt_map_tables'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    idxMapID = Column(Integer, ForeignKey('idx_index_maps.id'))  #: FK
    mapTableFileID = Column(Integer, ForeignKey('cmt_map_table_files.id'))  #: FK

    # Value Columns
    name = Column(String)  #: STRING
    numIDs = Column(Integer)  #: INTEGER
    maxNumCells = Column(Integer)  #: INTEGER
    numSed = Column(Integer)  #: INTEGER
    numContam = Column(Integer)  #: INTEGER
    maxSoilID = Column(Integer)

    # Relationship Properties
    mapTableFile = relationship('MapTableFile', back_populates='mapTables')  #: RELATIONSHIP
    indexMap = relationship('IndexMap', back_populates='mapTables')  #: RELATIONSHIP
    values = relationship('MTValue', back_populates='mapTable', cascade='all, delete, delete-orphan')  #: RELATIONSHIP
    sediments = relationship('MTSediment', back_populates='mapTable',
                             cascade='all, delete, delete-orphan')  #: RELATIONSHIP

    def __init__(self, name, numIDs=None, maxNumCells=None, numSed=None, numContam=None, maxSoilID=None):
        """
        Constructor
        """
        self.name = name
        self.numIDs = numIDs
        self.maxNumCells = maxNumCells
        self.numSed = numSed
        self.numContam = numContam
        self.maxSoilID = maxSoilID

    def __repr__(self):
        return '<MapTable: Name=%s, IndexMap=%s, NumIDs=%s, MaxNumCells=%s, NumSediments=%s, NumContaminants=%s, MaxSoilID=%s>' % (
            self.name,
            self.idxMapID,
            self.numIDs,
            self.maxNumCells,
            self.numSed,
            self.numContam,
            self.maxSoilID)

    def __eq__(self, other):
        return (self.name == other.name and
                self.numIDs == other.numIDs and
                self.maxNumCells == other.maxNumCells and
                self.numSed == other.numSed and
                self.numContam == other.numContam and
                self.maxSoilID == other.maxSoilID)


class MTIndex(DeclarativeBase):
    """
    Object containing mapping table index data. Mapping table index objects link the mapping table values to index maps.

    See: http://www.gsshawiki.com/Mapping_Table:Mapping_Tables
    """
    __tablename__ = 'cmt_indexes'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    idxMapID = Column(Integer, ForeignKey('idx_index_maps.id'))  #: FK

    # Value Columns
    index = Column(Integer)  #: INTEGER
    description1 = Column(String(40))  #: STRING
    description2 = Column(String(40))  #: STRING

    # Relationship Properties
    values = relationship('MTValue', back_populates='index')  #: RELATIONSHIP
    indexMap = relationship('IndexMap', back_populates='indices')  #: RELATIONSHIP

    def __init__(self, index, description1='', description2=''):
        """
        Constructor
        """
        self.index = index
        self.description1 = description1
        self.description2 = description2

    def __repr__(self):
        return '<MTIndex: Index=%s, Description1=%s, Description2=%s>' % (
            self.index, self.description1, self.description2)

    def __eq__(self, other):
        return (self.index == other.index and
                self.description1 == other.description1 and
                self.description2 == other.description2)


class MTValue(DeclarativeBase):
    """
    Object containing the hydrological variable and value data for mapping tables.

    See: http://www.gsshawiki.com/Mapping_Table:Mapping_Tables
    """
    __tablename__ = 'cmt_map_table_values'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    mapTableID = Column(Integer, ForeignKey('cmt_map_tables.id'))  #: FK
    mapTableIndexID = Column(Integer, ForeignKey('cmt_indexes.id'))  #: FK
    contaminantID = Column(Integer, ForeignKey('cmt_contaminants.id'))  #: FK

    # Value Columns
    variable = Column(String)  #: STRING
    value = Column(Float)  #: FLOAT
    layer_id = Column(Integer, default=0) # for tables with multiple layers

    # Relationship Properties
    mapTable = relationship('MapTable', back_populates='values')  #: RELATIONSHIP
    index = relationship('MTIndex', back_populates='values')  #: RELATIONSHIP
    contaminant = relationship('MTContaminant', back_populates='values')  #: RELATIONSHIP

    def __init__(self, variable, value=None):
        """
        Constructor
        """
        self.variable = variable
        self.value = value

    def __repr__(self):
        return '<MTValue: %s=%s>' % (self.variable, self.value)

    def __eq__(self, other):
        return (self.variable == other.variable and
                self.value == other.value)


class MTContaminant(DeclarativeBase):
    """
    Object containing data in contaminant transport type mapping tables.

    See: http://www.gsshawiki.com/Mapping_Table:Constituent_Mapping_Tables
    """
    __tablename__ = 'cmt_contaminants'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    idxMapID = Column(Integer, ForeignKey('idx_index_maps.id'))  #: FK

    # Value Columns
    name = Column(String)  #: STRING
    outputFilename = Column(String)  #: STRING
    precipConc = Column(Float)  #: FLOAT
    partition = Column(Float)  #: FLOAT
    numIDs = Column(Integer)  #: INTEGER

    # Relationship Properties
    indexMap = relationship('IndexMap', back_populates='contaminants')  #: RELATIONSHIP
    values = relationship('MTValue', back_populates='contaminant')  #: RELATIONSHIP

    def __init__(self, name, outputFilename, precipConc, partition, numIDs):
        """
        Constructor
        """
        self.name = name
        self.outputFilename = outputFilename
        self.precipConc = precipConc
        self.partition = partition
        self.numIDs = numIDs

    def __repr__(self):
        return '<MTContaminant: Name=%s, Precipitation Concentration=%s, Partition=%s, OutputFilename=%s, NumIDs=%s>' % (
            self.name,
            self.precipConc,
            self.partition,
            self.outputFilename,
            self.numIDs)

    def __eq__(self, other):
        return (self.name == other.name and
                self.outputFilename == other.outputFilename and
                self.precipConc == other.precipConc and
                self.partition == other.partition and
                self.numIDs == other.numIDs)


class MTSediment(DeclarativeBase):
    """
    Object containing data in sediment transport type mapping tables.

    See: http://www.gsshawiki.com/Mapping_Table:Sediment_Erosion_Mapping_Tables
    """
    __tablename__ = 'cmt_sediments'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    mapTableID = Column(Integer, ForeignKey('cmt_map_tables.id'))  #: FK

    # Value Columns
    description = Column(String)  #: STRING
    specificGravity = Column(Float)  #: FLOAT
    particleDiameter = Column(Float)  #: FLOAT
    outputFilename = Column(String)  #: STRING

    # Relationship Properties
    mapTable = relationship('MapTable', back_populates='sediments')  #: RELATIONSHIP

    def __init__(self, description, specificGravity, particleDiameter, outputFilename):
        """
        Constructor
        """
        self.description = description
        self.specificGravity = specificGravity
        self.particleDiameter = particleDiameter
        self.outputFilename = outputFilename

    def __repr__(self):
        return '<MTSediment: Description=%s, SpecificGravity=%s, ParticleDiameter=%s, OutputFilename=%s>' % (
            self.description, self.specificGravity, self.particleDiameter, self.outputFilename)

    def __eq__(self, other):
        return (self.description == other.description and
                self.specificGravity == other.specificGravity and
                self.particleDiameter == other.particleDiameter and
                self.outputFilename == other.outputFilename)
