"""
********************************************************************************
* Name: PrecipitationModel
* Author: Nathan Swain
* Created On: Mar 6, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from __future__ import unicode_literals

__all__ = ['PrecipFile',
           'PrecipEvent',
           'PrecipValue',
           'PrecipGage']

from future.utils import iteritems
from sqlalchemy import ForeignKey, Column, Table
from sqlalchemy.types import Integer, DateTime, String, Float
from sqlalchemy.orm import relationship

from . import DeclarativeBase
from ..base.file_base import GsshaPyFileObjectBase
from ..lib import pivot, parsetools as pt, gag_chunk as gak


gag_assoc_event_gage = Table('gag_assoc_event_gage', DeclarativeBase.metadata,
                             Column('gageID', Integer, ForeignKey('gag_coord.id')),
                             Column('eventID', Integer, ForeignKey('gag_events.id')))


class PrecipFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for the Precipitation Input File.

    The contents of the precipitation file are abstracted into three types of objects including: :class:`.PrecipEvent`,
    :class:`.PrecipValue`, and :class:`.PrecipGage`. One precipitation file can consist of multiple events and each event
    can have several gages and a time series of values for each gage.

    See: http://www.gsshawiki.com/Precipitation:Spatially_and_Temporally_Varied_Precipitation
    """
    __tablename__ = 'gag_precipitation_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK

    # Value Columns
    fileExtension = Column(String, default='gag')  #: STRING

    # Relationship Properties
    precipEvents = relationship('PrecipEvent', back_populates='precipFile')  #: RELATIONSHIP
    projectFile = relationship('ProjectFile', uselist=False, back_populates='precipFile')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
        """
        Precipitation Read from File Method
        """
        # Set file extension property
        self.fileExtension = extension

        # Dictionary of keywords/cards and parse function names
        KEYWORDS = ('EVENT',)

        # Parse file into chunks associated with keywords/cards
        with open(path, 'r') as f:
            chunks = pt.chunk(KEYWORDS, f)

        # Parse chunks associated with each key
        for key, chunkList in iteritems(chunks):
            # Parse each chunk in the chunk list
            for chunk in chunkList:
                result = gak.eventChunk(key, chunk)
                self._createGsshaPyObjects(result)

        # Add this PrecipFile to the database session
        session.add(self)

    def _write(self, session, openFile, replaceParamFile):
        """
        Precipitation File Write to File Method
        """
        # Retrieve the events associated with this PrecipFile
        events = self.precipEvents

        # Write each event to file
        for event in events:
            openFile.write('EVENT "%s"\nNRGAG %s\nNRPDS %s\n' % (event.description, event.nrGag, event.nrPds))

            if event.nrGag > 0:
                values = event.values

                valList = []

                # Convert PrecipValue objects into a list of dictionaries, valList,
                # so that it is compatible with the pivot function.
                for value in values:
                    valList.append({'ValueType': value.valueType,
                                    'DateTime': value.dateTime,
                                    'Gage': value.gage.id,
                                    'Value': value.value})

                # Pivot using the function found at:
                # code.activestate.com/recipes/334695
                pivotedValues = pivot.pivot(valList, ('DateTime', 'ValueType'), ('Gage',), 'Value')

                ## TODO: Create custom pivot function that can work with sqlalchemy
                ## objects explicitly without the costly conversion.

                # Create an empty set for obtaining a list of unique gages
                gages = session.query(PrecipGage). \
                    filter(PrecipGage.event == event). \
                    order_by(PrecipGage.id). \
                    all()

                for gage in gages:
                    openFile.write('COORD %s %s "%s"\n' % (gage.x, gage.y, gage.description))

                # Write the value rows out to file
                for row in pivotedValues:
                    # Extract the PrecipValues
                    valString = ''

                    # Retreive a list of sorted keys. This assumes the values are
                    # read into the database in order
                    keys = sorted([key for key in row if key != 'DateTime' and key != 'ValueType'])

                    # String all of the values together into valString
                    for key in keys:
                        if key != 'DateTime' and key != 'ValueType':
                            valString = '%s %.3f' % (valString, row[key])

                    # Write value line to file with appropriate formatting
                    openFile.write('%s %.4d %.2d %.2d %.2d %.2d%s\n' % (
                        row['ValueType'],
                        row['DateTime'].year,
                        row['DateTime'].month,
                        row['DateTime'].day,
                        row['DateTime'].hour,
                        row['DateTime'].minute,
                        valString))

    def _createGsshaPyObjects(self, eventChunk):
        """
        Create GSSHAPY PrecipEvent, PrecipValue, and PrecipGage Objects Method
        """
        ## TODO: Add Support for RADAR file format type values

        # Create GSSHAPY PrecipEvent
        event = PrecipEvent(description=eventChunk['description'],
                            nrGag=eventChunk['nrgag'],
                            nrPds=eventChunk['nrpds'])

        # Associate PrecipEvent with PrecipFile
        event.precipFile = self

        gages = []
        for coord in eventChunk['coords']:
            # Create GSSHAPY PrecipGage object
            gage = PrecipGage(description=coord['description'],
                              x=coord['x'],
                              y=coord['y'])

            # Associate PrecipGage with PrecipEvent
            gage.event = event

            # Append to gages list for association with PrecipValues
            gages.append(gage)

        for valLine in eventChunk['valLines']:
            for index, value in enumerate(valLine['values']):
                # Create GSSHAPY PrecipValue object
                val = PrecipValue(valueType=valLine['type'],
                                  dateTime=valLine['dateTime'],
                                  value=value)

                # Associate PrecipValue with PrecipEvent and PrecipGage
                val.event = event
                val.gage = gages[index]


class PrecipEvent(DeclarativeBase):
    """
    Object containing data for a single precipitation event.
    """
    __tablename__ = 'gag_events'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    precipFileID = Column(Integer, ForeignKey('gag_precipitation_files.id'))  #: FK

    # Value Columns
    description = Column(String)  #: STRING
    nrGag = Column(Integer)  #: INTEGER
    nrPds = Column(Integer)  #: INTEGER

    # Relationship Properties
    values = relationship('PrecipValue', back_populates='event')  #: RELATIONSHIP
    gages = relationship('PrecipGage', secondary=gag_assoc_event_gage, back_populates='event')  #: RELATIONSHIP
    precipFile = relationship('PrecipFile', back_populates='precipEvents')  #: RELATIONSHIP

    def __init__(self, description, nrGag, nrPds):
        """
        Constructor
        """
        self.description = description
        self.nrGag = nrGag
        self.nrPds = nrPds


    def __repr__(self):
        return '<PrecipEvent: Description=%s, NumGages=%s, NumPeriods=%s>' % (self.description, self.nrGag, self.nrPds)


class PrecipValue(DeclarativeBase):
    """
    Object containing data for a single time stamped precipitation value.
    """
    __tablename__ = 'gag_values'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    eventID = Column(Integer, ForeignKey('gag_events.id'))  #: FK
    coordID = Column(Integer, ForeignKey('gag_coord.id'))  #: FK

    # Value Columns
    valueType = Column(String)  #: STRING
    dateTime = Column(DateTime)  #: DATETIME
    value = Column(Float)  #: FLOAT

    # Relationship Properties
    event = relationship('PrecipEvent', back_populates='values')  #: RELATIONSHIP
    gage = relationship('PrecipGage', back_populates='values')  #: RELATIONSHIP

    def __init__(self, valueType, dateTime, value):
        """
        Constructor
        """
        self.valueType = valueType
        self.dateTime = dateTime
        self.value = value

    def __repr__(self):
        return '<PrecipValue: Type=%s, DateTime=%s, Value=%s>' % (self.valueType, self.dateTime, self.value)


class PrecipGage(DeclarativeBase):
    """
    Object containing data for a single precipitation gage or location.
    """
    __tablename__ = 'gag_coord'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK

    # Value Columns
    description = Column(String)  #: STRING
    x = Column(Float)  #: FLOAT
    y = Column(Float)  #: FLOAT
    #     geom = Column(Geometry('POINT')) #: POINT

    # Relationship Properties
    values = relationship('PrecipValue', back_populates='gage')  #: RELATIONSHIP
    event = relationship('PrecipEvent', secondary=gag_assoc_event_gage, uselist=False,
                         back_populates='gages')  #: RELATIONSHIP

    def __init__(self, description, x, y):
        """
        Constructor
        """
        self.description = description
        self.x = x
        self.y = y

    #         self.geom = 'POINT(%s %s)' % (x, y)

    def __repr__(self):
        return '<PrecipGage: Description=%s, X=%s, Y=%s>' % (self.description, self.x, self.y)
