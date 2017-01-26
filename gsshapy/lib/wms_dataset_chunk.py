"""
********************************************************************************
* Name: WMS Dataset Chunk
* Author: Nathan Swain
* Created On: July 16, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from future.utils import iteritems

from . import parsetools as pt

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

    for key, chunkList in iteritems(chunks):

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


def datasetScalarTimeStepChunk(lines, numberColumns, numberCells):
    """
    Process the time step chunks for scalar datasets
    """
    END_DATASET_TAG = 'ENDDS'

    # Define the result object
    result = {'iStatus': None,
              'timestamp': None,
              'cellArray': None,
              'rasterText': None}

    # Split the chunks
    timeStep = pt.splitLine(lines.pop(0))

    # Extract cells, ignoring the status indicators
    startCellsIndex = numberCells

    # Handle case when status cells are not included (istat = 0)
    iStatus = int(timeStep[1])

    if iStatus == 0:
        startCellsIndex = 0

    # Strip off ending dataset tag
    if END_DATASET_TAG in lines[-1]:
        lines.pop(-1)

    # Assemble the array string
    arrayString = '[['
    columnCounter = 1
    lenLines = len(lines) - 1

    # Also assemble raster text field to preserve for spatial datasets
    rasterText = ''

    for index in range(startCellsIndex, len(lines)):
        # Check columns condition
        if columnCounter % numberColumns != 0 and index != lenLines:
            arrayString += lines[index].strip() + ', '
        elif columnCounter % numberColumns == 0 and index != lenLines:
            arrayString += lines[index].strip() + '], ['
        elif index == lenLines:
            arrayString += lines[index].strip() + ']]'

        # Advance counter
        columnCounter += 1

        rasterText += lines[index]

    # Get Value Array
    result['cellArray'] = arrayString
    result['rasterText'] = rasterText

    # Assign Result
    result['iStatus'] = iStatus
    result['timestamp'] = float(timeStep[2])

    return result
