'''
********************************************************************************
* Name: Gssha File Object Base
* Author: Nathan Swain
* Created On: August 2, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

class GsshaPyFileObjectBase:
    '''
    classdocs
    '''
    
    # File Properties
    PATH = None
    PROJECT_NAME = None
    DIRECTORY = None
    SESSION = None
    EXTENSION = None
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        self.FILENAME = filename                             # e.g.: example.ext
        self.DIRECTORY = directory                           # e.g.: /path/to/my/example
        self.SESSION = session                               # SQL Alchemy Session object
        self.PATH = '%s%s' % (self.DIRECTORY, self.FILENAME) # e.g.: /path/to/my/example/example.ext
        self.EXTENSION = filename.split('.')[1]              # e.g.: ext
        
    def read(self):
        '''
        Front Facing Read from File Method
        '''
        # Add self to session
        self.SESSION.add(self)
        
        # Read
        self._readWithoutCommit()
        
        # Commit
        self.SESSION.commit()
