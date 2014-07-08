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
        filename_split = filename.split('.')
        name = filename_split[0]

        # Default file extension
        extension = ''

        if len(filename_split) >= 2:
            extension = filename_split[-1]

        if os.path.isfile(path):
            # Add self to session
            session.add(self)

            # Read
            success = self._read(directory, filename, session, path, name, extension, spatial, spatialReferenceID, raster2pgsqlPath)

            # Commit to database
            self._commit(session, self.COMMIT_ERROR_MESSAGE)
        else:
            # Rollback the session if the file doesn't exist
            session.rollback()

            # Issue warning
            print 'WARNING: {0} listed in project file, but no such file exists.'.format(filename)

    def write(self, session, directory, name):
        """
        Write from database to file.

        *session* = SQLAlchemy session object\n
        *directory* = to which directory will the files be written (e.g.: '/example/path')\n
        *name* = name of file that will be written (e.g.: 'my_project.ext')\n
        """

        # Assemble Path to file
        name_split = name.split('.')
        name = name_split[0]

        # Default extension
        extension = ''

        if len(name_split) >= 2:
            extension = name_split[-1]
            
        # Run name preprocessor method if present
        try:
            name = self._namePreprocessor(name)
        except:
            '''DO NOTHING'''

        if extension == '':
            filename = '{0}.{1}'.format(name, self.fileExtension)
        else:
            filename = '{0}.{1}'.format(name, extension)

        filePath = os.path.join(directory, filename)
        
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
        
    def _write(self, session, openFile):
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
        :param openFile: The file object of the file that will be written
        """
