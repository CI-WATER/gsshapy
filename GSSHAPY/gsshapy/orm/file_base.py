"""
********************************************************************************
* Name: Gssha File Object Base
* Author: Nathan Swain
* Created On: August 2, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

import os

from sqlalchemy.exc import IntegrityError

__all__ = ['GsshaPyFileObjectBase']


class GsshaPyFileObjectBase:
    """
    Abstract base class of all file objects in the GsshaPy ORM. Each file object has two methods: read and write. These
    methods in turn call the private _read and _write methods which must be implemented by the file classes.
    """
    
    # File Properties
    PROPER_NAME = None
    PROJECT_NAME = None
    EXTENSION = 'txt'
    
    # Error Messages
    COMMIT_ERROR_MESSAGE = 'Ensure the file is not empty and try again.'
    
    def __init__(self):
        """
        Constructor
        """

    def read(self, directory, filename, session, spatial=False, spatialReferenceID=4236, raster2pgsqlPath='raster2pgsql'):
        """
        Read file into the database.
        """

        # Read parameter derivatives
        path = os.path.join(directory, filename)
        name = filename.split('.')[0]
        extension = filename.split('.')[1]

        # Ensure file exists prior to reading in
        if os.path.exists(path):
            # Add self to session
            session.add(self)

            # Read
            success = self._read(directory, filename, session, path, name, extension, spatial, spatialReferenceID, raster2pgsqlPath)

            # Commit to database
            self._commit(session, self.COMMIT_ERROR_MESSAGE)
        else:
            # Rollback the session if the file doesn't exist
            session.rollback()

    def write(self, session, directory, name):
        """
        Write from database to file.

        *session* = SQLAlchemy session object\n
        *directory* = to which directory will the files be written (e.g.: '/example/path')\n
        *name* = project name (e.g.: 'my_project')\n
        """
        # For future use
        self.SESSION = session
        self.DIRECTORY = directory

        # Assemble Path to file
        try:
            # Handle name with extension case (e.g.: name.ext)
            name, extension = name.split('.')   # Will fail if '.' not present
            
            if extension != self.EXTENSION:
                self.EXTENSION = extension
        except:
            '''DO NOTHING'''
            
        # Run name preprocessor method if present
        try:
            name=self._namePreprocessor(name)
        except:
            '''DO NOTHING'''
        
        # Handle name only case (e.g.: name). Append fileExtension.
        try:
            # Handles case where file object handles
            # files with varying extentions 
            # (e.g.: TimeSeriesFile).
            filename = '%s.%s' % (name, self.fileExtension)
            filePath = os.path.join(directory, filename)
        
        except:
            # Handles the case where file object handles
            # files with a set extension
            # (e.g.: MapTableFile).
            filename = '%s.%s' % (name, self.EXTENSION)
            filePath = os.path.join(directory, filename)
        
        # For use after the file has been written
        self.PATH = os.path.join(directory, filename)
        
        with open(filePath, 'w') as openFile:
            # Write Lines
            self._write(session=session,
                        openFile=openFile)
            
    def _commit(self, session, errorMessage):
        """
        Custom commit function for file objects
        """
        try:
            session.commit()
        except IntegrityError:
            # Raise special error if the commit fails due to empty files
            print 'ERROR: Commit to database failed. %s' % errorMessage            
        except:
            # Raise other errors as normal
            raise
    
    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, raster2pgsqlPath):
        """
        This Private method must be defined in each file object for
        the read() method to work properly.The intent of the method
        is to prevent unnecessary commits. The method should read the
        file into GSSHAPY objects and associate them with the file
        object via relationship properties without committing to the
        database. The read() method associates the file object to
        the session, calls this method, and then performs the commit
        to the database.


        This is useful for methods that read multiple files (e.g.:
        ProjectFile.readProject()). They call this method directly,
        associate each file object with the ProjectFile object and
        commit once at the end of reading files.

        :param directory: The directory containing all the GSSHA input files (e.g.: /path/to/example
        :param filename: The filename of the file to be read (e.g.: example.ext)
        :param session: The SQLAlchemy session that will be used to connect to the database being read in
        :param path: Full path to the file being read
        :param name: Name of the file without the extension
        :param extension: The extension of the file
        :param spatial: Boolean representing whether or not the files should be read in as spatial features (PostGIS DBs only)
        :param spatialReferenceID: The spatial reference ID for the GSSHA model
        :param raster2pgsqlPath: The path to the commandline tool that generates SQL for the raster read
        """
        
    def _write(self, session, directory, openFile):
        """
        This private method must be defined in each file object for
        the write() method to work properly. The write() method handles
        assembly of the file path and initializing the file for writing

        (i.e.: opening the file). The open file object is passed to
        this method to allow this method to write the lines to the file
        and perform any logic that is necessary to do so (retrieve
        file data from database and pivot).

        Some files have special naming conventions. In these cases,
        override the write() method and write a custom method.

        :param session: The SQLAlchemy session object that will be used to retrieve the data from the database
        :param directory: The directory to which the file will be written
        :param openFile: The file object of the file that will be written
        """
