'''
********************************************************************************
* Name: Read a file in and write it back out
* Author: Nathan Swain
* Created On: July 8, 2014
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

import time
from gsshapy.orm import WMSDatasetFile, ProjectFile
from gsshapy.lib import db_tools as dbt
from sqlalchemy import MetaData, create_engine
from mapkit.RasterConverter import RasterConverter

# Database Setup ------------------------------------------------------------------------------------------------------#

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
                                        database='gsshapy_postgis_2')

# Global Parameters ---------------------------------------------------------------------------------------------------#
read_directory = '/Users/swainn/testing/timeseries_maps/ParkCity_MapType1/results'
write_directory = '/Users/swainn/testing/timeseries_maps/ParkCity_MapType1/results/write'
new_name = 'out'
spatial = True
srid = 26912
raster2pgsql_path = '/Applications/Postgres93.app/Contents/MacOS/bin/raster2pgsql'
read_session = dbt.create_session(sqlalchemy_url)
write_session = dbt.create_session(sqlalchemy_url)
   

# Read Project --------------------------------------------------------------------------------------------------------#

project_file = ProjectFile()

START = time.time()
project_file.readProject(read_directory, 'parkcity.prj', read_session, spatial=spatial, spatialReferenceID=srid, raster2pgsqlPath=raster2pgsql_path)
print 'READ: ', time.time() - START

# project_file = write_session.query(ProjectFile).first()
# START = time.time()
# project_file.writeProject(write_session, write_directory, 'parkcity')
# print 'WRITE: ', time.time() - START

# Test Time Series KML ------------------------------------------------------------------------------------------------#
project_file = write_session.query(ProjectFile).first()
wms_dataset = write_session.query(WMSDatasetFile).first()
START = time.time()
kml_animation_string = wms_dataset.getAsTimeStampedKml(write_session, project_file, colorRamp=RasterConverter.COLOR_RAMP_AQUA)
print 'KML OUT: ', time.time() - START

with open('/Users/swainn/testing/timeseries_maps/ParkCity_MapType1/results/write/out.kml', 'w') as f:
    f.write(kml_animation_string)