'''
********************************************************************************
* Name: StormPipeChunk
* Author: Nathan Swain
* Created On: July 26, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

from gsshapy.lib import parsetools as pt

def connectChunk(key, chunk):
    '''
    Parse Storm Pipe CONNECT Chunk Method
    '''
    schunk = chunk[0].strip().split()
    
    result = {'slinkNumber': schunk[1],
              'upSjunc': schunk[2],
              'downSjunc': schunk[3]}

    return result
    
def sjuncChunk(key, chunk):
    '''
    Parse Super Junction (SJUNC) Chunk Method
    '''
    schunk = chunk[0].strip().split()
    
    result = {'sjuncNumber': schunk[1],
              'groundSurfaceElev': schunk[2],
              'invertElev': schunk[3],
              'manholeSA': schunk[4],
              'inletCode': schunk[5],
              'linkOrCellI': schunk[6],
              'nodeOrCellJ': schunk[7],
              'weirSideLength': schunk[8],
              'orifaceDiameter': schunk[9]}

    return result
    
def slinkChunk(key, lines):
    '''
    Parse Super Link (SLINK) Chunk Method
    '''
    KEYWORDS = ('SLINK',
                'NODE',
                'PIPE')
    
    chunks = pt.chunk(KEYWORDS, lines)
    
    # Parse chunks associated with each key    
    for card, chunkList in chunks.iteritems():
        # Parse each chunk in the chunk list
        for chunk in chunkList:
            print chunk
            # Cases
            if card == 'SLINK':
                pass
            elif card == 'NODE':
                pass
            elif card == 'PIPE':
                pass
    
    