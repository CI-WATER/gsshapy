'''
********************************************************************************
* Name: Tutorial Script
* Description: This script summarizes the steps followed in
* the GsshaPy tutorial.
********************************************************************************
'''

# Create a GsshaPy SQLite database
from gsshapy.lib import db_tools as dbt
sqlalchemy_url = dbt.init_sqlite_db('/path/to/tutorial-data/db/gsshapy_parkcity.db')

# Create SQLAlchemy session object for db interaction
session = dbt.create_session(sqlalchemy_url)

# Set read parameters
readDirectory = '/path/to/tutorial-data/directory'
fileame = 'parkcity.prj'

# Instantiate ProjectFile file object
from gsshapy.orm import ProjectFile
projectFile = ProjectFile(directory=readDirectory, filename=filename, session=session)

# Read file into database
projectFile.read()


