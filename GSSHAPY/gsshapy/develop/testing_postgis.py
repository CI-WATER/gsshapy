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
from mapkit.RasterConverter import RasterConverter

#''' Comment this line to toggle
readDirectory='/Users/swainn/testing/test models/ParkCityBasic'
projectFile='parkcity.prj'

# Write Parameters
writeDirectory='/Users/swainn/testing/test models/ParkCityBasic/write'
newName='parkcitynew'
'''
# Read Parameters
readDirectory='/Users/swainn/testing/ci_water_models/LittleDellNathanTest'
projectFile='LittleDellNathanTest.prj'

# Write Parameters
writeDirectory='/Users/swainn/testing/ci_water_models/LittleDellNathanTest/write'
newName='LittleDell'
#'''

# Directory to append to project file
directory = ''

# Drop all tables except the spatial reference table that PostGIS uses
db_url = 'postgresql://swainn:(|water@localhost/gsshapy_postgis_2'
engine = create_engine(db_url)
meta = MetaData()
meta.reflect(bind=engine)
     
for table in reversed(meta.sorted_tables):
    if table.name != 'spatial_ref_sys':
        table.drop(engine)

# Create new tables
sqlalchemy_url = dbt.init_postgresql_db(username='swainn',
                                        password='(|w@ter',
                                        host='localhost',
                                        database='gsshapy_postgis_2',
                                        initTime=True)

# Initialize the Session
readSession = dbt.create_session(sqlalchemy_url)
writeSession = dbt.create_session(sqlalchemy_url)
   
# Create an empty Project File Object
project = ProjectFile()
   
# Start timer
start = time.time()
       
# Invoke read command on Project File Object
project.readProject(directory=readDirectory, projectFileName=projectFile, session=readSession, spatial=True, spatialReferenceID=26912, raster2pgsqlPath='/Applications/Postgres93.app/Contents/MacOS/bin/raster2pgsql')
# project.readProject()
   
# Report Read Time
print 'READ TIME:', time.time()-start
 
# # Test KML capabilities
#  
# # Get an index map
# idx = writeSession.query(IndexMap).filter(IndexMap.id==2).one()
#  
# # Start timer
# start = time.time()
# 
# # # Generate Hue Color Ramp
# # idx.getAsKmlGrid(session=writeSession,
# #                  path='/Users/swainn/testing/test models/ParkCityBasic/write/post_gis/index.kml',
# #                  colorRamp=RasterConverter.COLOR_RAMP_HUE,
# #                  alpha=1.0)
#  
# mapFile = writeSession.query(RasterMapFile).filter(RasterMapFile.id==2).one()
#  
# # # Generate Terrain Color Ramp
# # mapFile.getAsKmlGrid(session=writeSession,
# #                      path='/Users/swainn/testing/test models/ParkCityBasic/write/post_gis/ele_terrain.kml',
# #                      colorRamp=RasterConverter.COLOR_RAMP_TERRAIN,
# #                      alpha=1.0)
# #  
# # # Generate Aqua Color Ramp
# # mapFile.getAsKmlGrid(session=writeSession,
# #                      path='/Users/swainn/testing/test models/ParkCityBasic/write/post_gis/ele_aqua.kml',
# #                      colorRamp=RasterConverter.COLOR_RAMP_AQUA,
# #                      alpha=1.0)
# #   
# # # Generate Hue Color Ramp
# # mapFile.getAsKmlGrid(session=writeSession,
# #                      path='/Users/swainn/testing/test models/ParkCityBasic/write/post_gis/ele_hue.kml',
# #                      colorRamp=RasterConverter.COLOR_RAMP_HUE,
# #                      alpha=1.0)
# #  
# # # Generate Custom Color Ramp
# # customRamp = {'interpolatedPoints': 10,
# #               'colors': [(255, 0, 0), (0, 255, 0), (0, 0, 255)]}
# # mapFile.getAsKmlGrid(session=writeSession,
# #                      path='/Users/swainn/testing/test models/ParkCityBasic/write/post_gis/ele_custom.kml',
# #                      colorRamp=customRamp,
# #                      alpha=1.0)
# 
# # Generate Color Ramp
# idx.getAsKmlClusters(session=writeSession,
#                      path='/Users/swainn/testing/test models/ParkCityBasic/write/post_gis/index_cluster.kml',
#                      colorRamp=RasterConverter.COLOR_RAMP_HUE,
#                      alpha=1.0)
# 
# mapFile.getAsKmlPng(session=writeSession,
#                     path='/Users/swainn/testing/test models/ParkCityBasic/write/post_gis/ele_png.kml',
#                     colorRamp=RasterConverter.COLOR_RAMP_TERRAIN,
#                     alpha=1.0)
# 
# print idx.getAsGrassAsciiGrid(session=writeSession)
# 
# print mapFile.getAsGrassAsciiGrid(session=writeSession)
# 
# # Report Read Time
# print 'KML CONVERSION TIME:', time.time()-start

# Query Database to Retrieve Project File
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
