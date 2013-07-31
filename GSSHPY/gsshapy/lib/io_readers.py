'''
********************************************************************************
* Name: Input File Readers
* Author: Nathan Swain
* Created On: July 29, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''
from gsshapy.orm.cmt import MapTableFile
from gsshapy.orm.gag import PrecipFile
from gsshapy.orm.cif import ChannelInputFile
from gsshapy.orm.spn import StormPipeNetworkFile
from gsshapy.orm.hmet import HmetFile
from gsshapy.orm.snw import NwsrfsFile, OrthographicGageFile
from gsshapy.orm.gpi import GridPipeFile
from gsshapy.orm.gst import GridStreamFile
from gsshapy.orm.timeseries import TimeSeriesFile

## TODO: Write a generic method that can be used to read files similar to this:
def readGeneric(projectFile, fileIO, filename):
    instance = fileIO(directory=projectFile.DIRECTORY, filename=filename, session=projectFile.SESSION)
    instance.projectFile = projectFile
    instance.read()
    

def readMappingTableFile(projectFile, filename):
    '''
    Initiate Read Mapping Table File Method
    '''
    # Initiate GSSHAPY MapTableFile object, associate with this object, and read map table file
    mapTable = MapTableFile(directory=projectFile.DIRECTORY, filename=filename, session=projectFile.SESSION)
    mapTable.projectFile = projectFile
    mapTable.read()
    print 'Mapping Table File Read'

def readPrecipitationFile(projectFile, filename):
    '''
    Initiate Read Precipitation File Method
    '''
    # Initiate GSSHAPY PrecipFile object, associate it with this object, and read precipitation file
    precip = PrecipFile(directory=projectFile.DIRECTORY, filename=filename, session=projectFile.SESSION)
    precip.projectFile = projectFile
    precip.read()
    print 'Precipitation File Read'
    
def readPipeNetworkFile(projectFile, filename):
    '''
    Initiate Read Storm Pipe Network File Method
    '''
    # Initiate GSSHAPY StormPipeNetworkFile object, associate with this object, and read file
    pipeNetworkFile = StormPipeNetworkFile(directory=projectFile.DIRECTORY, filename=filename, session=projectFile.SESSION)
    pipeNetworkFile.projectFile = projectFile
    pipeNetworkFile.read()
    print 'Pipe Network File Read'
    
def readChannelInputFile(projectFile, filename):
    '''
    Initiate Read Channel Input File Method
    '''
    # Initiate GSSHAPY ChannelNetworkFile object, associate with this object, and read channel input file
    channelInputFile = ChannelInputFile(directory=projectFile.DIRECTORY, filename=filename, session=projectFile.SESSION)
    channelInputFile.projectFile = projectFile
    channelInputFile.read()
    print 'Channel Input File Read'
    
    
def readNwsrfsFile(projectFile, filename):
    '''
    Initiate Read NWSRFS File Method
    '''
    nwsrfs = NwsrfsFile(directory=projectFile.DIRECTORY, filename=filename, session=projectFile.SESSION)
    nwsrfs.projectFile = projectFile
    nwsrfs.read()
    print 'NWSRFS File Read'
    
def readOrthoGageFile(projectFile, filename):
    orthoGage = OrthographicGageFile(directory=projectFile.DIRECTORY, filename=filename, session=projectFile.SESSION)
    orthoGage.projectFile = projectFile
    orthoGage.read()
    print 'Orthographic Gage File Read'
    
def readGridPipeFile(projectFile, filename):
    gridPipeFile = GridPipeFile(directory=projectFile.DIRECTORY, filename=filename, session=projectFile.SESSION)
    gridPipeFile.projectFile = projectFile
    gridPipeFile.read()
    print 'Grid Pipe File Read'
    
def readGridStreamFile(projectFile, filename):
    gridStreamFile = GridStreamFile(directory=projectFile.DIRECTORY, filename=filename, session=projectFile.SESSION)
    gridStreamFile.projectFile = projectFile
    gridStreamFile.read()
    print 'Grid Stream File Read'
    
def readHmetWesFile(projectFile, filename):
    '''
    Initiate Read HMET_WES File Method
    '''
    hmet = HmetFile(directory=projectFile.DIRECTORY, filename=filename, session=projectFile.SESSION)
    hmet.projectFile = projectFile
    hmet.readWES()
    print 'HMET WES File Read'
    
def readTimeSeriesFile(projectFile, filename):
    timeSeriesFile = TimeSeriesFile(directory=projectFile.DIRECTORY, filename=filename, session=projectFile.SESSION)
    timeSeriesFile.projectFile = projectFile
    timeSeriesFile.read()
    print 'Time Series Read:', filename.split('.')[1]
                   
