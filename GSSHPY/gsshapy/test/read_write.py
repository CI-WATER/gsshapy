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
import time

# Initialize the Session
# sqlalchemy_url = 'postgresql://swainn:(|w@ter@localhost:5432/gsshapy_lite' # POSTGRESQL
# sqlalchemy_url = 'sqlite://'                                               # SQLITE_MEMEORY
# sqlalchemy_url = 'sqlite:///gsshapy_lite.db'                               # SQLITE_RELATIVE
sqlalchemy_url = 'sqlite:////Users/swainn/testing/db/gsshapy_lite.db'      # SQLITE_ABSOLUTE

engine = create_engine(sqlalchemy_url)
maker = sessionmaker(bind=engine)
DBSession = maker()
DBSession2 = maker()

# Create an empty Project File Object
project = ProjectFile(path='/Users/swainn/testing/LongTerm2/LongTerm2.prj', session=DBSession)



# # Invoke read command on Project File Object
start = time.time()
project.readAll()
            
# # Commit outside for now
# DBSession.commit()
print 'SUCCESS: Project Read to Database', 'TIME:', time.time()-start


# # Query Database to Retrieve Project File
# start = time.time()
# project1 = DBSession2.query(ProjectFile).filter(ProjectFile.id == 1).one()
#                    
# # Invoke write command on Project File Query Object
# project1.writeAll(session=DBSession2, directory='/Users/swainn/testing/LongTerm2w/', newName='longterm2')
# print 'SUCCESS: Project Written to File', 'TIME:', time.time()-start

