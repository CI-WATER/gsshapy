'''
********************************************************************************
* Name: Project File Read Tests
* Author: Nathan Swain
* Created On: July 10, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

from sqlalchemy import create_engine
from gsshapy.orm import ProjectFile, sessionmaker
from gsshapy.lib import db_tools as dbt

# Initialize the Session
# sqlalchemy_url = 'postgresql://swainn:(|w@ter@localhost:5432/gsshapy_lite' # POSTGRESQL
# sqlalchemy_url = 'sqlite://'                                               # SQLITE_MEMEORY
# sqlalchemy_url = 'sqlite:///gsshapy_lite.db'                               # SQLITE_RELATIVE
sqlalchemy_url = 'sqlite:////Users/swainn/testing/db/gsshapy_lite.db'      # SQLITE_ABSOLUTE

readSession = dbt.create_session(sqlalchemy_url)
writeSession = dbt.create_session(sqlalchemy_url)

# # Create an empty Project File Object
# project = ProjectFile(directory='/Users/swainn/testing/LongTerm2w/', filename='longterm2.prj', session=readSession)
#   
# # # Invoke read command on Project File Object
# project.readProject()


# Query Database to Retrieve Project File
project1 = writeSession.query(ProjectFile).filter(ProjectFile.id == 1).one()
                       
# Invoke write command on Project File Query Object
project1.writeProject(session=writeSession, directory='/Users/swainn/testing/write', newName='this_is_a_test')


