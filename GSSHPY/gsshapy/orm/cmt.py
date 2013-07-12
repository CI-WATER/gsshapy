'''
********************************************************************************
* Name: MappingTablesModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['MapTableFile',
           'MapTable',
           'MTValue',
           'MTIndex',
           'MTContaminant',
           'MTSediment']

from sqlalchemy import ForeignKey, Column, Table
from sqlalchemy.types import Integer, Enum, Float, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase, metadata

# Controlled Vocabulary Lists
mapTableNameEnum = Enum('ROUGHNESS','INTERCEPTION','RETENTION','GREEN_AMPT_INFILTRATION',\
                       'GREEN_AMPT_INITIAL_SOIL_MOISTURE','RICHARDS_EQN_INFILTRATION_BROOKS',\
                       'RICHARDS_EQN_INFILTRATION_HAVERCAMP','EVAPOTRANSPIRATION','WELL_TABLE',\
                       'OVERLAND_BOUNDARY','TIME_SERIES_INDEX','GROUNDWATER','GROUNDWATER_BOUNDARY',\
                       'AREA_REDUCTION','WETLAND_PROPERTIES','MULTI_LAYER_SOIL','SOIL_EROSION_PROPS',\
                       'CONTAMINANT_TRANSPORT','SEDIMENTS',\
                       name='cmt_table_names')

varNameEnum = Enum('ROUGH','STOR_CAPY','INTER_COEF','RETENTION_DEPTH','HYDR_COND','CAPIL_HEAD',\
                      'POROSITY','PORE_INDEX','RESID_SAT','FIELD_CAPACITY','WILTING_PT','SOIL_MOISTURE',\
                      'IMPERVIOUS_AREA','HYD_COND','SOIL_MOIST','DEPTH','LAMBDA',\
                      'BUB_PRESS','DELTA_Z','ALPHA','BETA','AHAV','ALBEDO','VEG_HEIGHT','V_RAD_COEFF',\
                      'CANOPY_RESIST','SPLASH_COEF', 'DETACH_COEF','DETACH_EXP','DETACH_CRIT','SED_COEF','XSEDIMENT',\
                      'TC_COEFF','TC_INDEX','TC_CRIT','SPLASH_K','DETACH_ERODE','DETACH_INDEX',\
                      'SED_K','DISPERSION','DECAY','UPTAKE','LOADING','GW_CONC','INIT_CONC',\
                      'SW_PART','SOLUBILITY',\
                      name='cmt_variable_names')

# Association table for many-to-many relationship between MapTableFile and MTValue
assocMapTable = Table('assoc_map_table_files_values', metadata,
    Column('mapTableFileID', Integer, ForeignKey('cmt_map_table_files.id')),
    Column('mapTableValueID', Integer, ForeignKey('cmt_map_table_values.id'))
    )

assocSediment = Table('assoc_map_table_files_sediments', metadata,
    Column('mapTableFileID', Integer, ForeignKey('cmt_map_table_files.id')),
    Column('sedimentID', Integer, ForeignKey('cmt_sediments.id'))
    )

class MapTableFile(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'cmt_map_table_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    
    # Relationship Properties
    mapTableValues = relationship('MTValue', secondary=assocMapTable, back_populates='mapTableFiles')
    mapTableSediments = relationship('MTSediment', secondary=assocSediment, back_populates='mapTableFiles')
    
    def __init__(self):
        '''
        Constructor
        '''
        
    def __repr__(self):
        return '<MapTableFile>'
    
    
    
    def _writeGeneric(self, session, fileObject, mapTableName):
        '''
        This method writes a mapping table in the generic format to file. The method will handle 
        both empty and filled cases of generic formatted mapping tables.
        '''
        # Try retreiving the data for the table with the current name. On exception the table is not
        # being used by this project file it will write an empty version.
        try:
            # Retrieve the current mapping table (This will fail if it is not used by this mapping table file)
            currentMapTable = session.query(MapTable).\
                                join(MTValue.mapTable).\
                                filter(MTValue.mapTableFiles.contains(self)).\
                                filter(MapTable.name == mapTableName).\
                                one()
            
            # Write mapping name          
            fileObject.write('%s "%s"\n' % (currentMapTable.name, currentMapTable.indexMap.name))
            
            # Write mappting table global variables
            if currentMapTable.numIDs != None:
                fileObject.write('NUM_IDS %s\n' % (currentMapTable.numIDs))
            
            if currentMapTable.maxNumCells != None:
                fileObject.write('MAX_NUMBER_CELLS %s\n' % (currentMapTable.maxNumCells))
            
            if currentMapTable.numSed != None:
                fileObject.write('NUM_SED %s\n' % (currentMapTable.numSed))
                
            if currentMapTable.numContam != None:
                fileObject.write('NUM_CONTAM %s\n' % currentMapTable.numContam)
            
            # Retrieve the map table values from the database and pivot into the correct format
            valueLines = self._genericPivot(session, currentMapTable, None)
            
            # Write map table value lines to file
            for valLine in valueLines:
                fileObject.write(valLine)
        
        # If the mapping table is empty, the query will throw an error. The error is handled by
        # writing an empty form of the table. 
        except:
            'Do Nothing'
#             # NOTE: Is it necessary to write out empty tables?  
#             fileObject.write('%s "%s"\n' % (mapTableName, ''))
#             fileObject.write('NUM_IDS %s\n' % (0))
#             fileObject.write('ID%sDESCRIPTION1%sDESCRIPTION2\n' % (' '*4, ' '*28))

    def _writeContaminant(self, session, fileObject):
        '''
        This method writes the contaminant transport mapping table case.
        '''
        try:
            # Retrieve the data for the contaminant mapping table
            contamMapTable = session.query(MapTable).\
                                    join(MTValue.mapTable).\
                                    filter(MTValue.mapTableFiles.contains(self)).\
                                    filter(MapTable.name == 'CONTAMINANT_TRANSPORT').\
                                    one()
                                    
            # Write the contaminant mapping table header
            fileObject.write('%s\n' % (contamMapTable.name))
            fileObject.write('NUM_CONTAM %s\n' % (contamMapTable.numContam))
            
            # Retrieve the contaminants for this project file
            contaminants = session.query(MTContaminant).\
                                    join(MTValue.contaminant).\
                                    filter(MTValue.mapTableFiles.contains(self)).\
                                    order_by(MTContaminant.id).\
                                    all()
            
            # Write out each contaminant and it's values
            for contaminant in contaminants:
                fileObject.write('"%s"  "%s"  %s\n' % (contaminant.name, contaminant.indexMap.name, contaminant.outputFilename))
                
                # Add trailing zeros to values
                precipConc = '%.2f' % contaminant.precipConc
                partition = '%.2f' % contaminant.partition
                
                # Write global variables for the contaminant
                fileObject.write('PRECIP_CONC%s%s\n' % (' '*10, precipConc))
                fileObject.write('PARTITION%s%s\n' % (' '*12, partition))
                
                # Retrieve the map table values from the database and pivot into the correct format
                valueLines = self._genericPivot(session, contamMapTable, contaminant)
                
                # Write map table value lines to file
                for valLine in valueLines:
                    fileObject.write(valLine)
                
            
        except:
            'Do Nothing'
            
            
    def _writeSediment(self, session, fileObject):
        '''
        This method writes the sediments special mapping table case.
        '''
        try:
            # Retrieve the data for the sediment mapping table
            sedimentMapTable = session.query(MapTable).\
                                    join(MTSediment.mapTable).\
                                    filter(MTSediment.mapTableFiles.contains(self)).\
                                    filter(MapTable.name == 'SEDIMENTS').\
                                    one()
            
            # Write the sediment mapping table header
            fileObject.write('%s\n' % (sedimentMapTable.name))
            fileObject.write('NUM_SED %s\n' % (sedimentMapTable.numSed))
            
            # Write the value header line
            fileObject.write('Sediment Description%sSpec. Grav%sPart. Dia%sOutput Filename\n' % (' '*22, ' '*3, ' '*5))
            
            # Retrive the sediment mapping table values
            sediments = session.query(MTSediment).\
                            filter(MTSediment.mapTableFiles.contains(self)).\
                            filter(MTSediment.mapTable == sedimentMapTable).\
                            order_by(MTSediment.id).\
                            all()
            
            # Write sediments out to file
            for sed in sediments:
                # Determine spacing for aesthetics
                space1 = 42 - len(sed.description)
                
                # Pad values with zeros
                specGrav = '%.6f' % sed.specificGravity
                partDiam = '%.6f' % sed.particleDiameter
                                
                fileObject.write('%s%s%s%s%s%s%s\n' % (sed.description, ' '*space1, specGrav, ' '*5, partDiam, ' '*6, sed.outputFilename))
        
        except:
            'Do Nothing'
        
    def _genericPivot(self, session, mapTable, contaminant):
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
                    filter(MTValue.mapTableFiles.contains(self)).\
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
                    filter(MTValue.mapTableFiles.contains(self)).\
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
                if idx < len(values)-1:
                    'Do Nothing'
                else:
                    varString = '%s%s%s%s' %(varString, mapTable.numSed, ' SEDIMENTS....', ' '*2)
            else:
                varString = '%s%s%s' %(varString, val.variable, ' '*2)
            
        # Compile the mapping table header
        header = 'ID%sDESCRIPTION1%sDESCRIPTION2%s%s\n' % (' '*4, ' '*28, ' '*28, varString)
        
        # Prepend the header line to the list of lines
        lines.insert(0, header)
        
        # Return the list of lines
        return lines
        
    
    def write(self, session, path, name):
        '''
        Map Table Write Algorithm
        '''
                
        # Obtain list of all possible mapping tables from the enumeration object defined at the top of this file
        # Note: to add to/modify the list of map table names, edit the mapTableNameEnum list.
        possibleMapTableNames = mapTableNameEnum.enums
        
        # Determine the unique set index map objects that the values describe
        idxList = []
        for val in self.mapTableValues:
            if val.contaminantID != None: # Contaminant value case
                idxList.append(val.contaminant.indexMap)
            else: # All others
                idxList.append(val.mapTable.indexMap)
        
        # Set of unique index map objects    
        idxMaps = set(idxList)

        # Initiate mapping table file
        fullPath = '%s%s%s' % (path, name, '.cmt')
        
        # Write to file
        with open(fullPath, 'w') as cmtFile:

            # Write first line to file
            cmtFile.write('GSSHA_INDEX_MAP_TABLES\n')
            
            # Write list of index maps
            for idx in idxMaps:
                cmtFile.write('INDEX_MAP%s%s "%s"\n' % (' '*16, idx.filename, idx.name))
            
            # Populate each mapping table in the file by looping through a list of possilbe names   
            for currentMapTableName in possibleMapTableNames:
                # Switch statement
                if currentMapTableName == 'SEDIMENTS':                  # Sediment mapping table case
                    self._writeSediment(session, cmtFile)
                elif currentMapTableName == 'CONTAMINANT_TRANSPORT':    # Contaminant mapping table case
                    self._writeContaminant(session, cmtFile)
                else:                                                   # Generic mapping table case
                    self._writeGeneric(session, cmtFile, currentMapTableName)    

class MapTable(DeclarativeBase):
    '''
    classdocs

    '''
    __tablename__ = 'cmt_map_tables'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    idxMapID = Column(Integer, ForeignKey('idx_index_maps.id'))
    
    # Value Columns
    name = Column(mapTableNameEnum, nullable=False)
    '''Consider removing num fields in refactoring'''
    numIDs = Column(Integer)
    maxNumCells = Column(Integer)
    numSed = Column(Integer)
    numContam = Column(Integer)
    
    # Relationship Properties
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
        return '<MapTable: Name=%s, Index Map=%s, NumIDs=%s, MaxNumCells=%s, NumSediments=%s, NumContaminants=%s>' % (
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
    mapTableFiles = relationship('MapTableFile', secondary=assocMapTable, back_populates='mapTableValues')
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
    mapTableFiles = relationship('MapTableFile', secondary=assocSediment, back_populates='mapTableSediments')
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