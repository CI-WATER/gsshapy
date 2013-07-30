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
    '''
    Initiate Write Mapping Table File Method
    '''
    mapTableFile = projectFile.mapTableFile
    mapTableFile.write(session=session, directory=directory, filePrefix=filePrefix)

def writeChannelInputFile(projectFile, session, directory, filePrefix):    
    '''
    Initiate Write Channel Input File Method
    '''
    channelInputFile = projectFile.channelInputFile
    channelInputFile.write(session=session, directory=directory, filePrefix=filePrefix)

def writePrecipitationFile(projectFile, session, directory, filePrefix):   
    '''
    Initiate Write Precipitation File Method
    '''
    precipFile = projectFile.precipFile
    precipFile.write(session=session, directory=directory, filePrefix=filePrefix)

def writePipeNetworkFile(projectFile, session, directory, filePrefix):   
    '''
    Initiate Write Storm Pipe Network File Method
    '''
    pipeFile = projectFile.stormPipeNetworkFile
    pipeFile.write(session=session, directory=directory, filePrefix=filePrefix)
    
def writeHmetFile(projectFile, session, directory, filePrefix):
    '''
    Initiate Write HMET File Method
    '''
    hmetFile = projectFile.hmetFile
    hmetFile.writeWES(session=session, directory=directory, filePrefix=filePrefix)
    
def writeNwsrfsFile(projectFile, session, directory, filePrefix):
    '''
    Initiate Write NWSRFS File Method
    '''
    nwsrfsFile = projectFile.nwsrfsFile
    nwsrfsFile.write(session=session, directory=directory, filePrefix=filePrefix)
    
def writeOrthoGageFile(projectFile, session, directory, filePrefix):
    '''
    Initiate Write Orthographic Gage File Method
    '''
    orthoGageFile = projectFile.orthoGageFile
    orthoGageFile.write(session=session, directory=directory, filePrefix=filePrefix)
    
def writeGridPipeFile(projectFile, session, directory, filePrefix):
    '''
    Initiate Write Grid Pipe File Method
    '''
    gridPipeFile = projectFile.gridPipeFile
    gridPipeFile.write(session=session, directory=directory, filePrefix=filePrefix)