'''
********************************************************************************
* Name: PrecipitationModel
* Author: Nathan Swain
* Created On: Mar 6, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['PrecipFile',
           'PrecipEvent',
           'PrecipValue',
           'PrecipGage']

from datetime import datetime

from sqlalchemy import ForeignKey, Column, Table
from sqlalchemy.types import Integer, DateTime, String, Float
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase, metadata
from gsshapy.lib import gpparse, pivot

assocPrecip = Table('assoc_precipitation_files_events', metadata,
    Column('precipFileID', Integer, ForeignKey('gag_precipitation_files.id')),
    Column('precipEventID', Integer, ForeignKey('gag_events.id'))
    )

class PrecipFile(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gag_precipitation_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Relationship Properties
    precipEvents = relationship('PrecipEvent', secondary=assocPrecip, back_populates='precipFiles')
    projectFile = relationship('ProjectFile', uselist=False, back_populates='precipFile')
    
    # Global Properties
    PATH = ''
    FILENAME = ''
    DIRECTORY = ''
    SESSION = None
    EXTENSION = 'gag'
    
    # This is the structure used by gpparse to read in the file
    STRUCTURE =\
        [ 
            ["R", None,
                [
                    ["R", 1, ["C", "D", "T-EDESC"]],
                    ["R", 1, ["C", "D", "I-PPP"]],
                    ["R", 1, ["C", "D", "I-PPP"]],
                    ["R", "NRGAG", ["C", "D", "F-X", "F-Y", "T-CDESC"]],
                    ["R", "NRPDS" , ["C", "T-TYPE", "I-YEAR", "I-MONTH", "I-DAY", "I-HOUR", "I-MIN", ["R", "NRGAG", ["C", "F-GAGVAL"]]]]
                ]
             ]
        ]
        
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        self.FILENAME = filename
        self.DIRECTORY = directory
        self.SESSION = session
        self.PATH = '%s%s' % (self.DIRECTORY, self.FILENAME)
    
    def read(self):
        '''
        Precipitation Read from File Method
        '''
        # List of GSSHAPY PrecipEvent Objects     
        evt = [] 
        
        # Parse file using gpparse. File object can be
        # accessed via the "list" attribute
        parsedFile= gpparse.gpparser(self.STRUCTURE, self.PATH)
        
        # Transform the gpparse list into a form that is easier to use
        events = self._transformGpparseArray(parsedFile.list)
                      
        for evtIndex, event in enumerate(events):
            # Determine which of the next two parameters
            # is NRGAG and which is NRPDS.
            if event[1][3] == 'NRGAG':
                ngag = int(event[1][5])
                npds = int(event[2][5])
            elif event[1][3] == 'NRPDS':
                ngag = int(event[2][5])
                npds = int(event[1][5])
            
            # Extract the event description
            edesc = event[0][5]
            
            # Create a new GSSHAPY PrecipEvent Object, add to this PrecipFile,
            # and append to list of PrecipEvents
            currEvt = PrecipEvent(description=edesc, numGages=ngag, numPeriods=npds)
            self.precipEvents.append(currEvt)
            evt.append(currEvt)
            
            # List of GSSHAPY PrecipGage objects for the current event
            gages = []
            
            
            if ngag > 0:
                for gageIndex in range(3, 3 + ngag):
                    # Extract x, y, and the coordinate description for
                    # the gage, create a GSSHAPY PrecipGage object,
                    # and append to list of PrecipGages
                    x=event[gageIndex][0][5]
                    y=event[gageIndex][1][5]
                    cdesc=event[gageIndex][2][5]
                    gages.append(PrecipGage(x=x, y=y, description=cdesc))
                
                for periodIndex in range(3 + ngag, 3 + ngag+ npds):
                    # Extract time of the current period and create a python 
                    # DataTime object
                    currType = event[periodIndex][0][5]
                    year = int(event[periodIndex][1][5])
                    month = int(event[periodIndex][2][5])
                    day = int(event[periodIndex][3][5])
                    hour = int(event[periodIndex][4][5])
                    minute = int(event[periodIndex][5][5])
                    currTime = datetime(year, month, day, hour, minute)
                    
                    
                    for gIndex, gage in enumerate(gages):
                        # Extract value for each gage at each time step, create a 
                        # GSSHAPY PrecipValue object, and assign appropriate event
                        # and gage
                        valIndex = gIndex + 6
                        currValue = float(event[periodIndex][valIndex][5])
                        val = PrecipValue(valueType=currType, dateTime=currTime, value=currValue)
                        val.event = evt[evtIndex]
                        val.gage = gage
            else:
                ''' 
                This is where code would go to handle the special case of gridded radar
                datasets passed in through the precipitation file. The logic of the parser
                breaks down for this case because the NRGAG is set to -1. At this point, 
                the best option may be to reparse the file to find these cases. For now
                The precipitation file reader will not support gridded RADAR rainfall.
                '''
                
        # Add this PrecipFile to the database session
        self.SESSION.add(self)
                
    def write(self, session, directory, filename):
        '''
        Precipitation Write to File Method
        '''
        # Assemble path to new precipitation file
        path = '%s%s' % (directory, filename)
        
        # Initialize file
        with open(path, 'w') as gagFile:
            # Retrieve the events associated with this PrecipFile
            events = self.precipEvents
            
            # Write each event to file
            for event in events:
                gagFile.write('EVENT %s\nNRGAG %s\nNRPDS %s\n' % (event.description, event.nrGag, event.nrPds))
                
                if event.nrGag > 0:
                    values = event.values
                    
                    valList = []
                    
                    # Convert PrecipValue objects into a list of dictionaries, valList,
                    # so that it is compatible with the pivot function.
                    for value in values:
                        valList.append({
                                'ValueType': value.valueType,
                                'DateTime': value.dateTime,
                                'Gage': value.gage.id,
                                'Value': value.value
                                })
                    
                    # Pivot using the function found at:
                    # code.activestate.com/recipes/334695
                    pivotedValues = pivot.pivot(valList, ('DateTime', 'ValueType'), ('Gage',), 'Value')
                    
                    ## TODO: Create custom pivot function that can work with sqlalchemy 
                    ## objects explicitly without the costly conversion.
                    
                    # Create an empty set for obtaining a list of unique gages
                    gages = set()
                    
                    # Get a list of unique gages
                    for value in values:
                        gages.add(value.gage)
                    
                    for gage in gages:
                        gagFile.write('COORD %s %s %s\n' % (gage.x, gage.y, gage.description))

                    # Write the value rows out to file
                    for row in pivotedValues:
                        
                        # Extract ValueType and DateTime
                        valType = row['ValueType']
                        year = row['DateTime'].year
                        month = row['DateTime'].month
                        day = row['DateTime'].day
                        hour = row['DateTime'].hour
                        minute = row['DateTime'].minute
                        
                        # Extract the PrecipValues
                        valString = ''
                        
                        # Retreive a lit of sorted keys. This assumes the values are 
                        # read into the database in order
                        keys = sorted(row)
                        
                        # String all of the values together into valString
                        for key in keys:
                            if key <> 'DateTime' and key <> 'ValueType':
                                valString = '%s  %.2f' % (valString, row[key])

                        # Write value line to file with appropriate formatting
                        gagFile.write('%s %.4d %.2d  %.2d  %.2d  %.2d%s\n' % (valType, year, month, day, hour, minute, valString))
                
    def _transformGpparseArray(self, gagList):
        ''' 
        This method is used to transform the gpparse results 
        into something that is easier to work with for reading
        the file into the database. A list of events is returned.
        The precipitation gages and values are appended to each
        event.
        '''
        ## TODO: Consider refactoring events into an dictionary for more
        ## readable code.
        
        events = []
        
        for item in gagList:
            if item[3] == 'EDESC':
                currEvent = [item]
                events.append(currEvent)
            elif item[3] == 'NRGAG':
                currEvent.append(item)
            elif item[3] == 'NRPDS':
                currEvent.append(item)
            elif item[3] == 'X':
                currCoord = [item]
                currEvent.append(currCoord)
            elif item[3] == 'Y':
                currCoord.append(item)
            elif item[3] == 'CDESC':
                currCoord.append(item)
            elif item[3] == 'TYPE':
                currVal = [item]
                currEvent.append(currVal)
            else:
                currVal.append(item)
        
        # Return the list of events
        return events
                
class PrecipEvent(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gag_events'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    description = Column(String, nullable=False)
    nrGag = Column(Integer, nullable=False)
    nrPds = Column(Integer, nullable=False)
    
    # Relationship Properties
    values = relationship('PrecipValue', back_populates='event')
    precipFiles = relationship('PrecipFile', secondary=assocPrecip, back_populates='precipEvents')
    
    def __init__(self, description, numGages, numPeriods):
        '''
        Constructor
        '''
        #TODO - add validation
        self.description = description
        self.nrGag = numGages
        self.nrPds = numPeriods
        

    def __repr__(self):
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.description,self.nrGag,self.nrPds)
    
    
class PrecipValue(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gag_values'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    eventID = Column(Integer, ForeignKey('gag_events.id'))
    coordID = Column(Integer, ForeignKey('gag_coord.id'))
    
    # Value Columns
    valueType = Column(String, nullable=False)
    dateTime = Column(DateTime, nullable=False)
    value = Column(Float, nullable=False)
    
    # Relationship Properties
    event = relationship('PrecipEvent', back_populates='values')
    gage = relationship('PrecipGage', back_populates='values')

    def __init__(self, valueType, dateTime, value):
        '''
        Constructor
        '''
        self.valueType = valueType
        self.dateTime = dateTime
        self.value = value
        

    def __repr__(self):
        return '<PrecipValue: Type=%s, DateTime=%s, Value=%s>' % (self.valueType, self.dateTime, self.value)
    

    
class PrecipGage(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'gag_coord'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    description = Column(String)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    
    # Relationship Properties
    values = relationship('PrecipValue', back_populates='gage')
    
    def __init__(self, description, x, y):
        '''
        Constructor
        '''
        self.description = description
        self.x = x
        self.y = y
        

    def __repr__(self):
        return '<PrecipGage: Description=%s, UTM Northing=%s, UTM Easting=%s>' % (self.description, self.x, self.y)
