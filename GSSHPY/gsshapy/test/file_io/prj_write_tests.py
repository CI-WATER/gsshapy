'''
********************************************************************************
* Name: Project File Write Tests
* Author: Nathan Swain
* Created On: June 5, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

from sqlalchemy import create_engine
from gsshapy.orm import *

# Define the session
engine = create_engine('postgresql://swainn:(|w@ter@localhost:5432/gsshapy_alternate')
maker = sessionmaker(bind=engine)
DBSession = maker()

'''
Project File
'''

# Get scenario object from the database
projectFile = DBSession.query(ProjectFile).filter(ProjectFile.id == 1).one()

projectFile.write(DBSession, '/Users/swainn/testing/write/')



