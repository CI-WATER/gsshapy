'''
********************************************************************************
* Name: ChannelInputChunk
* Author: Nathan Swain
* Created On: July 23, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

from gsshapy.lib import parsetools as pt

def cardChunk(key, chunk):
    '''
    Parse Card Chunk Method
    '''
    for line in chunk:
        values = []
        sline = line.strip().split()
        
        for idx in range(1, len(sline)):
            values.append(sline[idx])
        
    return {'card': sline[0],
            'values': values}

def linkChunk(key, chunk):
    '''
    Parse LINK Chunk Method
    '''
    # Extract link type card
    linkType = chunk[1].strip().split()[0]
    
    # Handlers for different link types
    if linkType == 'DX':
        result = xSectionLink(chunk)
            
    elif linkType == 'STRUCTURE':
        result = structureLink(chunk)
        
    elif linkType in ['RESERVOIR', 'LAKE']:
        result = reservoirLink(key, chunk)
    
    return result

def structureLink(lines):
    '''
    Parse STRUCTURE LINK Method
    '''
    KEYWORDS = ['LINK',
                'STRUCTURE',
                'NUMSTRUCTS',
                'STRUCTTYPE']
    
    WEIRS = ['WEIR', 'SAG_WEIR']
    
    CULVERTS = ['ROUND_CULVERT', 'RECT_CULVERT']
    
    CURVES = ['RATING_CURVE', 'SCHEDULED_RELEASE', 'RULE_CURVE']
    
    result = {'header': [],
              'structures':[]}
    
    
    chunks = pt.chunk(KEYWORDS, lines)
    
    # Parse chunks associated with each key    
    for key, chunkList in chunks.iteritems():
        # Parse each chunk in the chunk list
        for chunk in chunkList:
            if key == 'STRUCTTYPE':
                structType = chunk[0].strip().split()[1]
                if structType in WEIRS:
                    result['structures'].append(weirChunk(chunk))
                elif structType in CULVERTS:
                    result['structures'].append(culvertChunk(chunk))
                elif structType in CURVES:
                    pass
            else:
                result['header'].append(cardChunk(key, chunk))
               
    return result
    
def xSectionLink(lines):
    '''
    Parse TRAPEZOID Channel LINK Method
    '''
    KEYWORDS = ['LINK',
                'DX',
                'TRAPEZOID',
                'TRAPEZOID_ERODE',
                'TRAPEZOID_SUBSURFACE',
                'TRAPEZOID_SUBSURFACE_ERODE',
                'TRAPEZOID_ERODE_SUBSURFACE',
                'BREAKPOINT',
                'BREAKPOINT_ERODE',
                'BREAKPOINT_SUBSURFACE',
                'BREAKPOINT_SUBSURFACE_ERODE',
                'BREAKPOINT_ERODE_SUBSURFACE',
                'NODES',
                'NODE',
                'XSEC']
    
    result  =  {'header': [],
                'xSection': None,
                'nodes': []}
    
    chunks = pt.chunk(KEYWORDS, lines)
    
    # Parse chunks associated with each key    
    for key, chunkList in chunks.iteritems():
        # Parse each chunk in the chunk list
        for chunk in chunkList:
            # Cases
            if key == 'NODE':
                # Extract node x and y
                result['nodes'].append(nodeChunk(chunk))
                
            elif key == 'XSEC':
                # Extract cross section information
                result['xSection'] = xSectionChunk(chunk)
                
            else:
                # Extract all other variables into header
                result['header'].append(cardChunk(key, chunk))
    return result

def reservoirLink(key, chunk):
    '''
    Parse RESERVOIR Channel LINK Method
    '''
    return key, chunk

def nodeChunk(lines):
    '''
    Parse NODE Method
    '''
    KEYWORDS = ['NODE',
                'X_Y',
                'ELEV']
    
    result = {'node': None,
              'x': None,
              'y': None,
              'elev': None}

    chunks = pt.chunk(KEYWORDS, lines)
    
    # Parse chunks associated with each key    
    for key, chunkList in chunks.iteritems():
        # Parse each chunk in the chunk list
        for chunk in chunkList:
            schunk = chunk[0].strip().split()
            if key == 'X_Y':
                result['x'] = schunk[1]
                result['y'] = schunk[2]
            else:
                result[key.lower()] = schunk[1]
                
    return result
    
def xSectionChunk(lines):
    '''
    Parse XSEC Method
    '''
    KEYWORDS = ['MANNINGS_N',
                'BOTTOM_WIDTH',
                'BANKFULL_DEPTH',
                'SIDE_SLOPE',
                'NPAIRS',
                'NUM_INTERP',
                'X1',
                'ERODE',
                'MAX_ERODE',
                'SUBSURFACE',
                'M_RIVER',
                'K_RIVER']
    
    result = {'manning_n': None,
              'bottom_width': None,
              'bankfull_depth': None,
              'side_slope': None,
              'npairs': None,
              'num_interp': None,
              'erode': False,
              'subsurface': False,
              'max_erode': None,
              'm_river': None,
              'k_river': None,
              'breakpoints': []}
    
    chunks = pt.chunk(KEYWORDS, lines)
    
    # Parse chunks associated with each key    
    for key, chunkList in chunks.iteritems():
        # Parse each chunk in the chunk list
        for chunk in chunkList:
            # Strip and split the line (only one item in each list)
            schunk = chunk[0].strip().split()
            
            # Cases
            if key == 'X1':
                # Extract breakpoint XY pairs
                x = schunk[1]
                y = schunk[2]
                result['breakpoints'].append({'x': x, 'y': y})
                
            if key in ['SUBSURFACE', 'ERODE']:
                # Set booleans
                result[key.lower()] = True
                
            else:
                # Extract value
                result[key.lower()] = schunk[1]
    return result

def weirChunk(lines):
    '''
    Parse Weir Structures Method
    '''
    KEYWORDS = ['STRUCTTYPE',
                'CREST_LENGTH',
                'CREST_LOW_ELEV',
                'DISCHARGE_COEFF_FORWARD',
                'DISCHARGE_COEFF_REVERSE',
                'CREST_LOW_LOC',
                'STEEP_SLOPE',
                'SHALLOW_SLOPE']
    
    result = {}
    chunks = pt.chunk(KEYWORDS, lines)
    
    # Parse chunks associated with each key    
    for key, chunkList in chunks.iteritems():
        # Parse each chunk in the chunk list
        for chunk in chunkList:
            # Strip and split the line (only one item in each list)
            schunk = chunk[0].strip().split()
            print schunk
    
    return result
    
def culvertChunk(lines):
    '''
    Parse Culvert Structures Method
    '''
    KEYWORDS = ['STRUCTTYPE',
                'UPINVERT',
                'DOWNINVERT',
                'INLET_DISCH_COEFF',
                'REV_FLOW_DISCH_COEFF',
                'SLOPE',
                'LENGTH',
                'ROUGH_COEFF',
                'DIAMETER',
                'WIDTH',
                'HEIGHT']
    
    result = {}
    chunks = pt.chunk(KEYWORDS, lines)
    
    # Parse chunks associated with each key    
    for key, chunkList in chunks.iteritems():
        # Parse each chunk in the chunk list
        for chunk in chunkList:
            # Strip and split the line (only one item in each list)
            schunk = chunk[0].strip().split()
            print schunk
    
    return result
    


    
