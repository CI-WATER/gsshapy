'''
********************************************************************************
* Name: MappingTablesModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Enum, Float, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.idx import IndexMap
from gsshapy.lib import parsetools as pt, mapTableChunk as mtc

__all__ = ['MapTableFile',
           'MapTable',
           'MTValue',
           'MTIndex',
           'MTContaminant',
           'MTSediment']

# Controlled Vocabulary Lists
mapTableNameEnum = Enum('ROUGHNESS','INTERCEPTION','RETENTION','GREEN_AMPT_INFILTRATION',
                       'GREEN_AMPT_INITIAL_SOIL_MOISTURE','RICHARDS_EQN_INFILTRATION_BROOKS',
                       'RICHARDS_EQN_INFILTRATION_HAVERCAMP','EVAPOTRANSPIRATION','WELL_TABLE',
                       'OVERLAND_BOUNDARY','TIME_SERIES_INDEX','GROUNDWATER','GROUNDWATER_BOUNDARY',
                       'AREA_REDUCTION','WETLAND_PROPERTIES','MULTI_LAYER_SOIL','SOIL_EROSION_PROPS',
                       'CONTAMINANT_TRANSPORT','SEDIMENTS',
                       name='cmt_table_names')

varNameEnum = Enum('ROUGH','STOR_CAPY','INTER_COEF','RETENTION_DEPTH','HYDR_COND','CAPIL_HEAD',
                      'POROSITY','PORE_INDEX','RESID_SAT','FIELD_CAPACITY','WILTING_PT',
                      'SOIL_MOISTURE', 'IMPERVIOUS_AREA','HYD_COND','SOIL_MOIST','DEPTH','LAMBDA',
                      'BUB_PRESS','DELTA_Z','ALPHA','BETA','AHAV','ALBEDO','VEG_HEIGHT','V_RAD_COEF', 
                      'V_RAD_COEFF', 'CANOPY_RESIST','SPLASH_COEF', 'DETACH_COEF','DETACH_EXP',
                      'DETACH_CRIT','SED_COEF','XSEDIMENT', 'TC_COEFF','TC_INDEX','TC_CRIT','SPLASH_K',
                      'DETACH_ERODE','DETACH_INDEX', 'SED_K','DISPERSION','DECAY','UPTAKE','LOADING',
                      'GW_CONC','INIT_CONC','SW_PART','SOLUBILITY',
                      name='cmt_variable_names')

class MapTableFile(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cmt_map_table_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Relationship Properties
    mapTables = relationship('MapTable', back_populates='mapTableFile')
    projectFile = relationship('ProjectFile', uselist=False, back_populates='mapTableFile')
    
    # Global Properties
    PATH = ''
    FILENAME = ''
    DIRECTORY = ''
    SESSION = None
    EXTENSION = 'cmt'
    
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        self.FILENAME = filename
        self.DIRECTORY = directory
        self.SESSION = session
        self.PATH = '%s%s' % (self.DIRECTORY, self.FILENAME)
        
    def read(self):
        '''
        Mapping Table Read from File Method
        '''
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
        with open(self.PATH, 'r') as f:
            chunks = pt.chunk(KEYWORDS, f)
        
        # Parse chunks associated with each key    
        for key, chunkList in chunks.iteritems():
            # Parse each chunk in the chunk list
            for chunk in chunkList:
                # Call chunk specific parsers for each chunk
                result = KEYWORDS[key](key, chunk)
                
                # Index Map handler
                if key == 'INDEX_MAP':
                    # Create GSSHAPY IndexMap object from result object
                    indexMap = IndexMap(name=result['idxName'],
                                        filename=result['filename'],
                                        rasterMap=result['map'])
                    
                    # Dictionary used to map index maps to mapping tables
                    indexMaps[result['idxName']] = indexMap
                
                # Map Table Handler
                else:
                    # Create a list of all the map tables in the file
                    if result:
                        mapTables.append(result)
        
        # Create GSSHAPY ORM objects with the resulting objects that are 
        # returned from the parser functions
        self._createGsshaPyObjects(mapTables, indexMaps)
            
    def write(self, session, directory, filename):
        '''
        Map Table Write to File Method
        ''' 
                
        # Obtain a list of MTIndexMap objects
        indexMapList = []
        
        for mapTable in self.mapTables:
            if mapTable.name == 'CONTAMINANT_TRANSPORT': # Contaminant value case
                contaminantList = []
                for mtValue in mapTable.values:
                    contaminantList.append(mtValue.contaminant)
                    
                contaminants = set(contaminantList)
                for contaminant in contaminants:
                    indexMapList.append(contaminant.indexMap)
            else: # All others
                if mapTable.indexMap != None:
                    indexMapList.append(mapTable.indexMap)
        
        # Derive a set of unique MTIndexMap objects    
        indexMaps = set(indexMapList)

        # Initiate map table file and write
        fullPath = '%s%s' % (directory, filename)
        
        with open(fullPath, 'w') as cmtFile:

            # Write first line to file
            cmtFile.write('GSSHA_INDEX_MAP_TABLES\n')
            
            # Write list of index maps
            for indexMap in indexMaps:
                cmtFile.write('INDEX_MAP%s"%s" "%s"\n' % (' '*16, indexMap.filename, indexMap.name))
            
            for mapTable in self.mapTables:
                if mapTable.name == 'SEDIMENTS':
                    self._writeSedimentTable(session, cmtFile, mapTable)
                elif mapTable.name == 'CONTAMINANT_TRANSPORT':
                    self._writeContaminantTable(session, cmtFile, mapTable, contaminants)
                else:
                    self._writeMapTable(session, cmtFile, mapTable)  
    
    
    def _createGsshaPyObjects(self, mapTables, indexMaps):
        '''
        Create GSSHAPY Mapping Table ORM Objects Method
        '''
        for mt in mapTables:
            # Create GSSHAPY MapTable object
            mapTable = MapTable(name=mt['name'], 
                                numIDs=mt['numVars']['NUM_IDS'], 
                                maxNumCells=mt['numVars']['MAX_NUMBER_CELLS'], 
                                numSed=mt['numVars']['NUM_SED'],
                                numContam=mt['numVars']['NUM_CONTAM'])
            
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
                    # Initialize GSSHAPY MTContaminant object
                    contaminant = MTContaminant(name=contam['name'],
                                                outputFilename=contam['outPath'],
                                                precipConc=contam['contamVars']['PRECIP_CONC'],
                                                partition=contam['contamVars']['PARTITION'],
                                                numIDs=contam['contamVars']['NUM_IDS'])
                    
                    # Associate MTContaminant with appropriate IndexMap
                    indexMap = indexMaps[contam['indexMapName']]
                    contaminant.indexMap = indexMap
                    
                    self._createValueObjects(contam['valueList'], contam['varList'], mapTable, indexMap, contaminant)
            
            # SEDIMENTS map table handler
            elif mt['name'] == 'SEDIMENTS':
                for line in mt['valueList']:
                    # Create GSSHAPY MTSediment object
                    sediment = MTSediment(description=line[0],
                                          specificGravity=line[1],
                                          particleDiameter=line[2],
                                          outputFilename=line[3])
                    
                    # Associate the MTSediment with the MapTable
                    sediment.mapTable = mapTable
            
            # All other map table handler
            else:
                indexMap = indexMaps[mt['indexMapName']]
                
                # Create MTValue and MTIndex objects
                self._createValueObjects(mt['valueList'], mt['varList'], mapTable, indexMap, None)
    
    def _createValueObjects(self, valueList, varList, mapTable, indexMap, contaminant):
        '''
        Populate GSSHAPY MTValue and MTIndex Objects Method
        '''
        for row in valueList:
            # Create GSSHAPY MTIndex object and associate with IndexMap
            mtIndex = MTIndex(index=row['index'], description1=row['description1'], description2=row['description2'])
            mtIndex.indexMap = indexMap
                
            for i, value in enumerate(row['values']):
                # Create MTValue object and associate with MTIndex and MapTable
                mtValue = MTValue(variable=varList[i], value=float(value))
                mtValue.index = mtIndex
                mtValue.mapTable = mapTable
                
                # MTContaminant handler (associate MTValue with MTContaminant)
                if contaminant:
                    mtValue.contaminant = contaminant

    def _writeMapTable(self, session, fileObject, mapTable):
        '''
        Write Generic Map Table Method
        
        This method writes a mapping table in the generic format to file. The method will handle 
        both empty and filled cases of generic formatted mapping tables.
        
        session = SQLAlchemy session object for retrieving data from the database
        fileObject = The file object to write to
        mapTable = The GSSHAPY MapTable object to write
        '''
            
        # Write mapping name          
        fileObject.write('%s "%s"\n' % (mapTable.name, mapTable.indexMap.name))
        
        # Write mapping table global variables
        if mapTable.numIDs:
            fileObject.write('NUM_IDS %s\n' % (mapTable.numIDs))
        
        if mapTable.maxNumCells:
            fileObject.write('MAX_NUMBER_CELLS %s\n' % (mapTable.maxNumCells))
        
        if mapTable.numSed:
            fileObject.write('NUM_SED %s\n' % (mapTable.numSed))
        
        # Write value lines from the database
        self._writeValues(session, fileObject, mapTable, None)


    def _writeContaminantTable(self, session, fileObject, mapTable, contaminants):
        '''
        This method writes the contaminant transport mapping table case.
        '''        
        # Write the contaminant mapping table header
        fileObject.write('%s\n' % (mapTable.name))
        fileObject.write('NUM_CONTAM %s\n' % (mapTable.numContam))
        
        # Write out each contaminant and it's values
        for contaminant in contaminants:
            fileObject.write('"%s"  "%s"  %s\n' % (contaminant.name, contaminant.indexMap.name, contaminant.outputFilename))
            
            # Add trailing zeros to values
            precipConc = '%.2f' % contaminant.precipConc
            partition = '%.2f' % contaminant.partition
            
            # Write global variables for the contaminant
            fileObject.write('PRECIP_CONC%s%s\n' % (' '*10, precipConc))
            fileObject.write('PARTITION%s%s\n' % (' '*12, partition))
            
            # Write value lines
            self._writeValues(session, fileObject, mapTable, contaminant)
            
            
    def _writeSedimentTable(self, session, fileObject, mapTable):
        '''
        Write Sediment Mapping Table Method
        
        This method writes the sediments special mapping table case.
        '''
        
        # Write the sediment mapping table header
        fileObject.write('%s\n' % (mapTable.name))
        fileObject.write('NUM_SED %s\n' % (mapTable.numSed))
        
        # Write the value header line
        fileObject.write('Sediment Description%sSpec. Grav%sPart. Dia%sOutput Filename\n' % (' '*22, ' '*3, ' '*5))
        
        # Retrive the sediment mapping table values
        sediments = session.query(MTSediment).\
                        filter(MTSediment.mapTable == mapTable).\
                        order_by(MTSediment.id).\
                        all()
        
        # Write sediments out to file
        for sediment in sediments:
            # Determine spacing for aesthetics
            space1 = 42 - len(sediment.description)
            
            # Pad values with zeros
            specGrav = '%.6f' % sediment.specificGravity
            partDiam = '%.6f' % sediment.particleDiameter
                            
            fileObject.write('%s%s%s%s%s%s%s\n' % (sediment.description, ' '*space1, specGrav, ' '*5, partDiam, ' '*6, sediment.outputFilename))
        
    def _valuePivot(self, session, mapTable, contaminant):
        '''
        This function retrives the values of a mapping table from the database
        and pivots them into the format that is required by the mapping table
        file. This function returns a list of strings that can be printed to
        the file directly.
        '''
        # Retrieve the indices for the current mapping table and mapping table file
        indexes = session.query(MTIndex).\
                    join(MTValue.index).\
                    filter(MTValue.mapTable == mapTable).\
                    filter(MTValue.contaminant == contaminant).\
                    order_by(MTIndex.index).\
                    all()
        
        # ----------------------------------------
        # Construct each line in the mapping table
        #-----------------------------------------
        
        # All lines will be compiled into this list
        lines = []
        
        for idx in indexes:
            # Retrieve values for the current index
            values = session.query(MTValue).\
                    filter(MTValue.mapTable == mapTable).\
                    filter(MTValue.contaminant == contaminant).\
                    filter(MTValue.index == idx).\
                    order_by(MTValue.variable).\
                    order_by(MTValue.sedimentID).\
                    all() 
            
            # NOTE: The second order_by modifier in the query above
            # handles the special ordering of XSEDIMENT columns 
            # in soil erosion properties table (i.e. these columns
            # must be in the same order as the sediments in the 
            # sediments table. Accomplished by using the sedimentID
            # field). Similarly, the contaminant filter is only used 
            # in the case of the contaminant transport table. Values
            # that don't belong to a contaminant will have a contaminant
            # attribute equal to None. Compare usage of this function 
            # by _writeGeneric and _writeContaminant.
                                  
            #Value string
            valString = ''
            
            # Define valString    
            for val in values:
                # Format value with trailing zeros up to 6 digits
                numString = '%.6f' % val.value 
                valString = '%s%s%s' %(valString, numString, ' '*3)
            
            # Determine spacing for aesthetics (so each column lines up)
            spacing1 = 6 - len(str(idx.index))
            spacing2 = 40 - len(idx.description1)
            spacing3 = 40 - len(idx.description2)
            
            # Compile each mapping table line
            line = '%s%s%s%s%s%s%s\n' % (idx.index, ' '*spacing1, idx.description1, ' '*spacing2, idx.description2, ' '*spacing3, valString)
            
            # Compile each lines into a list
            lines.append(line)
        
        #-----------------------------
        # Define the value header line
        #-----------------------------
        
        # Define varString for the header line
        varString = ''
        
        # Compile list of variables (from MTValue object list) into a single string of variables
        for idx, val in enumerate(values):
            if val.variable == 'XSEDIMENT': # Special case for XSEDIMENT variable
                if idx >= len(values)-1:
                    varString = '%s%s%s%s' %(varString, mapTable.numSed, ' SEDIMENTS....', ' '*2)
            else:
                varString = '%s%s%s' %(varString, val.variable, ' '*2)
            
        # Compile the mapping table header
        header = 'ID%sDESCRIPTION1%sDESCRIPTION2%s%s\n' % (' '*4, ' '*28, ' '*28, varString)
        
        # Prepend the header line to the list of lines
        lines.insert(0, header)
        
        # Return the list of lines
        return lines
    
    def _writeValues(self, session, fileObject, mapTable, contaminant):
        
        valueLines = self._valuePivot(session, mapTable, contaminant)
            
        # Write map table value lines to file
        for valLine in valueLines:
            fileObject.write(valLine)
        
    
    
                    

class MapTable(DeclarativeBase):
    '''
    classdocs

    '''
    __tablename__ = 'cmt_map_tables'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    idxMapID = Column(Integer, ForeignKey('idx_index_maps.id'))
    mapTableFileID = Column(Integer, ForeignKey('cmt_map_table_files.id'))
    
    # Value Columns
    name = Column(mapTableNameEnum, nullable=False)
    '''Consider removing num fields in refactoring'''
    numIDs = Column(Integer)
    maxNumCells = Column(Integer)
    numSed = Column(Integer)
    numContam = Column(Integer)
    
    # Relationship Properties
    mapTableFile = relationship('MapTableFile', back_populates='mapTables')
    indexMap = relationship('IndexMap', back_populates='mapTables')
    values = relationship('MTValue', back_populates='mapTable', cascade='all, delete, delete-orphan')
    sediments = relationship('MTSediment', back_populates='mapTable', cascade='all, delete, delete-orphan')
    
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
        return '<MapTable: Name=%s, IndexMap=%s, NumIDs=%s, MaxNumCells=%s, NumSediments=%s, NumContaminants=%s>' % (
                self.name,
                self.idxMapID,
                self.numIDs,
                self.maxNumCells,
                self.numSed,
                self.numContam)
    
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
    '''
    classdocs

    '''
    __tablename__ = 'cmt_map_table_values'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    mapTableID = Column(Integer, ForeignKey('cmt_map_tables.id'), nullable=False)
    mapTableIndexID = Column(Integer, ForeignKey('cmt_indexes.id'), nullable=False)
    contaminantID = Column(Integer, ForeignKey('cmt_contaminants.id'))
    sedimentID = Column(Integer, ForeignKey('cmt_sediments.id'))
    
    # Value Columns
    variable = Column(varNameEnum, nullable=False)
    value = Column(Float, nullable=False)
    
    # Relationship Properties
    mapTable = relationship('MapTable', back_populates='values')
    index = relationship('MTIndex', back_populates='values')
    contaminant = relationship('MTContaminant', back_populates='values')
    sediment = relationship('MTSediment', back_populates='values')
    
    
    def __init__(self, variable, value=None):
        '''
        Constructor
        '''
        self.variable = variable
        self.value = value
        
    def __repr__(self):
        return '<MTValue: %s=%s>' % (self.variable, self.value)



class MTContaminant(DeclarativeBase):
    '''
    classdocs

    '''
    __tablename__ = 'cmt_contaminants'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    idxMapID = Column(Integer, ForeignKey('idx_index_maps.id'), nullable=False)
    
    # Value Columns
    name = Column(String, nullable=False)
    outputFilename = Column(String, nullable = False)
    precipConc = Column(Float, nullable=False)
    partition = Column(Float, nullable=False)
    numIDs = Column(Integer, nullable=False)

    # Relationship Properties
    indexMap = relationship('IndexMap', back_populates='contaminants')
    values = relationship('MTValue', back_populates='contaminant')
    
    def __init__(self, name, outputFilename, precipConc, partition, numIDs):
        '''
        Constructor
        '''
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


    
class MTSediment(DeclarativeBase):
    '''
    classdocs

    '''
    __tablename__ = 'cmt_sediments'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    mapTableID = Column(Integer, ForeignKey('cmt_map_tables.id'), nullable=False)
    
    # Value Columns
    description = Column(String, nullable=False)
    specificGravity = Column(Float, nullable=False)
    particleDiameter = Column(Float,nullable=False)
    outputFilename = Column(String, nullable=False)
    
    # Relationship Properties
    mapTable = relationship('MapTable', back_populates='sediments')
    values = relationship('MTValue', back_populates='sediment')
    
    def __init__(self, description, specificGravity, particleDiameter, outputFilename):
        '''
        Constructor
        '''
        self.description = description
        self.specificGravity = specificGravity
        self.particleDiameter = particleDiameter
        self.outputFilename = outputFilename
    
    def __repr__(self):
        return '<MTSediment: Description=%s, SpecificGravity=%s, ParticleDiameter=%s, OuputFilename=%s>' % (self.description, self.specificGravity, self.particleDiameter, self.outputFilename)
    
