# -*- coding: utf-8 -*-
#
#  model.py
#  GSSHApy
#
#  Created by Alan D Snow, 2016.
#  BSD 3-Clause

from datetime import timedelta
from gsshapy.orm import (ProjectFile, WatershedMaskFile, ElevationGridFile,
                         MapTableFile)
from gsshapy.lib import db_tools as dbt

from .event import EventMode, LongTermMode

class GSSHAModel(object):
    '''
    This class manages the generation and modification of
    models for GSSHA
    '''
    def __init__(self,
                 project_name,
                 project_directory,
                 simulation_timestep=30,
                 out_hydrograph_write_frequency=10,
                 roughness=0.013,
                ):

        self.project_directory = project_directory

        # Create Test DB
        sqlalchemy_url, sql_engine = dbt.init_sqlite_memory()

        # Create DB Sessions
        self.db_session = dbt.create_session(sqlalchemy_url, sql_engine)

        # Instantiate GSSHAPY object for reading to database
        self.project_manager = ProjectFile(name=project_name, map_type=1)
        self.db_session.add(self.project_manager)
        self.db_session.commit()

        # ADD BASIC REQUIRED CARDS
        # see http://www.gsshawiki.com/Project_File:Required_Inputs
        self.project_manager.setCard('TIMESTEP', str(simulation_timestep))
        self.project_manager.setCard('HYD_FREQ', str(out_hydrograph_write_frequency))
        # see http://www.gsshawiki.com/Project_File:Output_Files_%E2%80%93_Required
        self.project_manager.setCard('SUMMARY', '{0}.sum'.format(project_name), add_quotes=True)
        self.project_manager.setCard('OUTLET_HYDRO', '{0}.otl'.format(project_name), add_quotes=True)
        # see http://www.gsshawiki.com/Project_File:Overland_Flow_%E2%80%93_Required
        self.project_manager.setCard('MANNING_N', str(roughness))

    def set_mask_from_shapefile(self, shapefile_path, cell_size=None, num_cells=None):
        '''
        Adds a mask from a shapefile
        '''
        # ADD MASK
        mask_name = '{0}.msk'.format(self.project_manager.name)
        msk_file = WatershedMaskFile(project_file=self.project_manager,
                                     session=self.db_session)

        msk_file.generateFromWatershedShapefile(shapefile_path,
                                                mask_name,
                                                x_cell_size=cell_size,
                                                y_cell_size=cell_size,
                                                x_num_cells=num_cells,
                                                y_num_cells=num_cells,
                                                )

    def set_elevation(self, elevation_grid_path):
        '''
        Adds elevation file to project
        '''
        # ADD ELEVATION FILE
        ele_file = ElevationGridFile(project_file=self.project_manager,
                                     session=self.db_session)
        ele_file.generateFromRaster(elevation_grid_path)

    def set_outlet(self, latitude, longitude, outslope):
        '''
        Adds outlet point to project
        '''
        self.project_manager.setOutlet(latitude=latitude, longitude=longitude,
                                       outslope=outslope)

    def set_roughtness_idx(self, land_use_grid, land_use_grid_id=None,
                           land_use_to_roughness_table=None):
        '''
        ADD ROUGHNESS FROM LAND COVER
        See: http://www.gsshawiki.com/Project_File:Overland_Flow_%E2%80%93_Required
        '''
        mapTableFile = MapTableFile(project_file=self.project_manager)
        mapTableFile.addRoughnessMapFromLandUse("roughness",
                                                self.db_session,
                                                land_use_grid,
                                                land_use_to_roughness_table=land_use_to_roughness_table,
                                                land_use_grid_id=land_use_grid_id,
                                                )

    def set_event(self,
                  simulation_start=None,
                  simulation_duration=None,
                  simulation_end=None,
                  rain_intensity=2,
                  rain_duration=timedelta(seconds=30*60),
                  event_type='EVENT',
                 ):

        # ADD TEMPORTAL EVENT INFORMAITON
        if event_type == 'LONG_TERM':
            self.event = LongTermMode(self.project_manager,
                                      self.db_session,
                                      self.project_directory,
                                      simulation_start=simulation_start,
                                      simulation_end=simulation_end,
                                      simulation_duration=simulation_duration,
                                     )
        else: # 'EVENT'
            self.event = EventMode(self.project_manager,
                                   self.db_session,
                                   self.project_directory,
                                   simulation_start=simulation_start,
                                   simulation_duration=simulation_duration,
                                   )
            self.event.add_uniform_precip_event(intensity=rain_intensity,
                                                duration=rain_duration)

    def write(self):
        '''
        Write project to directory
        '''
        # write data
        self.project_manager.writeInput(session=self.db_session,
                                        directory=self.project_directory,
                                        name=self.project_manager.name)
