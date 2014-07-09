"""
********************************************************************************
* Name: WMS Dataset Chunk
* Author: Nathan Swain
* Created On: July 16, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

from gsshapy.lib import parsetools as pt


def datasetHeaderChunk(key, lines):
    """
    Process the dataset header
    """
    KEYWORDS = ('DATASET',
                'OBJTYPE',
                'VECTYPE',
                'BEGSCL',
                'BEGVEC',
                'OBJID',
                'ND',
                'NC',
                'NAME')

    TYPE_KEYS = ('BEGSCL', 'BEGVEC')

    result = {'type': None,
              'numberData': None,
              'numberCells': None,
              'name': None,
              'objectID': None,
              'objectType': None,
              'vectorType': None}

    chunks = pt.chunk(KEYWORDS, lines)

    for key, chunkList in chunks.iteritems():

        for chunk in chunkList:
            schunk = pt.splitLine(chunk[0])

            if key == 'ND':
                result['numberData'] = int(schunk[1])

            elif key == 'NC':
                result['numberCells'] = int(schunk[1])

            elif key == 'NAME':
                result['name'] = schunk[1]

            elif key == 'OBJID':
                result['objectID'] = int(schunk[1])

            elif key == 'OBJTYPE':
                result['objectType'] = schunk[1]

            elif key == 'VECTYPE':
                result['vectorType'] = schunk[1]

            elif key in TYPE_KEYS:
                result['type'] = schunk[0]

    return result


def datasetTimeStepChunk(key, lines):
    """
    Process the time step chunks
    """

    # Define the result object
    result = {'iStatus': None,
              'timestamp': None,
              'values': []}

    # Split the chunks
    timeStep = pt.splitLine(lines.pop(0))
    values = []

    for line in lines:
        values.append(pt.splitLine(line)[0])

    # Assign Result
    result['iStatus'] = int(timeStep[1])
    result['timestamp'] = float(timeStep[2])
    result['values'] = values

    return result
