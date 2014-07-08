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
from gsshapy.orm import RasterMapFile, MapTableFile, PrecipFile, ProjectFile
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
read_directory = '/Users/swainn/testing/timeseries_maps/ParkCityBasic'
write_directory = '/Users/swainn/testing/timeseries_maps/ParkCityInput'
new_name = 'parkcity'
spatial = True
srid = 26912
raster2pgsql_path = '/Applications/Postgres93.app/Contents/MacOS/bin/raster2pgsql'
read_session = dbt.create_session(sqlalchemy_url)
write_session = dbt.create_session(sqlalchemy_url)
   

# Read Project --------------------------------------------------------------------------------------------------------#

project_file = ProjectFile()
project_file.readProject(read_directory, 'parkcity.prj', read_session, spatial=spatial, spatialReferenceID=srid, raster2pgsqlPath=raster2pgsql_path)

project_file = write_session.query(ProjectFile).first()
project_file.writeInput(write_session, write_directory, 'parkcity')