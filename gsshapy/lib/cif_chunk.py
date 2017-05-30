"""
********************************************************************************
* Name: ChannelInputChunk
* Author: Nathan Swain
* Created On: July 23, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from future.utils import iteritems

from . import parsetools as pt

def cardChunk(key, chunk):
    """
    Parse Card Chunk Method
    """
    for line in chunk:
        values = []
        sline = line.strip().split()

        for idx in range(1, len(sline)):
            values.append(sline[idx])

    return {'card': sline[0],
            'values': values}

def connectChunk(key, chunk):
    """
    Parse Card Chunk Method
    """
    upLinks = []
    schunk = chunk[0].strip().split()

    for idx in range(4, len(schunk)):
        upLinks.append(schunk[idx])

    result = {'link': schunk[1],
              'downLink': schunk[2],
              'numUpLinks': schunk[3],
              'upLinks': upLinks}

    return result

def linkChunk(key, chunk):
    """
    Parse LINK Chunk Method
    """
    # Extract link type card
    linkType = chunk[1].strip().split()[0]

    # Cases
    if linkType == 'DX':
        # Cross section link type handler
        result = xSectionLink(chunk)

    elif linkType == 'STRUCTURE':
        # Structure link type handler
        result = structureLink(chunk)

    elif linkType in ('RESERVOIR', 'LAKE'):
        # Reservoir link type handler
        result = reservoirLink(chunk)
    return result

def structureLink(lines):
    """
    Parse STRUCTURE LINK Method
    """
    # Constants
    KEYWORDS = ('LINK',
                'STRUCTURE',
                'NUMSTRUCTS',
                'STRUCTTYPE')

    WEIR_KEYWORDS = ('STRUCTTYPE',
                     'CREST_LENGTH',
                     'CREST_LOW_ELEV',
                     'DISCHARGE_COEFF_FORWARD',
                     'DISCHARGE_COEFF_REVERSE',
                     'CREST_LOW_LOC',
                     'STEEP_SLOPE',
                     'SHALLOW_SLOPE')

    CULVERT_KEYWORDS = ('STRUCTTYPE',
                        'UPINVERT',
                        'DOWNINVERT',
                        'INLET_DISCH_COEFF',
                        'REV_FLOW_DISCH_COEFF',
                        'SLOPE',
                        'LENGTH',
                        'ROUGH_COEFF',
                        'DIAMETER',
                        'WIDTH',
                        'HEIGHT')

    WEIRS = ('WEIR', 'SAG_WEIR')

    CULVERTS = ('ROUND_CULVERT', 'RECT_CULVERT')

    CURVES = ('RATING_CURVE', 'SCHEDULED_RELEASE', 'RULE_CURVE')

    result = {'type': 'STRUCTURE',
              'header': {'link': None,
                         'numstructs': None},
              'structures':[]}

    chunks = pt.chunk(KEYWORDS, lines)

    # Parse chunks associated with each key
    for key, chunkList in iteritems(chunks):
        # Parse each chunk in the chunk list
        for chunk in chunkList:
            # Cases
            if key == 'STRUCTTYPE':
                # Structure handler
                structType = chunk[0].strip().split()[1]

                # Cases
                if structType in WEIRS:

                    weirResult = {'structtype': None,
                                  'crest_length': None,
                                  'crest_low_elev': None,
                                  'discharge_coeff_forward': None,
                                  'discharge_coeff_reverse': None,
                                  'crest_low_loc': None,
                                  'steep_slope': None,
                                  'shallow_slope': None}

                    # Weir type structures handler
                    result['structures'].append(structureChunk(WEIR_KEYWORDS, weirResult, chunk))

                elif structType in CULVERTS:

                    culvertResult = {'structtype': None,
                                     'upinvert': None,
                                     'downinvert': None,
                                     'inlet_disch_coeff': None,
                                     'rev_flow_disch_coeff': None,
                                     'slope': None,
                                     'length': None,
                                     'rough_coeff': None,
                                     'diameter': None,
                                     'width': None,
                                     'height': None}

                    # Culvert type structures handler
                    result['structures'].append(structureChunk(CULVERT_KEYWORDS, culvertResult, chunk))

                elif structType in CURVES:
                    # Curve type handler
                    pass
            elif key != 'STRUCTURE':
                # All other variables header
                result['header'][key.lower()] = chunk[0].strip().split()[1]

    return result

def xSectionLink(lines):
    """
    Parse Cross Section Links Method
    """
    # Constants
    KEYWORDS = ('LINK',
                'DX',
                'TRAPEZOID',
                'TRAPEZOID_ERODE',
                'TRAPEZOID_SUBSURFACE',
                'ERODE_TRAPEZOID',
                'ERODE_SUBSURFACE',
                'SUBSURFACE_TRAPEZOID',
                'SUBSURFACE_ERODE',
                'TRAPEZOID_ERODE_SUBSURFACE',
                'TRAPEZOID_SUBSURFACE_ERODE',
                'ERODE_TRAPEZOID_SUBSURFACE',
                'ERODE_SUBSURFACE_TRAPEZOID',
                'SUBSURFACE_TRAPEZOID_ERODE',
                'SUBSURFACE_ERODE_TRAPEZOID',
                'BREAKPOINT',
                'BREAKPOINT_ERODE',
                'BREAKPOINT_SUBSURFACE',
                'ERODE_BREAKPOINT',
                'ERODE_SUBSURFACE',
                'SUBSURFACE_BREAKPOINT',
                'SUBSURFACE_ERODE',
                'BREAKPOINT_ERODE_SUBSURFACE',
                'BREAKPOINT_SUBSURFACE_ERODE',
                'ERODE_BREAKPOINT_SUBSURFACE',
                'ERODE_SUBSURFACE_BREAKPOINT',
                'SUBSURFACE_BREAKPOINT_ERODE',
                'SUBSURFACE_ERODE_BREAKPOINT',
                'TRAP',
                'TRAP_ERODE',
                'TRAP_SUBSURFACE',
                'ERODE_TRAP',
                'ERODE_SUBSURFACE',
                'SUBSURFACE_TRAP',
                'SUBSURFACE_ERODE',
                'TRAP_ERODE_SUBSURFACE',
                'TRAP_SUBSURFACE_ERODE',
                'ERODE_TRAP_SUBSURFACE',
                'ERODE_SUBSURFACE_TRAP',
                'SUBSURFACE_TRAP_ERODE',
                'SUBSURFACE_ERODE_TRAP',
                'NODES',
                'NODE',
                'XSEC')



    ERODE = ('TRAPEZOID_ERODE',
             'TRAP_ERODE',
             'TRAP_SUBSURFACE_ERODE',
             'TRAP_ERODE_SUBSURFACE',
             'BREAKPOINT_ERODE',
             'TRAPEZOID_SUBSURFACE_ERODE',
             'TRAPEZOID_ERODE_SUBSURFACE',
             'BREAKPOINT_SUBSURFACE_ERODE',
             'BREAKPOINT_ERODE_SUBSURFACE')

    SUBSURFACE = ('TRAPEZOID_SUBSURFACE',
                  'TRAP_SUBSURFACE',
                  'TRAP_SUBSURFACE_ERODE',
                  'TRAP_ERODE_SUBSURFACE',
                  'BREAKPOINT_SUBSURFACE',
                  'TRAPEZOID_SUBSURFACE_ERODE',
                  'TRAPEZOID_ERODE_SUBSURFACE',
                  'BREAKPOINT_SUBSURFACE_ERODE',
                  'BREAKPOINT_ERODE_SUBSURFACE')

    result  =  {'type': 'XSEC',
                'header': {'link': None,
                           'dx': None,
                           'xSecType': None,
                           'nodes': None,
                           'erode': False,
                           'subsurface': False},
                'xSection': None,
                'nodes': []}

    chunks = pt.chunk(KEYWORDS, lines)

    # Parse chunks associated with each key
    for key, chunkList in iteritems(chunks):
        # Parse each chunk in the chunk list
        for chunk in chunkList:
            # Cases
            if key == 'NODE':
                # Extract node x and y
                result['nodes'].append(nodeChunk(chunk))

            elif key == 'XSEC':
                # Extract cross section information
                result['xSection'] = xSectionChunk(chunk)

            elif ('TRAPEZOID' in key) or ('BREAKPOINT' in key) or ('TRAP' in key):
                # Cross section type handler
                result['header']['xSecType'] = key

            elif key in ERODE:
                # Erode handler
                result['header']['erode'] = True

            elif key in SUBSURFACE:
                # Subsurface handler
                result['header']['subsurface'] = True

            else:
                # Extract all other variables into header
                result['header'][key.lower()] = chunk[0].strip().split()[1]

    return result

def reservoirLink(lines):
    """
    Parse RESERVOIR Link Method
    """
    # Constants
    KEYWORDS = ('LINK',
                'RESERVOIR',
                'RES_MINWSE',
                'RES_INITWSE',
                'RES_MAXWSE',
                'RES_NUMPTS',
                'LAKE',
                'MINWSE',
                'INITWSE',
                'MAXWSE',
                'NUMPTS')

    result  =  {'header': {'link': None,
                           'res_minwse': None,
                           'res_initwse': None,
                           'res_maxwse': None,
                           'res_numpts': None,
                           'minwse': None,
                           'initwse': None,
                           'maxwse': None,
                           'numpts': None},
                'type': None,
                'points': []}

    pair = {'i': None,
            'j': None}

    # Rechunk the chunk
    chunks = pt.chunk(KEYWORDS, lines)

    # Parse chunks associated with each key
    for key, chunkList in iteritems(chunks):
        # Parse each chunk in the chunk list
        for chunk in chunkList:
            schunk = chunk[0].strip().split()


            # Cases
            if key in ('NUMPTS', 'RES_NUMPTS'):
                # Points handler
                result['header'][key.lower()] = schunk[1]

                # Parse points
                for idx in range(1, len(chunk)):
                    schunk = chunk[idx].strip().split()

                    for count, ordinate in enumerate(schunk):
                        # Divide ordinates into ij pairs
                        if (count % 2) == 0:
                            pair['i'] = ordinate
                        else:
                            pair['j'] = ordinate
                            result['points'].append(pair)
                            pair = {'i': None,
                                    'j': None}

            elif key in ('LAKE', 'RESERVOIR'):
                # Type handler
                result['type'] = schunk[0]
            else:
                # Header variables handler
                result['header'][key.lower()] = schunk[1]
    return result

def nodeChunk(lines):
    """
    Parse NODE Method
    """
    # Constants
    KEYWORDS = ('NODE',
                'X_Y',
                'ELEV')

    result = {'node': None,
              'x': None,
              'y': None,
              'elev': None}

    chunks = pt.chunk(KEYWORDS, lines)

    # Parse chunks associated with each key
    for key, chunkList in iteritems(chunks):
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
    """
    Parse XSEC Method
    """
    # Constants
    KEYWORDS = ('MANNINGS_N',
                'BOTTOM_WIDTH',
                'BANKFULL_DEPTH',
                'SIDE_SLOPE',
                'NPAIRS',
                'NUM_INTERP',
                'X1',
                'ERODE',
                'MAX_EROSION',
                'SUBSURFACE',
                'M_RIVER',
                'K_RIVER')

    result = {'mannings_n': None,
              'bottom_width': None,
              'bankfull_depth': None,
              'side_slope': None,
              'npairs': None,
              'num_interp': None,
              'erode': False,
              'subsurface': False,
              'max_erosion': None,
              'm_river': None,
              'k_river': None,
              'breakpoints': []}

    chunks = pt.chunk(KEYWORDS, lines)

    # Parse chunks associated with each key
    for key, chunkList in iteritems(chunks):
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

            if key in ('SUBSURFACE', 'ERODE'):
                # Set booleans
                result[key.lower()] = True

            else:
                # Extract value
                result[key.lower()] = schunk[1]
    return result

def structureChunk(keywords, resultDict, lines):
    """
    Parse Weir and Culvert Structures Method
    """
    chunks = pt.chunk(keywords, lines)

    # Parse chunks associated with each key
    for key, chunkList in iteritems(chunks):
        # Parse each chunk in the chunk list
        for chunk in chunkList:
            # Strip and split the line (only one item in each list)
            schunk = chunk[0].strip().split()

            # Extract values and assign to appropriate key in resultDict
            resultDict[key.lower()] = schunk[1]

    return resultDict
