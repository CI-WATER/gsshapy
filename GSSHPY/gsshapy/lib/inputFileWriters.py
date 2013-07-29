'''
********************************************************************************
* Name: Input File Readers
* Author: Nathan Swain
* Created On: July 29, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

def writeMappingTableFile(projectFile, session, directory, filePrefix):
    # Write map table file
    mapTableFile = projectFile.mapTableFile
    mapTableFile.write(session=session, directory=directory, filePrefix=filePrefix)

def writeChannelInputFile(projectFile, session, directory, filePrefix):    
    # Write channel input file
    channelInputFile = projectFile.channelInputFile
    channelInputFile.write(session=session, directory=directory, filePrefix=filePrefix)

def writePrecipitationFile(projectFile, session, directory, filePrefix):   
    # Write precipitation file
    precipFile = projectFile.precipFile
    precipFile.write(session=session, directory=directory, filePrefix=filePrefix)

def writePipeNetworkFile(projectFile, session, directory, filePrefix):   
    # Write pipe network
    pipeFile = projectFile.stormPipeNetworkFile
    pipeFile.write(session=session, directory=directory, filePrefix=filePrefix)
    
def writeHmetFile(projectFile, session, directory, filePrefix):
    # Write hmet file
    hmetFile = projectFile.hmetFile
    hmetFile.writeWES(session=session, directory=directory, filePrefix=filePrefix)