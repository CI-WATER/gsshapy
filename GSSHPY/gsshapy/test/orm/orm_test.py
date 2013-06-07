'''
********************************************************************************
* Name: ORM Tests
* Author: Nathan Swain
* Created On: May 16, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

import unittest
from datetime import date

from gsshapy import init_model, DBSession, metadata
from gsshapy.orm import *
from gsshapy.test.orm.bootstrap import orm_test_data
from sqlalchemy import create_engine

class TestGSSHAORM (unittest.TestCase):
    def setUp(self):
        # Create a database for loading purposes
        testEngine = create_engine('postgresql://swainn:(|w@ter@localhost:5432/gsshapy_alternate')
        #testEngine = create_engine('sqlite:///:memory', echo=True)
        metadata.create_all(testEngine)
        #init_model(testEngine)
        
        # Bootstrap Data for testing
        #orm_test_data(DBSession)
        
        #DBSession.commit()
        
    
    def test_this(self):
        self.x = 5
    

if __name__ == '__main__':
    unittest.main()


