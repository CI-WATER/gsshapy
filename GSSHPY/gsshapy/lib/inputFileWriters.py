'''
********************************************************************************
* Name: Input File Readers
* Author: Nathan Swain
* Created On: July 29, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

def writeMappingTableFile(projectFile, session, directory, filename):
    # Write map table file
    mapTableFile = projectFile.mapTableFile
    mapTableFile.write(session=session, directory=directory, filename=filename)

def writeChannelInputFile(projectFile, session, directory, filename):    
    # Write channel input file
    channelInputFile = projectFile.channelInputFile
    channelInputFile.write(session=session, directory=directory, filename=filename)

def writePrecipitationFile(projectFile, session, directory, filename):   
    # Write precipitation file
    precipFile = projectFile.precipFile
    precipFile.write(session=session, directory=directory, filename=filename)

def writePipeNetworkFile(projectFile, session, directory, filename):   
    # Write pipe Network
    pipeFile = projectFile.stormPipeNetworkFile
    pipeFile.write(session=session, directory=directory, filename=filename)