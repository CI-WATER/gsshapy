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

from gsshapy import *
from gsshapy.orm import *
#from gsshapy.test.orm.bootstrap import *
from sqlalchemy import create_engine

class TestGSSHAORM (unittest.TestCase):
    def setUp(self):
        # Create a database for loading purposes
        testEngine = create_engine('postgresql://swainn:(|w@ter@localhost:5432/gsshapy2')
        #testEngine = create_engine('sqlite:///:memory', echo=True)
        metadata.create_all(testEngine)
        init_model(testEngine)
        
        # Bootstrap Data for testing
        # self.data = orm_test_data()
        
        # DB Commit
        #DBSession.add(self.data.mdl)
        #DBSession.commit()
    
    def test_this(self):
        self.x = 5
    

if __name__ == '__main__':
    unittest.main()


