"""
********************************************************************************
* Name: Channel Input File Chunk
* Author: Nathan Swain
* Created On: July 26, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

from future.utils import iteritems

from . import parsetools as pt

def connectChunk(key, chunk):
    """
    Parse Storm Pipe CONNECT Chunk Method
    """
    schunk = chunk[0].strip().split()

    result = {'slinkNumber': schunk[1],
              'upSjunc': schunk[2],
              'downSjunc': schunk[3]}

    return result

def sjuncChunk(key, chunk):
    """
    Parse Super Junction (SJUNC) Chunk Method
    """
    schunk = chunk[0].strip().split()

    result = {'sjuncNumber': schunk[1],
              'groundSurfaceElev': schunk[2],
              'invertElev': schunk[3],
              'manholeSA': schunk[4],
              'inletCode': schunk[5],
              'linkOrCellI': schunk[6],
              'nodeOrCellJ': schunk[7],
              'weirSideLength': schunk[8],
              'orificeDiameter': schunk[9]}

    return result

def slinkChunk(key, lines):
    """
    Parse Super Link (SLINK) Chunk Method
    """
    KEYWORDS = ('SLINK',
                'NODE',
                'PIPE')

    result = {'slinkNumber':None,
              'numPipes':None,
              'nodes':[],
              'pipes':[]}

    chunks = pt.chunk(KEYWORDS, lines)

    # Parse chunks associated with each key
    for card, chunkList in iteritems(chunks):
        # Parse each chunk in the chunk list
        for chunk in chunkList:
            schunk = chunk[0].strip().split()

            # Cases
            if card == 'SLINK':
                # SLINK handler
                result['slinkNumber'] = schunk[1]
                result['numPipes'] = schunk[2]

            elif card == 'NODE':
                # NODE handler
                node = {'nodeNumber': schunk[1],
                        'groundSurfaceElev': schunk[2],
                        'invertElev': schunk[3],
                        'manholeSA': schunk[4],
                        'inletCode': schunk[5],
                        'cellI': schunk[6],
                        'cellJ': schunk[7],
                        'weirSideLength': schunk[8],
                        'orificeDiameter': schunk[9]}

                result['nodes'].append(node)

            elif card == 'PIPE':
                # PIPE handler
                pipe = {'pipeNumber': schunk[1],
                        'xSecType': schunk[2],
                        'diameterOrHeight': schunk[3],
                        'width': schunk[4],
                        'slope': schunk[5],
                        'roughness': schunk[6],
                        'length': schunk[7],
                        'conductance': schunk[8],
                        'drainSpacing': schunk[9]}

                result['pipes'].append(pipe)

    return result
