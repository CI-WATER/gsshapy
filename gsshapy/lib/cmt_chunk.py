"""
********************************************************************************
* Name: Map Table Parse
* Author: Nathan Swain
* Created On: July 16, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

import logging
import shlex
import numpy as np

#local
from . import parsetools as pt

logging.basicConfig()
log = logging.getLogger(__name__)


def indexMapChunk(key, chunk):
    # Create return/result object
    result = {'idxName': None,
              'filename': None}

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
               'NUM_CONTAM': None,
               'MAX_SOIL_ID': None}
    varList = []
    valueList = []

    # Extract MapTable Name and Index Map Name
    mtName = shlex.split(chunk[0])[0]
    idxName = shlex.split(chunk[0])[1]

    # Check if the mapping table is valid via the
    # index map name. If now index map name, stop
    # processing.
    if idxName == '':
        log.info('No index map assigned to %s table. The table will '
                 'not be read into the database.', mtName)
        # No need to process if the index map is empty
        return None

    soil_3d_layer = False
    if key in ('MULTI_LAYER_SOIL', 'RICHARDS_EQN_INFILTRATION_BROOKS'):
        soil_3d_layer = True
    num_layers_loaded = 0

    # Parse the chunk into a datastructure
    valDict = {}
    for line in chunk:
        sline = line.strip().split()
        token = sline[0]

        if token == key:
            """
            DO NOTHING: The map table name and index map name
            has already been extracted above.
            """
        elif token in numVars:
            # Extract NUM type variables
            numVars[sline[0]] = sline[1]

        elif token == 'ID':
            varList = _buildVarList(sline=sline, mapTableName=mtName, numVars=numVars)
        else:
            if valDict and soil_3d_layer:
                if len(np.shape(valDict['values'])) == 2:
                    # this is for when there are no values
                    # for the DEPTH of the bottom groundwater
                    # layer as it is infinity
                    if len(sline) < len(varList):
                        sline += ['-9999']
                    valDict['values'].append(sline)
                else:
                    valDict['values'] = [valDict['values'], sline]
            else:
                valDict = _extractValues(line)

            num_layers_loaded += 1
            if not soil_3d_layer or num_layers_loaded >=3:
                valueList.append(valDict)
                valDict = {}
                num_layers_loaded = 0

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
        log.info('No contaminants found in the CONTAMINANT_TRANSPORT TABLE (NUM_CONTAM = 0).'
                 'This table will not be read into the database.')
        return None

    # Parse the chunk into a data structure
    for line in chunk:
        sline = line.strip().split()
        token = sline[0]


        if token == key:
            mtName = sline[0]

        elif token == 'NUM_CONTAM':
            """DO NOTHING"""

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
              'varList': None,
              'valueList': None,
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
            if int(sline[1]) == 0:
                # If there are no sediments return nothing
                log.info('No sediments found in the SEDIMENTS table (NUM_SED = 0).'
                         'This table will not be read into the database.')
                return None
            else:
                # This is the test for an empty
                # SEDIMENTS table
                numVars['NUM_SED'] = int(sline[1])

        elif token == 'Sediment':
            """DO NOTHING"""
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
