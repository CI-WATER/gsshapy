"""
********************************************************************************
* Name: Gssha File Object Base
* Author: Nathan Swain
* Created On: August 2, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

from io import open as io_open
import logging
import os

from sqlalchemy.exc import IntegrityError

__all__ = ['GsshaPyFileObjectBase']

log = logging.getLogger(__name__)

class GsshaPyFileObjectBase:
    """
    Abstract base class for all file objects in the GsshaPy ORM.

    This base class provides two methods for reading and writing files: ``read()`` and ``write()``. These methods in
    turn call the private ``_read()`` and ``_write()`` methods which must be implemented by child classes.
    """
    # Error Messages
    COMMIT_ERROR_MESSAGE = 'Ensure the file is not empty and try again.'

    def __init__(self):
        """
        Constructor
        """
        self.fileExtension = ''

    def read(self, directory, filename, session, spatial=False,
             spatialReferenceID=4236, replaceParamFile=None, **kwargs):
        """
        Generic read file into database method.

        Args:
            directory (str): Directory containing the file to be read.
            filename (str): Name of the file which will be read (e.g.: 'example.prj').
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database.
            spatial (bool, optional): If True, spatially enabled objects will be read in as PostGIS spatial objects.
                Defaults to False.
            spatialReferenceID (int, optional): Integer id of spatial reference system for the model. Required if
                spatial is True. Defaults to srid 4236.
            replaceParamFile (:class:`gsshapy.orm.ReplaceParamFile`, optional): ReplaceParamFile instance. Use this if
                the file you are reading contains replacement parameters.
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
            self._read(directory, filename, session, path, name, extension,
                       spatial, spatialReferenceID, replaceParamFile, **kwargs)

            # Commit to database
            self._commit(session, self.COMMIT_ERROR_MESSAGE)
        else:
            # Rollback the session if the file doesn't exist
            session.rollback()

            # Print warning
            log.warn('Could not find file named {0}. File not read.'.format(filename))

    def write(self, session, directory, name, replaceParamFile=None, **kwargs):
        """
        Write from database back to file.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database.
            directory (str): Directory where the file will be written.
            name (str): The name of the file that will be created (including the file extension is optional).
            replaceParamFile (:class:`gsshapy.orm.ReplaceParamFile`, optional): ReplaceParamFile instance. Use this if
                the file you are writing contains replacement parameters.
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
            'DO NOTHING'

        if extension == '':
            filename = '{0}.{1}'.format(name, self.fileExtension)
        else:
            filename = '{0}.{1}'.format(name, extension)

        filePath = os.path.join(directory, filename)

        with io_open(filePath, 'w') as openFile:
            # Write Lines
            self._write(session=session,
                        openFile=openFile,
                        replaceParamFile=replaceParamFile,
                        **kwargs)

    def _commit(self, session, errorMessage):
        """
        Custom commit function for file objects
        """
        try:
            session.commit()
        except IntegrityError:
            # Raise special error if the commit fails due to empty files
            log.error('Commit to database failed. %s' % errorMessage)
        except:
            # Raise other errors as normal
            raise

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, replaceParamFile):
        """
        Private file object read method. Classes that inherit from this base class must implement this method.

        The ``read()`` method that each file object inherits from this base class performs the processes common to all
        file read methods, after which it calls the file object's ``_read()`` (the preceding underscore denotes that
        the method is a private method).

        The purpose of the ``_read()`` method is to perform the file read operations that are specific to the file that
        the file object represents. This method should add any supporting SQLAlchemy objects to the session without
        committing. The common ``read()`` method handles the database commit for all file objects.

        The ``read()`` method processes the user input and passes on the information through the many parameters of the
        ``_read()`` method. As the ``_read()`` method should never be called by the user directly, the arguments will
        be defined in terms of what they offer for the developer of a new file object needing to implement this method.

        Args:
            directory (str): Directory containing the file to be read. Same as given by user in ``read()``.
            filename (str): Name of the file which will be read (e.g.: 'example.prj'). Same as given by user. Same as
                given by user in ``read()``.
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled
                database. Same as given by user in ``read()``.
            path (str): Directory and filename combined into the path to the file. This is a convenience parameter.
            name (str): Name of the file without extension. This is a convenience parameter.
            extension (str): Extension of the file without the name. This is a convenience parameter.
            spatial (bool, optional): If True, spatially enabled objects will be read in as PostGIS spatial objects.
                Defaults to False. Same as given by user in ``read()``.
            spatialReferenceID (int, optional): Integer id of spatial reference system for the model. Required if
                spatial is True. Same as given by user in ``read()``.
            replaceParamFile (:class:`gsshapy.orm.ReplaceParamFile`, optional): Handle the case when replacement
                parameters are used in place of normal variables. If this is not None, then the user expects there
                to be replacement variables in the file. Use the gsshapy.lib.parsetools.valueReadPreprocessor() to
                handle these.
        """

    def _write(self, session, openFile, replaceParamFile):
        """
        Private file object write method. Classes that inherit from this base class must implement this method.

        The ``write()`` method that each file object inherits from this base class performs the processes common to all
        file write methods, after which it calls the file object's ``_write()`` (the preceding underscore denotes that
        the method is a private method).

        The purpose of the ``_write()`` method is to perform the write operations that are specific to the file that the
        file object represents. This method is passed Python file object that has been "opened". Thus, the developer
        implementing this method does not need to worry about paths, but simply writes to the opened file object.

        Some files have special naming conventions. In these cases, override the write() method and write a custom
        method.

        The ``write()`` method processes the user input and passes on the information to the ``_write()`` method.  As
        the ``_write()`` method should never be called by the user directly, the arguments will be defined in terms of
        what they offer for the developer of a new file object needing to implement this method.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled
                database. Use this object to query the database during file writing. Same as given by user in
                ``write()``.
            openFile (:mod:`file`): File object that has been instantiated and "opened" for writing by the ``write()``
                method. Write lines of the file directly to this object. (e.g.: ``openFile.write('foo')``)
            replaceParamFile (:class:`gsshapy.orm.ReplaceParamFile`, optional): Handle the case when replacement
                parameters are used in place of normal variables. If this is not None, then the user expects there
                to be replacement variables in the file. Use the gsshapy.lib.parsetools.valueWritePreprocessor() to
                handle these.
        """

    def _namePreprocessor(self, name):
        """
        Override this method to preprocess the filename during writing.

        Args:
            name (str): The name of the file without the extension. The file extension will be appended after
                preprocessing

        Returns:
            str: Filename that will given to the file being written.
        """

        return name
