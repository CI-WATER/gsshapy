"""
********************************************************************************
* Name: Tutorial Script
* Description: This script summarizes the steps followed in the GsshaPy tutorial
* Author: Nathan Swain
* Created On: July 30, 2014
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

# Create a GsshaPy PostGIS database
from gsshapy.lib import db_tools as dbt
sqlalchemy_url = dbt.sqlalchemy_url = dbt.init_postgresql_db(username='gsshapy', host='localhost', database='gsshapy_tutorial', port='5432', password='pass')

# Create SQLAlchemy session object for db interaction
session = dbt.create_session(sqlalchemy_url)

# Read Files to a Database --------------------------------------------------------------------------------------------#

# Instantiate ProjectFile file object
from gsshapy.orm import ProjectFile
projectFile = ProjectFile()

# Read file into database
readDirectory = '/path_to/tutorial-data'
filename = 'parkcity.prj'
projectFile.read(directory=readDirectory, filename=filename, session=session)

# Inspect supporting objects
projectCards = projectFile.projectCards

for card in projectCards:
    print card

for card in projectCards:
    print card.name, card.value

# Querying the database using the GsshaPy objects ---------------------------------------------------------------------#

# Retrieve all project cards for a given project file
from gsshapy.orm import ProjectCard
cards = session.query(ProjectCard).all()
for card in cards:
    print card

cards = session.query(ProjectCard).filter(ProjectCard.projectFile == projectFile).all()
for card in cards:
    print card

# Equivalently:
cards = projectFile.projectCards
for card in cards:
    print card

# Write File from a Database ------------------------------------------------------------------------------------------#

# Retrieve the ProjectFile object from the database
newProjectFile = session.query(ProjectFile).first()

# Define write parameters and invoke write
writeDirectory = '/path_to/tutorial-data/write'
name = 'mymodel'
newProjectFile.write(session=session, directory=writeDirectory, name=name)

# Read and Write Entire GSSHA Projects --------------------------------------------------------------------------------#

# Create new session
from gsshapy.lib import db_tools as dbt
sqlalchemy_url = dbt.sqlalchemy_url = dbt.init_postgresql_db(username='gsshapy', host='localhost', database='gsshapy_tutorial', port='5432', password='pass')
all_session = dbt.create_session(sqlalchemy_url)

# Instantiate a new ProjectFile object
from gsshapy.orm import ProjectFile
projectFileAll = ProjectFile()

# Invoke the readProject() method
readDirectory = '/path_to/tutorial-data'
filename = 'parkcity.prj'
projectFileAll.readProject(directory=readDirectory, projectFileName=filename, session=all_session)

# Retrieve project file from dataabase and invoke writeProject()
newProjectFileAll = all_session.query(ProjectFile).filter(ProjectFile.id == 2).one()
writeDirectory = '/path_to/tutorial-data/write'
name = 'mymodel'
newProjectFileAll.writeProject(session=all_session, directory=writeDirectory, name=name)

# Read as Spatial Objects and Generate Spatial Visualizations ---------------------------------------------------------#


from gsshapy.lib import db_tools as dbt
sqlalchemy_url = dbt.sqlalchemy_url = dbt.init_postgresql_db(username='gsshapy', host='localhost', database='gsshapy_tutorial', port='5432', password='pass')
all_session = dbt.create_session(sqlalchemy_url)

from gsshapy.orm import ProjectFile
spatialProjectFile = ProjectFile()
readDirectory = '/Users/swainn/testing/test_models/tutorial-data'
filename = 'parkcity.prj'
spatial = True
srid = 26912
raster2pgsql_path = '/Applications/Postgres93.app/Contents/MacOS/bin/raster2pgsql'
spatialProjectFile.readProject(directory=readDirectory, projectFileName=filename, session=all_session, spatial=spatial, spatialReferenceID=srid, raster2pgsqlPath=raster2pgsql_path)
writeDirectory = '/Users/swainn/testing/test_models/tutorial-data/write'
name = 'spatialmodel'
spatialProjectFile.writeProject(session=all_session, directory=writeDirectory, name=name)
