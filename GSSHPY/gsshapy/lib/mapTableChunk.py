'''
********************************************************************************
* Name: Map Table Parse
* Author: Nathan Swain
* Created On: July 16, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

from gsshapy.lib import parsetools as pt

def indexMapChunk(key, chunk):
    # Create return/result object
    result = {'idxName': None,
              'filename': None,
              'map': None}
    
    # Extract info
    for line in chunk:
        sline = pt.splitLine(line)
        result['idxName'] = sline[2]
        result['filename'] = pt.relativePath(sline[1])
        
    return result
    
def mapTableChunk(key, chunk):
    # Global variables
    numVars = {'NUM_IDS': None,
               'MAX_NUMBER_CELLS': None,
               'NUM_SED': None,
               'NUM_CONTAM': None}
    varList = []
    valueList = []

    # Extract MapTable Name and Index Map Name
    mtName = chunk[0].strip().split()[0]
    idxName = chunk[0].strip().split()[1].strip('\"')
    
    # Check if the mapping table is being used via 
    # index map name.
    if idxName == '':
        # No need to process if the index map is empty
        return None
    
    # Parse the chunk into a datastructure
    for line in chunk:
        sline = line.strip().split()
        token = sline[0]
        valDict = {}
        
        if token == key:
            '''DO NOTHING'''        
            
        elif token in numVars:
            # Extract NUM type variables
            numVars[sline[0]] = sline[1]
        
        elif token == 'ID':
            varList = _buildVarList(sline=sline, mapTableName=mtName, numVars=numVars)
        else:
            valDict = _extractValues(line)
            valueList.append(valDict)
    
    # Create return/result object
    result = {'name': mtName,
              'indexMapName': idxName,
              'numVars': numVars,
              'varList': varList,
              'valueList': valueList,
              'contaminants': None}

    return result
    
def contamChunk(key, chunk):
    # Global variables
    contamList = []
    valDict = dict()
    numVars = {'NUM_IDS': None,
               'MAX_NUMBER_CELLS': None,
               'NUM_SED': None,
               'NUM_CONTAM': None}
    
    # Extract the number of contaminants
    numVars['NUM_CONTAM'] = int(chunk[1].strip().split()[1])
    
    # Check if there are any contaminants. No need
    # to process further if there are 0.
    if numVars['NUM_CONTAM'] == 0:
        return None
    
    # Parse the chunk into a data structure
    for line in chunk:
        sline = line.strip().split()
        token = sline[0]
        
        
        if token == key:
            mtName = sline[0]
        
        elif token == 'NUM_CONTAM':
            '''DO NOTHING'''
        
        elif '\"' in token:
            # Append currContam to contamList and extract
            # data from the current line.
            
            # Initialize new contaminant dictionary and variables
            currContam = dict()
            valueList = []
            contamVars = {'NUM_IDS': None,
                          'PRECIP_CONC': None,
                          'PARTITION': None}
            
            # Extract contam info and add variables to dictionary
            currContam['name'] = sline[0].strip('\"')
            currContam['indexMapName'] = sline[1].strip('\"')
            currContam['outPath'] = sline[2].strip('\"')
            currContam['numVars'] = numVars
            currContam['valueList'] = valueList

            contamList.append(currContam)
            
        elif token in contamVars:
            # Extract NUM type variables
            contamVars[token] = sline[1]
        
        elif token == 'ID':
            currContam['contamVars'] = contamVars
            varList = _buildVarList(sline=sline, mapTableName=mtName, numVars=numVars)
            
            currContam['varList'] = varList
            
        else:
            valDict = _extractValues(line)
            valueList.append(valDict)
     
    # Create return/result object
    result = {'name': mtName,
              'indexMapName': None,
              'numVars': numVars,
              'varList': varList,
              'valueList': valueList,
              'contaminants': contamList}
        
    return result
    
def sedimentChunk(key, chunk):
    # Global Variables
    valueList = []
    numVars = {'NUM_IDS': None,
               'MAX_NUMBER_CELLS': None,
               'NUM_SED': None,
               'NUM_CONTAM': None}
    
    for line in chunk:
        sline = line.strip().split()
        token = sline[0]
        
        if token == key:
            mtName = sline[0]
        elif token == 'NUM_SED':
            numVars['NUM_SED'] = int(sline[1])
        elif token == 'Sediment':
            '''DO NOTHING'''
        else:
            valueList.append(sline)
                    
    # Create return/result object
    result = {'name': mtName,
              'indexMapName': None,
              'numVars': numVars,
              'varList': None,
              'valueList': valueList,
              'contaminants': None}
    
    return result

def _buildVarList(sline, mapTableName, numVars):
    # Global constant
    IGNORE = ['ID', 'DESCRIPTION1', 'DESCRIPTION2']
    SOIL_EROSION = ['SPLASH_COEF', 'DETACH_COEF', 'DETACH_EXP', 'DETACH_CRIT', 'SED_COEF']
    
    varList = []
    # Extract variable names from the header line which 
    # begins with the 'ID' token.
    if mapTableName =='SOIL_EROSION_PROPS':
        if numVars['NUM_SED']:
            for item in sline:
                if item in SOIL_EROSION:
                    varList.append(item)
            for i in range(0, int(numVars['NUM_SED'])):
                varList.append('XSEDIMENT')
    else:
        for item in sline:
            if item not in IGNORE:
                varList.append(item)
    
    return varList

def _extractValues(line):
    valDict = dict()
    # Extract value line via slices
    valDict['index'] = line[:6].strip() # First 7 columns
    valDict['description1'] = line[6:46].strip() # Next 40 columns
    valDict['description2'] = line[46:86].strip() # Next 40 columns
    valDict['values'] = line[86:].strip().split() # Remaining columns
    return valDict

def _createValueObjects(valueList, varList, mapTable, contaminant=None):
    # Global Variables
    mtIndices = []
    
    # Populate GSSHAPY MTValue and MTIndex objects
    for row in valueList:
        mtIndex = MTIndex(index=row['index'], description1=row['description1'], description2=row['description2'])
        mtIndices.append(mtIndex)
        for i, value in enumerate(row['values']):
            mtValue = MTValue(variable=varList[i], value=float(value))
            mtValue.index = mtIndex
            mtValue.mapTable = mapTable
            if contaminant:
                mtValue.contaminant = contaminant
    return mtIndices