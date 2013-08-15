'''
********************************************************************************
* Name: Tutorial Script
* Description: This script summarizes the steps followed in
* the GsshaPy tutorial.
********************************************************************************
'''

# Create a GsshaPy SQLite database
from gsshapy.lib import db_tools as dbt
sqlalchemy_url = dbt.init_sqlite_db('/path/to/tutorial-data/directory/db/gsshapy_parkcity.db')

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

# Querying the database using the GsshaPy objects

# 1. Retrieve all project cards for a given project file
from gsshapy.orm import ProjectCard
cards = session.query(ProjectCard).filter(ProjectCard.projectFileID == 1).all()
for card in cards:
    print card

# Equivilently:
cards = session.query(ProjectCard).filter(ProjectCard.projectFile == projectFile).all()
for card in cards:
    print card

# Access the attributes of the ProjectCard objects with object notation.
for card in cards:
    print card.name, card.value

# Retrieve the ProjectFile object from the database
projectFile1 = session.query(ProjectFile).filter(ProjectFile.id == 1).one()

# Define write parameters
writeDirectory = '/path/to/tutorial-data/directory/write'
name = 'mymodel'

# Invoke write method
projectFile1.write(session=session, directory=writeDirectory, name=name)
