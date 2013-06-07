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
from gsshapy.orm import Scenario

from gsshapy.file_io.project_file import ProjectFile

from sqlalchemy.orm import scoped_session, sessionmaker

# Define the session
engine = create_engine('postgresql://swainn:(|w@ter@localhost:5432/gsshapy_testing')
maker = sessionmaker(bind=engine)
DBSession = maker()

'''
Project File
'''

# Get scenario object from the database
scn = DBSession.query(Scenario).filter(Scenario.id == 2).one()

prjFile = ProjectFile(DBSession, scn)
prjFile.write('/Users/swainn/testing/write')
