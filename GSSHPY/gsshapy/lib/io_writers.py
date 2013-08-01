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
    '''
    Initiate Write Mapping Table File Method
    '''
    mapTableFile = projectFile.mapTableFile
    mapTableFile.write(session=session, directory=directory, filename=filename)

def writeChannelInputFile(projectFile, session, directory, filename):    
    '''
    Initiate Write Channel Input File Method
    '''
    channelInputFile = projectFile.channelInputFile
    channelInputFile.write(session=session, directory=directory, filename=filename)

def writePrecipitationFile(projectFile, session, directory, filename):   
    '''
    Initiate Write Precipitation File Method
    '''
    precipFile = projectFile.precipFile
    precipFile.write(session=session, directory=directory, filename=filename)

def writePipeNetworkFile(projectFile, session, directory, filename):   
    '''
    Initiate Write Storm Pipe Network File Method
    '''
    pipeFile = projectFile.stormPipeNetworkFile
    pipeFile.write(session=session, directory=directory, filename=filename)
    
def writeHmetFile(projectFile, session, directory, filename):
    '''
    Initiate Write HMET File Method
    '''
    hmetFile = projectFile.hmetFile
    hmetFile.writeWES(session=session, directory=directory, filename=filename)
    
def writeNwsrfsFile(projectFile, session, directory, filename):
    '''
    Initiate Write NWSRFS File Method
    '''
    nwsrfsFile = projectFile.nwsrfsFile
    nwsrfsFile.write(session=session, directory=directory, filename=filename)
    
def writeOrthoGageFile(projectFile, session, directory, filename):
    '''
    Initiate Write Orthographic Gage File Method
    '''
    orthoGageFile = projectFile.orthoGageFile
    orthoGageFile.write(session=session, directory=directory, filename=filename)
    
def writeGridPipeFile(projectFile, session, directory, filename):
    '''
    Initiate Write Grid Pipe File Method
    '''
    gridPipeFile = projectFile.gridPipeFile
    gridPipeFile.write(session=session, directory=directory, filename=filename)
    
def writeGridStreamFile(projectFile, session, directory, filename):
    '''
    Initiate Write Grid Stream File Method
    '''
    gridStreamFile = projectFile.gridStreamFile
    gridStreamFile.write(session=session, directory=directory, filename=filename)
    
def writeTimeSeriesFile(projectFile, session, directory, filename):
    '''
    Initiate Write Generic Time Series File Method
    '''
    extension = filename.split('.')[1]
    
    # Retrieve appropriate time series file
    timeSeriesFiles = projectFile.timeSeriesFiles
    
    for tsf in timeSeriesFiles:
        if tsf.fileExtension == extension:
            timeSeriesFile = tsf
    
    timeSeriesFile.write(session=session, directory=directory, filename=filename)
    