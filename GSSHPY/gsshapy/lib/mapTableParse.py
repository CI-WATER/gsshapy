'''
********************************************************************************
* Name: Map Table Parse
* Author: Nathan Swain
* Created On: July 16, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''
import re

from gsshapy.lib import parsetools as pt
from gsshapy.orm.idx import IndexMap
from gsshapy.orm.cmt import MapTable


def indexMapChunk(key, chunk):
    for line in chunk:
        sline = pt.splitLine(line)
        idxName = sline[2]
        filename = pt.relativePath(sline[1])
        indexMap = IndexMap(name=idxName, filename=filename, rasterMap=None)
    return indexMap
    
def mapTableChunk(key, chunk):
    NUM_VARS = {'NUM_IDS': None,
                'MAX_NUMBER_CELLS': None}
    
    IGNORE = ['ID', 'DESCRIPTION1', 'DESCRIPTION2']
    varList = []
    valList = []
    
    
    for line in chunk:
        sline = line.strip().split()
        token = sline[0]
        valDict = {}
        
        if token == key:
            # Extract name and index map name
            mtName = sline[0]
            idxName = sline[1]
            
            
            if idxName == '""':
                # No need to process if the index map is empty
                return None
            
        elif token in NUM_VARS:
            # Extract NUM type variables
            NUM_VARS[sline[0]] = sline[1]
        
        elif token == 'ID':
            # Extract variable names from the header line which 
            # begins with the 'ID' token.
            for item in sline:
                if item not in IGNORE:
                    varList.append(item)
        
        else:
            # Extract value line through slices
            valDict['index'] = line[:6].strip()
            valDict['description1'] = line[6:47].strip()
            valDict['description2'] = line[47:88].strip()
            valDict['values'] = line[88:].strip()
            valList.append(valDict)
            
    # Initiate GSSHAPY objects
    mapTable = MapTable(name=mtName, numIDs=NUM_VARS['NUM_IDS'], maxNumCells=NUM_VARS['MAX_NUMBER_CELLS'])
                
    print mtName, idxName
    print varList
    print NUM_VARS
    print valList
        
def contamChunk(key, chunk):
    print key, chunk
    
def sedimentChunk(key, chunk):
    print key, chunk 
    
def splitIndexLine(line):
    line = line.strip()
    splitLine = re.split('\s{2,}', line)
    return splitLine
