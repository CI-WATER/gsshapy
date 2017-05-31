# -*- coding: utf-8 -*-
#
#  model.py
#  GSSHApy
#
#  Created by Alan D Snow, 2016.
#  BSD 3-Clause

from datetime import timedelta
import logging
import os

from gazar.grid import GDALGrid

from .event import EventMode, LongTermMode
from ..orm import (ProjectFile, WatershedMaskFile, ElevationGridFile,
                         MapTableFile)
from ..lib import db_tools as dbt
from ..util.context import tmp_chdir

log = logging.getLogger(__name__)


class GSSHAModel(object):
    """
    This class manages the generation and modification of
    models for GSSHA.

    Parameters:
         project_directory(str): Directory to write GSSHA project files to.
         project_name(Optional[str]): Name of GSSHA project. Required for new model.
         mask_shapefile(Optional[str]): Path to watershed boundary shapefile. Required for new model.
         grid_cell_size(Optional[str]): Cell size of model (meters). Required for new model.
         elevation_grid_path(Optional[str]): Path to elevation raster used for GSSHA grid. Required for new model.
         simulation_timestep(Optional[float]): Overall model timestep (seconds). Sets TIMESTEP card. Required for new model.
         out_hydrograph_write_frequency(Optional[str]): Frequency of writing to hydrograph (minutes). Sets HYD_FREQ card. Required for new model.
         roughness(Optional[float]): Value of uniform manning's n roughness for grid. Mutually exlusive with land use roughness. Required for new model.
         land_use_grid(Optional[str]): Path to land use grid to use for roughness. Mutually exlusive with roughness. Required for new model.
         land_use_grid_id(Optional[str]): ID of default grid supported in GSSHApy. Mutually exlusive with roughness. Required for new model.
         land_use_to_roughness_table(Optional[str]): Path to land use to roughness table. Use if not using land_use_grid_id. Mutually exlusive with roughness. Required for new model.
         db_session(Optional[database session]): Active database session object. Required for existing model.
         project_manager(Optional[ProjectFile]): Initialized ProjectFile object. Required for existing model.

    Model Generation Example:

    .. code:: python

        from datetime import datetime, timedelta
        from gsshapy.modeling import GSSHAModel

        model = GSSHAModel(project_name="gssha_project",
                           project_directory="/path/to/gssha_project",
                           mask_shapefile="/path/to/watershed_boundary.shp",
                           grid_cell_size=1000,
                           elevation_grid_path="/path/to/elevation.tif",
                           simulation_timestep=10,
                           out_hydrograph_write_frequency=15,
                           land_use_grid='/path/to/land_use.tif',
                           land_use_grid_id='glcf',
                           )
        model.set_event(simulation_start=datetime(2017, 2, 28, 14, 33),
                        simulation_duration=timedelta(seconds=180*60),
                        rain_intensity=2.4,
                        rain_duration=timedelta(seconds=30*60),
                        )
        model.write()

    """
    def __init__(self,
                 project_directory,
                 project_name=None,
                 mask_shapefile=None,
                 grid_cell_size=None,
                 elevation_grid_path=None,
                 simulation_timestep=30,
                 out_hydrograph_write_frequency=10,
                 roughness=None,
                 land_use_grid=None,
                 land_use_grid_id=None,
                 land_use_to_roughness_table=None,
                 load_rasters_to_db=True,
                 db_session=None,
                 project_manager=None,
                ):

        self.project_directory = project_directory
        self.db_session = db_session
        self.project_manager = project_manager
        self.load_rasters_to_db = load_rasters_to_db

        if project_manager is not None and db_session is None:
            raise ValueError("'db_session' is required to edit existing model if 'project_manager' is given.")

        if project_manager is None and db_session is None:

            if project_name is not None and mask_shapefile is None and elevation_grid_path is None:
                self.project_manager, db_sessionmaker = \
                    dbt.get_project_session(project_name, self.project_directory)
                self.db_session = db_sessionmaker()
                self.project_manager.readInput(directory=self.project_directory,
                                               projectFileName="{0}.prj".format(project_name),
                                               session=self.db_session)
            else:
                # generate model
                if None in (project_name, mask_shapefile, elevation_grid_path):
                    raise ValueError("Need to set project_name, mask_shapefile, "
                                     "and elevation_grid_path to generate "
                                     "a new GSSHA model.")

                self.project_manager, db_sessionmaker = \
                    dbt.get_project_session(project_name, self.project_directory, map_type=0)
                self.db_session = db_sessionmaker()
                self.db_session.add(self.project_manager)
                self.db_session.commit()

                # ADD BASIC REQUIRED CARDS
                # see http://www.gsshawiki.com/Project_File:Required_Inputs
                self.project_manager.setCard('TIMESTEP',
                                             str(simulation_timestep))
                self.project_manager.setCard('HYD_FREQ',
                                             str(out_hydrograph_write_frequency))
                # see http://www.gsshawiki.com/Project_File:Output_Files_%E2%80%93_Required
                self.project_manager.setCard('SUMMARY',
                                             '{0}.sum'.format(project_name),
                                             add_quotes=True)
                self.project_manager.setCard('OUTLET_HYDRO',
                                             '{0}.otl'.format(project_name),
                                             add_quotes=True)

                # ADD REQUIRED MODEL GRID INPUT
                if grid_cell_size is None:
                    # caluclate cell size from elevation grid if not given
                    # as input from the user
                    ele_grid = GDALGrid(elevation_grid_path)
                    utm_bounds = ele_grid.bounds(as_utm=True)
                    x_cell_size = (utm_bounds[1] - utm_bounds[0])/ele_grid.x_size
                    y_cell_size = (utm_bounds[3] - utm_bounds[2])/ele_grid.y_size
                    grid_cell_size = min(x_cell_size, y_cell_size)
                    ele_grid = None
                    log.info("Calculated cell size is {grid_cell_size}"
                             .format(grid_cell_size=grid_cell_size))

                self.set_mask_from_shapefile(mask_shapefile, grid_cell_size)
                self.set_elevation(elevation_grid_path, mask_shapefile)
                self.set_roughness(roughness=roughness,
                                   land_use_grid=land_use_grid,
                                   land_use_grid_id=land_use_grid_id,
                                   land_use_to_roughness_table=land_use_to_roughness_table,
                                   )

    def set_mask_from_shapefile(self, shapefile_path, cell_size):
        """
        Adds a mask from a shapefile
        """
        # make sure paths are absolute as the working directory changes
        shapefile_path = os.path.abspath(shapefile_path)
        # ADD MASK
        with tmp_chdir(self.project_directory):
            mask_name = '{0}.msk'.format(self.project_manager.name)
            msk_file = WatershedMaskFile(project_file=self.project_manager,
                                         session=self.db_session)

            msk_file.generateFromWatershedShapefile(shapefile_path,
                                                    cell_size=cell_size,
                                                    out_raster_path=mask_name,
                                                    load_raster_to_db=self.load_rasters_to_db)

    def set_elevation(self, elevation_grid_path, mask_shapefile):
        """
        Adds elevation file to project
        """
        # ADD ELEVATION FILE
        ele_file = ElevationGridFile(project_file=self.project_manager,
                                     session=self.db_session)
        ele_file.generateFromRaster(elevation_grid_path,
                                    mask_shapefile,
                                    load_raster_to_db=self.load_rasters_to_db)

    def set_outlet(self, latitude, longitude, outslope):
        """
        Adds outlet point to project
        """
        self.project_manager.setOutlet(latitude=latitude, longitude=longitude,
                                       outslope=outslope)

    def set_roughness(self,
                      roughness=None,
                      land_use_grid=None,
                      land_use_grid_id=None,
                      land_use_to_roughness_table=None):
        """
        ADD ROUGHNESS FROM LAND COVER
        See: http://www.gsshawiki.com/Project_File:Overland_Flow_%E2%80%93_Required
        """
        if roughness is not None:
            self.project_manager.setCard('MANNING_N', str(roughness))
        elif land_use_grid is not None and (land_use_grid_id is not None \
                or land_use_to_roughness_table is not None):
            # make sure paths are absolute as the working directory changes
            land_use_grid = os.path.abspath(land_use_grid)
            if land_use_to_roughness_table is not None:
                land_use_to_roughness_table = os.path.abspath(land_use_to_roughness_table)

            mapTableFile = MapTableFile(project_file=self.project_manager)
            mapTableFile.addRoughnessMapFromLandUse("roughness",
                                                    self.db_session,
                                                    land_use_grid,
                                                    land_use_to_roughness_table=land_use_to_roughness_table,
                                                    land_use_grid_id=land_use_grid_id)
        else:
            raise ValueError("Need to either set 'roughness', or need "
                             "to set values from land use grid ...")

    def set_event(self,
                  simulation_start=None,
                  simulation_duration=None,
                  simulation_end=None,
                  rain_intensity=2,
                  rain_duration=timedelta(seconds=30*60),
                  event_type='EVENT',
                 ):
        """
        Initializes event for GSSHA model
        """
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
        """
        Write project to directory
        """
        # write data
        self.project_manager.writeInput(session=self.db_session,
                                        directory=self.project_directory,
                                        name=self.project_manager.name)
