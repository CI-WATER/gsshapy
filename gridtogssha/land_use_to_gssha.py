from gsshapy.orm import ProjectFile
from gsshapy.lib import db_tools as dbt

from os import path, chdir

gssha_directory = '/home/rdchlads/scripts/gsshapy/tests/grid_standard/gssha_project'
land_use_grid = path.join('/home/rdchlads/scripts/gsshapy/gridtogssha', 'LC_5min_global_2012.tif')
land_use_to_roughness_table = path.join('/home/rdchlads/scripts/gsshapy/gridtogssha/land_cover', 'land_cover_glcf_modis.txt')

chdir(gssha_directory)

# Create Test DB
sqlalchemy_url, sql_engine = dbt.init_sqlite_memory()

# Create DB Sessions
db_session = dbt.create_session(sqlalchemy_url, sql_engine)

# Instantiate GSSHAPY object for reading to database
project_manager = ProjectFile()

# Call read method
project_manager.readInput(directory=gssha_directory,
                          projectFileName='grid_standard.prj',
                          session=db_session)

project_manager.mapTableFile.addRoughnessMapFromLandUse("roughness",
                                                        db_session,
                                                        land_use_grid,
                                                        #land_use_to_roughness_table,
                                                        land_use_grid_id='glcf',
                                                        )
# WRITE OUT UPDATED GSSHA PROJECT FILE
project_manager.writeInput(session=db_session,
                           directory=gssha_directory,
                           name='grid_standard')
