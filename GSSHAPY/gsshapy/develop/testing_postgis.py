'''
********************************************************************************
* Name: Testing Script
* Author: Nathan Swain
* Created On: July 10, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''
import time
from gsshapy.orm import ProjectFile, IndexMap, RasterMapFile
from gsshapy.lib import db_tools as dbt
from sqlalchemy import MetaData, create_engine

# Read Parameters
readDirectory='/Users/swainn/testing/test models/ParkCityBasic'
projectFile='parkcity.prj'

# Write Parameters
writeDirectory='/Users/swainn/testing/test models/ParkCityBasic/write'
newName='parkcity'

# Directory to append to project file
directory = '/home/swainn/post_read_LittleDellNathanTest'

# Drop all tables except the spatial reference table that PostGIS uses
db_url = 'postgresql://swainn:(|water@localhost/gsshapy_postgis'
# engine = create_engine(db_url)
# meta = MetaData()
# meta.reflect(bind=engine)

# for table in reversed(meta.sorted_tables):
#     if table.name != 'spatial_ref_sys':
#         table.drop(engine)

# Create new tables
sqlalchemy_url = dbt.init_postgresql_db(username='swainn',
                                        password='(|w@ter',
                                        host='localhost',
                                        database='gsshapy',
                                        initTime=True)

# Initialize the Session
readSession = dbt.create_session(sqlalchemy_url)
writeSession = dbt.create_session(sqlalchemy_url)
   
# # Create an empty Project File Object
# project = ProjectFile(directory=readDirectory, filename=projectFile, session=readSession)
#     
# Start timer
start = time.time()
#     
# # Invoke read command on Project File Object
# project.readProject(spatial=True, spatialReferenceID=26912, raster2pgsqlPath='/Applications/Postgres.app/Contents/MacOS/bin/raster2pgsql')
# # project.readProject()
# 
# # Report Read Time
# print 'READ TIME:', time.time()-start

## Test KML capabilities

# Get an index map
idx = writeSession.query(IndexMap).filter(IndexMap.id==2).one()
idx.getAsKmlGrid(session=writeSession,
                 path='/Users/swainn/projects/post_gis/index.kml',
                 ramp='rainbow',
                 alpha=1.0)

mapFile = writeSession.query(RasterMapFile).filter(RasterMapFile.id==2).one()
mapFile.getAsKmlGrid(session=writeSession,
                     path='/Users/swainn/projects/post_gis/ele.kml',
                     ramp='terrain',
                     alpha=1.0)

# Report Read Time
print 'KML CONVERSION TIME:', time.time()-start

# # Query Database to Retrieve Project File
# project1 = writeSession.query(ProjectFile).filter(ProjectFile.id == 1).one()
#      
# # Reset Timer
# start = time.time()
#                             
# # Invoke write command on Project File Query Object
# project1.writeProject(session=writeSession, directory=writeDirectory, name=newName)
#      
# # # Test append directory method
# # project1.appendDirectory(directory)
#      
# # Report Write Time
# print 'WRITE TIME:', time.time() - start
