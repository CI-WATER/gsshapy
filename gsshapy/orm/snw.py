"""
********************************************************************************
* Name: SnowSimulationModel
* Author: Nathan Swain
* Created On: May 16, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from __future__ import unicode_literals

__all__ = ['NwsrfsFile',
           'NwsrfsRecord',
           'OrographicGageFile',
           'OrographicMeasurement']

from datetime import datetime

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float, DateTime, String
from sqlalchemy.orm import relationship

from . import DeclarativeBase
from ..base.file_base import GsshaPyFileObjectBase


class NwsrfsFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for the NWSRFS Snow File.

    The contents of this file is abstracted into one supporting object: :class:`.NwsrfsRecord`.

    See: `GSSHAWIKI <http://www.gsshawiki.com/Snow_Card_Inputs_-_Optional>`_ 
    """
    __tablename__ = 'snw_nwsrfs_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK

    # Value Columns
    numBands = Column(Integer, nullable=False)  #: INTEGER
    fileExtension = Column(String, default='txt')  #: STRING

    # Relationship Properties
    nwsrfsRecords = relationship('NwsrfsRecord', back_populates='nwsrfsFile')  #: RELATIONSHIP
    projectFile = relationship('ProjectFile', uselist=False, back_populates='nwsrfsFile')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
        """
        NWSRFS Read from File Method
        """
        # Set file extension property
        self.fileExtension = extension

        # Open file and parse
        with open(path, 'r') as nwsrfsFile:
            for line in nwsrfsFile:
                sline = line.strip().split()

                # Cases
                if sline[0].lower() == 'number_bands:':
                    self.numBands = sline[1]
                elif sline[0].lower() == 'lower_elevation':
                    """DO NOTHING"""
                else:
                    # Create GSSHAPY NwsrfsRecord object
                    record = NwsrfsRecord(lowerElev=sline[0],
                                          upperElev=sline[1],
                                          mfMin=sline[2],
                                          mfMax=sline[3],
                                          scf=sline[4],
                                          frUse=sline[5],
                                          tipm=sline[6],
                                          nmf=sline[7],
                                          fua=sline[8],
                                          plwhc=sline[9])

                    # Associate NwsrfsRecord with NwsrfsFile
                    record.nwsrfsFile = self

    def _write(self, session, openFile, replaceParamFile):
        """
        NWSRFS Write to File Method
        """
        # Write lines
        openFile.write('Number_Bands:    %s\n' % self.numBands)
        openFile.write('Lower_Elevation  Upper_Elevation  MF_Min  MF_Max  SCF  FR_USE  TIPM  NMF  FUA  PCWHC\n')

        # Retrieve NwsrfsRecords
        records = self.nwsrfsRecords

        for record in records:
            openFile.write('%s%s%s%s%.1f%s%.1f%s%.1f%s%.1f%s%.1f%s%.1f%s%.1f%s%.1f\n' % (
                record.lowerElev,
                ' ' * (17 - len(str(record.lowerElev))),  # Num Spaces
                record.upperElev,
                ' ' * (17 - len(str(record.upperElev))),  # Num Spaces
                record.mfMin,
                ' ' * (8 - len(str(record.mfMin))),  # Num Spaces
                record.mfMax,
                ' ' * (8 - len(str(record.mfMax))),  # Num Spaces
                record.scf,
                ' ' * (5 - len(str(record.scf))),  # Num Spaces
                record.frUse,
                ' ' * (8 - len(str(record.frUse))),  # Num Spaces
                record.tipm,
                ' ' * (6 - len(str(record.tipm))),  # Num Spaces
                record.nmf,
                ' ' * (5 - len(str(record.nmf))),  # Num Spaces
                record.fua,
                ' ' * (5 - len(str(record.fua))),  # Num Spaces
                record.plwhc))


class NwsrfsRecord(DeclarativeBase):
    """
    Object containing data for a single NWSRFS record from the NWSRFS snow file.
    """
    __tablename__ = 'snw_nwsrfs_records'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    nwsrfsFileID = Column(Integer, ForeignKey('snw_nwsrfs_files.id'))  #: FK

    # Value Columns
    lowerElev = Column(Integer, nullable=False)  #: INTEGER
    upperElev = Column(Integer, nullable=False)  #: INTEGER
    mfMin = Column(Float, nullable=False)  #: FLOAT
    mfMax = Column(Float, nullable=False)  #: FLOAT
    scf = Column(Float, nullable=False)  #: FLOAT
    frUse = Column(Float, nullable=False)  #: FLOAT
    tipm = Column(Float, nullable=False)  #: FLOAT
    nmf = Column(Float, nullable=False)  #: FLOAT
    fua = Column(Float, nullable=False)  #: FLOAT
    plwhc = Column(Float, nullable=False)  #: FLOAT

    # Relationship Properties
    nwsrfsFile = relationship('NwsrfsFile', back_populates='nwsrfsRecords')  #: RELATIONSHIP

    def __init__(self, lowerElev, upperElev, mfMin, mfMax, scf, frUse, tipm, nmf, fua, plwhc):
        """
        Constructor
        """
        self.lowerElev = lowerElev
        self.upperElev = upperElev
        self.mfMin = mfMin
        self.mfMax = mfMax
        self.scf = scf
        self.frUse = frUse
        self.tipm = tipm
        self.nmf = nmf
        self.fua = fua
        self.plwhc = plwhc


    def __repr__(self):
        return '<ElevationNWSRFS: LowerElev=%s, UpperElev=%s, MFMin=%s, MFMax=%s, SCF=%s, FRUse=%s, TIPM=%s, NMF=%s, FUA=%s, PLWHC=%s>' % (
            self.lowerElev,
            self.upperElev,
            self.mfMin,
            self.mfMax,
            self.scf,
            self.frUse,
            self.tipm,
            self.nmf,
            self.fua,
            self.plwhc)


class OrographicGageFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for the Orographic Gage File.

    The contents of this file is abstracted into one supporting object: :class:`.OrographicMeasurement`.

    See: `GSSHAWIKI <http://www.gsshawiki.com/Snow_Card_Inputs_-_Optional>`_ 
    """
    __tablename__ = 'snw_orographic_gage_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK

    # Value Columns
    numSites = Column(Integer, nullable=False)  #: INTEGER
    elevBase = Column(Float, nullable=False)  #: FLOAT
    elev2 = Column(Float, nullable=False)  #: FLOAT
    fileExtension = Column(String, default='txt')  #: STRING

    # Relationship Properties
    orographicMeasurements = relationship('OrographicMeasurement', back_populates='orographicGageFile')  #: RELATIONSHIP
    projectFile = relationship('ProjectFile', uselist=False, back_populates='orographicGageFile')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
        """
        Orographic Gage File Read from File Method
        """
        # Set file extension property
        self.fileExtension = extension

        # Open file and parse into HmetRecords
        with open(path, 'r') as orthoFile:
            for line in orthoFile:
                sline = line.strip().split()

                # Cases
                if sline[0].lower() == 'num_sites:':
                    self.numSites = sline[1]
                elif sline[0].lower() == 'elev_base':
                    self.elevBase = sline[1]
                elif sline[0].lower() == 'elev_2':
                    self.elev2 = sline[1]
                elif sline[0].lower() == 'year':
                    """DO NOTHING"""
                else:
                    # Create datetime object
                    dateTime = datetime(year=int(sline[0]),
                                        month=int(sline[1]),
                                        day=int(sline[2]),
                                        hour=int(sline[3]))

                    # Create GSSHAPY OrthoMeasurement object
                    measurement = OrographicMeasurement(dateTime=dateTime,
                                                        temp2=sline[4])

                    # Associate OrthoMeasurement with OrthographicGageFile
                    self.orographicMeasurements.append(measurement)

    def _write(self, session, openFile, replaceParamFile):
        """
        Orographic Gage File Write to File Method
        """
        # Write lines
        openFile.write('Num_Sites:    %s\n' % self.numSites)
        openFile.write('Elev_Base     %s\n' % self.elevBase)
        openFile.write('Elev_2        %s\n' % self.elev2)
        openFile.write('Year    Month   Day     Hour    Temp_2\n')

        # Retrieve OrographicMeasurements
        measurements = self.orographicMeasurements

        for measurement in measurements:
            dateTime = measurement.dateTime
            openFile.write('%s%s%s%s%s%s%s%s%.3f\n' % (
                dateTime.year,
                '    ',
                dateTime.month,
                ' ' * (8 - len(str(dateTime.month))),
                dateTime.day,
                ' ' * (8 - len(str(dateTime.day))),
                dateTime.hour,
                ' ' * (8 - len(str(dateTime.hour))),
                measurement.temp2))


class OrographicMeasurement(DeclarativeBase):
    """
    Object containing data for a single orographic gage as defined in the orographic gage file.
    """
    __tablename__ = 'snw_orographic_measurements'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    orthoGageID = Column(Integer, ForeignKey('snw_orographic_gage_files.id'))  #: FK

    # Value Columns
    dateTime = Column(DateTime)  #: DATETIME
    temp2 = Column(Float)  #: FLOAT

    # Relationship Properties
    orographicGageFile = relationship('OrographicGageFile', back_populates='orographicMeasurements')  #: RELATIONSHIP

    def __init__(self, dateTime, temp2):
        """
        Constructor
        """
        self.dateTime = dateTime
        self.temp2 = temp2

    def __repr__(self):
        return '<OroMeasurement: DateTime=%s, Temp2=%s>' % (self.dateTime, self.temp2)
