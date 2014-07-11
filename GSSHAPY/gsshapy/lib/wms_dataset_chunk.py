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


def datasetScalarTimeStepChunk(lines, columns, numberData, numberCells):
    """
    Process the time step chunks for scalar datasets
    """
    # Define the result object
    result = {'iStatus': None,
              'timestamp': None,
              'dataArray': None,
              'cellArray': None}

    # Split the chunks
    timeStep = pt.splitLine(lines.pop(0))
    values = []

    # Assemble lines
    for line in lines:
        values.append(pt.splitLine(line)[0])

    # Spice list into data and cells parts
    startDataIndex = 0
    endDataIndex = numberData
    startCellsIndex = numberData
    endCellsIndex = numberData + numberCells

    dataElementList = values[startDataIndex:endDataIndex]
    cellsElementList = values[startCellsIndex:endCellsIndex]

    # Get Status Array
    iStatus = int(timeStep[1])
    if iStatus == 1:
        result['dataArray'] = wmsDatasetToTwoDimensionalArray(dataElementList, columns)

    # Get Value Array
    result['cellArray'] = wmsDatasetToTwoDimensionalArray(cellsElementList, columns)

    # Assign Result
    result['iStatus'] = iStatus
    result['timestamp'] = float(timeStep[2])

    return result


def wmsDatasetToTwoDimensionalArray(elementsList, numberColumns):
    """
    Take an element list generated from a wms dataset an convert it to a string.
    """
    # Derived Variables
    numberElements = len(elementsList)

    # Define the Header
    rasterArray = []

    # Ensure that there is an integer number of rows
    if numberElements % numberColumns == 0:
        beginningIndex = 0
        endingIndex = numberColumns
        numberRows = numberElements / numberColumns

        for i in range(numberRows):
            # Extract Row
            extractedRow = elementsList[beginningIndex:endingIndex]

            # Convert value strings to numbers
            tempRow = []
            for value in extractedRow:
                tempRow.append(float(value))

            # Join all columns into a row string
            rasterArray.append(tempRow)

            # Increment indices by number of columns
            beginningIndex += numberColumns
            endingIndex += numberColumns

    return rasterArray
