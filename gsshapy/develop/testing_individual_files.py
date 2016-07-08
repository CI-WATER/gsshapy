'''
********************************************************************************
* Name: Testing the capabilities to work with individual files objects
* Author: Nathan Swain
* Created On: July 8, 2014
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

import time
from gsshapy.orm import RasterMapFile, MapTableFile, PrecipFile
from gsshapy.lib import db_tools as dbt
from sqlalchemy import MetaData, create_engine

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
read_directory = '/Users/swainn/testing/test models/standard'
write_directory = '/Users/swainn/testing/test models/standard/write'
new_name = 'new_standard'
spatial = True
srid = 26912
raster2pgsql_path = '/Applications/Postgres93.app/Contents/MacOS/bin/raster2pgsql'
   

# Test Reading Individual Files ---------------------------------------------------------------------------------------#

##############################
##### Read in a Mask Map #####
##############################

# 1. Define Variables
mask_in_filename = 'standard.msk'

# 2. Create Session
mask_in_session = dbt.create_session(sqlalchemy_url)

# 3. Instantiate File Object
mask_map_in_file = RasterMapFile()

# 4. Call Read Method
mask_map_in_file.read(read_directory, mask_in_filename, mask_in_session, spatial, srid, raster2pgsql_path)


########################################
##### Read in a Mapping Table File #####
########################################

# 1. Define Variables
map_table_in_filename = 'standard.cmt'

# 2. Create Session
map_table_in_session = dbt.create_session(sqlalchemy_url)

# 3. Instantiate File Object
map_table_in_file = MapTableFile()

# 4. Call Read Method
map_table_in_file.read(read_directory, map_table_in_filename, map_table_in_session, spatial, srid, raster2pgsql_path)


########################################
##### Read in a Precipitation File #####
########################################

# 1. Define Variables
precip_in_filename = 'standard.gag'

# 2. Create Session
precip_in_session = dbt.create_session(sqlalchemy_url)

# 3. Instantiate File Object
precip_in_file = PrecipFile()

# 4. Call Read Method
precip_in_file.read(read_directory, precip_in_filename, precip_in_session, spatial, srid, raster2pgsql_path)

# Test Writing of Individual Files ------------------------------------------------------------------------------------#

##########################
##### Write Mask Map #####
##########################

# 1. Define variables
mask_out_name = 'new_standard.msk'

# 2. Create Session
mask_out_session = dbt.create_session(sqlalchemy_url)

# 3. Query for File (First One)
mask_map_out_file = mask_out_session.query(RasterMapFile).first()

# 4. Write to File
mask_map_out_file.write(mask_out_session, write_directory, mask_out_name)

####################################
##### Write Mapping Table File #####
####################################

# 1. Define the variables
map_table_out_name = 'new_standard.cmt'

# 2. Create Session
map_table_out_session = dbt.create_session(sqlalchemy_url)

# 3. Query for the File (First One)
map_table_out_file = map_table_out_session.query(MapTableFile).first()

# 4. Write to File
map_table_out_file.write(map_table_out_session, write_directory, map_table_out_name)


####################################
##### Write Precipitation File #####
####################################

# 1. Define the variables
precip_out_name = 'new_standard'

# 2. Create Session
precip_out_session = dbt.create_session(sqlalchemy_url)

# 3. Query for the File (First One)
precip_out_file = precip_out_session.query(PrecipFile).first()

# 4. Write to File
precip_out_file.write(precip_out_session, write_directory, precip_out_name)