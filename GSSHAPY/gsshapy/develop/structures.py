"""
********************************************************************************
* Name: Read a file in and write it back out
* Author: Nathan Swain
* Created On: July 8, 2014
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

import os

import time
from gsshapy.orm import WMSDatasetFile, ProjectFile, ChannelInputFile, LinkNodeDatasetFile, IndexMap, RasterMapFile, WMSDatasetRaster
from gsshapy.lib import db_tools as dbt
from sqlalchemy import MetaData, create_engine
from mapkit.RasterConverter import RasterConverter
from mapkit.ColorRampGenerator import ColorRampGenerator, ColorRampEnum

# DATABASE SETUP ------------------------------------------------------------------------------------------------------#
'''
# Drop all tables except the spatial reference table that PostGIS uses
db_url = 'postgresql://swainn:(|water@localhost/gsshapy_structures'
engine = create_engine(db_url)
meta = MetaData()
meta.reflect(bind=engine)

for table in reversed(meta.sorted_tables):
    if table.name != 'spatial_ref_sys':
        table.drop(engine)
#'''

# Create new tables
sqlalchemy_url = dbt.init_postgresql_db(username='swainn',
                                        password='(|w@ter',
                                        host='localhost',
                                        database='gsshapy_structures')

# GLOBAL PARAMETERS ---------------------------------------------------------------------------------------------------#
read_directory = '/Users/swainn/testing/test_models/structures'
write_directory = '/Users/swainn/testing/test_models/structures/write'
project_file_name = 'EMBANKSTRUCT.prj'

out_file_name = 'out'
new_name = 'out'
spatial = True
srid = 26912
raster2pgsql_path = '/Applications/Postgres93.app/Contents/MacOS/bin/raster2pgsql'
read_session = dbt.create_session(sqlalchemy_url)
write_session = dbt.create_session(sqlalchemy_url)
   

# READ PROJECT --------------------------------------------------------------------------------------------------------#
'''
project_file = ProjectFile()

START = time.time()
project_file.readProject(read_directory, project_file_name, read_session, spatial=spatial)
print 'READ: ', time.time() - START
#'''

# WRITE PROJECT -------------------------------------------------------------------------------------------------------#
'''
project_file = write_session.query(ProjectFile).first()
START = time.time()
project_file.writeProject(write_session, write_directory, out_file_name)
print 'WRITE: ', time.time() - START
#'''

# KML TESTING ---------------------------------------------------------------------------------------------------------#
project_file = write_session.query(ProjectFile).first()
wms_dataset = write_session.query(WMSDatasetFile).first()

START = time.time()

# WMS DATASETS --------------------------------------------------------------------------------------------------------#
'''
out_path = os.path.join(write_directory, 'depth.kml')
wms_dataset.getAsKmlGridAnimation(write_session, project_file, path=out_path, colorRamp=ColorRampEnum.COLOR_RAMP_AQUA)
'''

'''
out_path = os.path.join(write_directory, 'depth.kmz')
wms_dataset.getAsKmlPngAnimation(write_session, project_file, path=out_path, colorRamp=ColorRampEnum.COLOR_RAMP_AQUA, alpha=0.8, cellSize=10)
#'''

# SINGLE WMS DATASET RASTER -------------------------------------------------------------------------------------------#
'''
out_path = os.path.join(write_directory, 'one_depth.kml')
wms_raster = write_session.query(WMSDatasetRaster).get(144)
wms_raster.getAsKmlGrid(write_session, path=out_path)
#'''

# INDEX AND RASTER MAPS -----------------------------------------------------------------------------------------------#
'''
out_path = os.path.join(write_directory, 'index.kmz')
index_map = write_session.query(IndexMap).first()
index_map.getAsKmlPng(write_session, path=out_path)
'''

'''
out_path = os.path.join(write_directory, 'elevation.kml')
elevation = write_session.query(RasterMapFile).filter(RasterMapFile.projectFile == project_file).filter(RasterMapFile.fileExtension == 'ele').one()
elevation.getAsKmlGrid(write_session, path=out_path, colorRamp=ColorRampEnum.COLOR_RAMP_TERRAIN)
#'''

# STREAM NETWORK ------------------------------------------------------------------------------------------------------#
'''
channel_input_file = write_session.query(ChannelInputFile).first()
stream_links = channel_input_file.streamLinks

out_path = os.path.join(write_directory, 'channel.kml')
styles = {'lineColor': (0, 255, 128, 255)}

channel_input_file.getStreamNetworkAsKml(write_session, out_path)
#'''

# MODEL REPRESENTATION ------------------------------------------------------------------------------------------------#
'''
out_path = os.path.join(write_directory, 'model.kml')
styles = {'maskFillColor': (255, 128, 0, 255),
          'maskLineWidth': 0.0}
# project_file.getModelSummaryAsKml(write_session, out_path, withStreamNetwork=True, styles=styles)
# print project_file.getModelSummaryAsWkt(write_session, withStreamNetwork=True, withNodes=True)
#print project_file.getModelSummaryAsGeoJson(write_session, withStreamNetwork=True)
#'''

# LINK NODE DATASET ANIMATION -----------------------------------------------------------------------------------------#
#'''
channel_input_file = write_session.query(ChannelInputFile).first()
link_node_dataset_file = write_session.query(LinkNodeDatasetFile).first()


# link_node_dataset_file.linkToChannelInputFile(write_session, channel_input_file)
out_path = os.path.join(write_directory, 'channel_depth.kml')
styles = {'radius': 10}
link_node_dataset_file.getAsKmlAnimation(write_session, channel_input_file, path=out_path, styles=styles)
#'''

print 'KML OUT: ', time.time() - START