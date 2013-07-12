'''
********************************************************************************
* Name: ORM Tests
* Author: Nathan Swain
* Created On: June 7, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

from sqlalchemy import create_engine
from gsshapy.orm import metadata
from gsshapy import DBSession
from gsshapy.test.orm.bootstrap import orm_test_data

# Define the session
engine = create_engine('postgresql://swainn:(|w@ter@localhost:5432/gsshapy_lite')
metadata.create_all(engine)

DBSession.configure(bind=engine)

#orm_test_data(DBSession)

DBSession.commit()
