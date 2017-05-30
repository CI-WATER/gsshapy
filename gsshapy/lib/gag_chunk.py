"""
********************************************************************************
* Name: Precipitation File Chunk
* Author: Nathan Swain
* Created On: July 16, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from datetime import datetime
from future.utils import iteritems

from . import parsetools as pt

def eventChunk(key, lines):
    """
    Parse EVENT chunks
    """
    ## NOTE: RADAR file format not supported currently.
    ## TODO: Add Support for RADAR file format type values

    # Contants
    KEYWORDS = ('EVENT',
                'NRPDS',
                'NRGAG',
                'COORD',
                'GAGES',
                'ACCUM',
                'RATES',
                'RADAR')

    NUM_CARDS = ('NRPDS',
                 'NRGAG')

    VALUE_CARDS = ('GAGES',
                   'ACCUM',
                   'RATES',
                   'RADAR')

    # Define result object
    result = {'description': None,
              'nrgag': None,
              'nrpds': None,
              'coords':[],
              'valLines':[]}

    chunks = pt.chunk(KEYWORDS, lines)

    # Parse chunks associated with each key
    for card, chunkList in iteritems(chunks):
        # Parse each chunk in the chunk list
        for chunk in chunkList:
            schunk = chunk[0].strip().split()

            # Cases
            if card == 'EVENT':
                # EVENT handler
                schunk = pt.splitLine(chunk[0])
                result['description'] = schunk[1]

            elif card in NUM_CARDS:
                # Num cards handler
                result[card.lower()] = schunk[1]

            elif card == 'COORD':
                # COORD handler
                schunk = pt.splitLine(chunk[0])

                try:
                    # Extract the event description
                    desc = schunk[3]
                except:
                    # Handle case where the event description is blank
                    desc = ""

                coord = {'x': schunk[1],
                         'y': schunk[2],
                         'description': desc}

                result['coords'].append(coord)

            elif card in VALUE_CARDS:
                # Value cards handler
                # Extract DateTime
                dateTime = datetime(year=int(schunk[1]),
                                    month=int(schunk[2]),
                                    day=int(schunk[3]),
                                    hour=int(schunk[4]),
                                    minute=int(schunk[5]))

                # Compile values into a list
                values = []
                for index in range(6, len(schunk)):
                    values.append(schunk[index])

                valueLine = {'type': schunk[0],
                             'dateTime': dateTime,
                             'values': values}

                result['valLines'].append(valueLine)

    return result
