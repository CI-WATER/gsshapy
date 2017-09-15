"""
********************************************************************************
* Name: Project Generation Tests
* Author: Alan D. Snow
* Created On: February 28, 2017
* License: BSD 3-Clause
********************************************************************************
"""
from datetime import datetime, timedelta
from glob import glob
from os import path
import unittest
from shutil import copy

import pytest

from .template import TestGridTemplate


from gsshapy.modeling import GSSHAModel
from gsshapy.orm import (ProjectFile, WatershedMaskFile, ElevationGridFile,
                         MapTableFile)
from gsshapy.lib import db_tools as dbt


class TestProjectGenerateBase(TestGridTemplate):
    def _compare_basic_model(self, project_name):
        """
        Compare output from basic GSSHA model
        """
        # compare msk
        mask_name = '{0}.msk'.format(project_name)
        new_mask_grid = path.join(self.gssha_project_directory, mask_name)
        compare_msk_file = path.join(self.compare_path, mask_name)
        self._compare_files(compare_msk_file, new_mask_grid, raster=True)
        # compare ele
        ele_grid_name = '{0}.ele'.format(project_name)
        new_ele_grid = path.join(self.gssha_project_directory, ele_grid_name)
        compare_ele_file = path.join(self.compare_path, ele_grid_name)
        self._compare_files(compare_ele_file, new_ele_grid, raster=True)
        # compare project files
        prj_file_name = '{0}.prj'.format(project_name)
        generated_prj_file = path.join(self.gssha_project_directory,
                                       prj_file_name)
        compare_prj_file = path.join(self.compare_path, prj_file_name)
        self._compare_files(generated_prj_file, compare_prj_file)
        # check to see if projection file generated
        proj_file_name = '{0}_prj.pro'.format(project_name)
        generated_proj_file = path.join(self.gssha_project_directory,
                                        proj_file_name)
        compare_proj_file = path.join(self.compare_path, proj_file_name)
        self._compare_files(generated_proj_file, compare_proj_file)

    def _compare_basic_model_idx_maps(self, project_name):
        """
        Compare output from basic GSSHA model with index maps
        """
        # compare main project files
        self._compare_basic_model(project_name)
        # compare cmt
        cmt_file_name = '{0}.cmt'.format(project_name)
        new_cmt_file = path.join(self.gssha_project_directory, cmt_file_name)
        compare_cmt_file = path.join(self.compare_path, cmt_file_name)
        self._compare_files(new_cmt_file, compare_cmt_file)
        # compare idx
        new_idx_file = path.join(self.gssha_project_directory, 'roughness.idx')
        original_idx_file = path.join(self.compare_path, 'roughness.idx')
        self._compare_files(original_idx_file, new_idx_file, raster=True)


class TestProjectGenerate(TestProjectGenerateBase):
    def setUp(self):
        self.compare_path = path.join(self.readDirectory,
                                      'philippines',
                                      'compare_data')

        self.gssha_project_directory = self.writeDirectory

        self.shapefile_path = path.join(self.writeDirectory,
                                        'philippines_5070115700.shp')

        self.elevation_path = path.join(self.writeDirectory,
                                        'gmted_elevation.tif')
        self.land_use_grid = path.join(self.writeDirectory, 'LC_hd_global_2012.tif')

        # copy shapefile
        shapefile_basename = path.join(self.readDirectory,
                                       'philippines',
                                       'philippines_5070115700.*')

        for shapefile_part in glob(shapefile_basename):
            try:
                copy(shapefile_part,
                     path.join(self.writeDirectory, path.basename(shapefile_part)))
            except OSError:
                pass

        # copy elevation grid
        try:
            copy(path.join(self.readDirectory, 'philippines',
                           'gmted_elevation.tif'),
                 self.elevation_path)
        except OSError:
            pass

        # copy land cover data
        try:
            copy(path.join(self.readDirectory, 'land_cover', 'LC_hd_global_2012.tif'),
                 self.land_use_grid)
        except OSError:
            pass

    def test_generate_basic_project(self):
        """
        Tests generating a basic GSSHA project
        """

        project_name = "grid_standard_basic"
        # Instantiate GSSHAPY object for reading to database
        # Create Test DB
        project_manager, db_sessionmaker = \
            dbt.get_project_session(project_name,
                                    self.gssha_project_directory,
                                    map_type=1)
        # Create DB Sessions
        db_session = db_sessionmaker()
        db_session.add(project_manager)
        db_session.commit()

        # ADD MASK
        mask_name = '{0}.msk'.format(project_name)
        msk_file = WatershedMaskFile(project_file=project_manager,
                                     session=db_session)

        msk_file.generateFromWatershedShapefile(self.shapefile_path,
                                                cell_size=1000,
                                                out_raster_path=mask_name,
                                                )

        # ADD ELEVATION FILE
        ele_file = ElevationGridFile(project_file=project_manager,
                                     session=db_session)
        ele_file.generateFromRaster(self.elevation_path,
                                    self.shapefile_path)

        # ADD OUTLET POINT
        project_manager.setOutlet(col=0, row=6,
                                  outslope=0.002)

        # ADD ADDITIONAL REQUIRED FILES
        # see http://www.gsshawiki.com/Project_File:Required_Inputs
        project_manager.setCard('TOT_TIME', '180')
        project_manager.setCard('TIMESTEP', '10')
        project_manager.setCard('HYD_FREQ', '15')
        # see http://www.gsshawiki.com/Project_File:Output_Files_%E2%80%93_Required
        project_manager.setCard('SUMMARY', '{0}.sum'.format(project_name), add_quotes=True)
        project_manager.setCard('OUTLET_HYDRO', '{0}.otl'.format(project_name), add_quotes=True)
        # see http://www.gsshawiki.com/Project_File:Overland_Flow_%E2%80%93_Required
        project_manager.setCard('MANNING_N', '0.013')
        # see http://www.gsshawiki.com/Project_File:Rainfall_Input_and_Options_%E2%80%93_Required
        project_manager.setCard('PRECIP_UNIF', '')
        project_manager.setCard('RAIN_INTENSITY', '2.4')
        project_manager.setCard('RAIN_DURATION', '30')
        project_manager.setCard('START_DATE', '2017 02 28')
        project_manager.setCard('START_TIME', '14 33')

        # write data
        project_manager.writeInput(session=db_session,
                                   directory=self.gssha_project_directory,
                                   name=project_name)

        db_session.close()
        # compare
        self._compare_basic_model(project_name)

    def test_generate_basic_project_land_cover(self):
        """
        Tests generating a basic GSSHA project with land cover
        """

        project_name = "grid_standard_basic_land_cover"
        # Instantiate GSSHAPY object for reading to database
        project_manager, db_sessionmaker = \
            dbt.get_project_session(project_name,
                                    self.gssha_project_directory,
                                    map_type=1)
        # Create DB Sessions
        db_session = db_sessionmaker()
        db_session.add(project_manager)
        db_session.commit()

        # ADD MASK
        mask_name = '{0}.msk'.format(project_name)
        msk_file = WatershedMaskFile(project_file=project_manager,
                                     session=db_session)

        msk_file.generateFromWatershedShapefile(self.shapefile_path,
                                                cell_size=1000,
                                                out_raster_path=mask_name,
                                                )

        # ADD ELEVATION FILE
        ele_file = ElevationGridFile(project_file=project_manager,
                                     session=db_session)
        ele_file.generateFromRaster(self.elevation_path,
                                    self.shapefile_path)

        # ADD ROUGHNESS FROM LAND COVER
        # see http://www.gsshawiki.com/Project_File:Overland_Flow_%E2%80%93_Required
        mapTableFile = MapTableFile(project_file=project_manager)
        mapTableFile.addRoughnessMapFromLandUse("roughness",
                                                db_session,
                                                self.land_use_grid,
                                                land_use_grid_id='glcf',
                                                )

        # ADD ADDITIONAL REQUIRED FILES
        # see http://www.gsshawiki.com/Project_File:Required_Inputs
        project_manager.setCard('TOT_TIME', '180')
        project_manager.setCard('TIMESTEP', '10')
        project_manager.setCard('HYD_FREQ', '15')
        # see http://www.gsshawiki.com/Project_File:Output_Files_%E2%80%93_Required
        project_manager.setCard('SUMMARY', '{0}.sum'.format(project_name), add_quotes=True)
        project_manager.setCard('OUTLET_HYDRO', '{0}.otl'.format(project_name), add_quotes=True)
        # see http://www.gsshawiki.com/Project_File:Rainfall_Input_and_Options_%E2%80%93_Required
        project_manager.setCard('PRECIP_UNIF', '')
        project_manager.setCard('RAIN_INTENSITY', '2.4')
        project_manager.setCard('RAIN_DURATION', '30')
        project_manager.setCard('START_DATE', '2017 02 28')
        project_manager.setCard('START_TIME', '14 33')

        # write data
        project_manager.writeInput(session=db_session,
                                   directory=self.gssha_project_directory,
                                   name=project_name)
        db_session.close()
        # compare main project files
        self._compare_basic_model_idx_maps(project_name)

    def test_generate_basic_project_manager(self):
        """
        Tests generating a basic GSSHA project with GSSHAModel
        """

        project_name = "grid_standard_basic_model"

        model = GSSHAModel(project_name=project_name,
                           project_directory=self.gssha_project_directory,
                           mask_shapefile=self.shapefile_path,
                           grid_cell_size=1000,
                           elevation_grid_path=self.elevation_path,
                           out_hydrograph_write_frequency=15,
                           roughness=0.013)
        model.set_event(simulation_start=datetime(2017, 2, 28),
                        simulation_duration=timedelta(seconds=180*60),
                        rain_intensity=2.4,
                        rain_duration=timedelta(seconds=30*60))
        model.write()

        # compare main project files
        self._compare_basic_model(project_name)

    def test_generate_basic_project_manager(self):
        """
        Tests generating a basic GSSHA project with GSSHAModel self-calulating
        grid cell size from elevation grid
        """

        project_name = "grid_standard_basic_model_auto"

        model = GSSHAModel(project_name=project_name,
                           project_directory=self.gssha_project_directory,
                           mask_shapefile=self.shapefile_path,
                           elevation_grid_path=self.elevation_path,
                           out_hydrograph_write_frequency=15,
                           roughness=0.013)
        model.set_event(simulation_start=datetime(2017, 2, 28),
                        simulation_duration=timedelta(seconds=180*60),
                        rain_intensity=2.4,
                        rain_duration=timedelta(seconds=30*60))
        model.write()

        # compare main project files
        self._compare_basic_model(project_name)

    def test_generate_basic_rough_project_manager(self):
        """
        Tests generating a basic GSSHA project with GSSHAModel with roughness
        """

        project_name = "grid_standard_basic_model_land_cover"

        model = GSSHAModel(project_name=project_name,
                           project_directory=self.gssha_project_directory,
                           mask_shapefile=self.shapefile_path,
                           grid_cell_size=1000,
                           elevation_grid_path=self.elevation_path,
                           simulation_timestep=10,
                           out_hydrograph_write_frequency=15,
                           land_use_grid=self.land_use_grid,
                           land_use_grid_id='glcf')

        model.set_event(simulation_start=datetime(2017, 2, 28, 14, 33),
                        simulation_duration=timedelta(seconds=180 * 60),
                        rain_intensity=2.4,
                        rain_duration=timedelta(seconds=30 * 60))
        model.write()

        # compare main project files
        self._compare_basic_model_idx_maps(project_name)

    def test_generate_basic_nodb_project_manager(self):
        """
        Tests generating a basic GSSHA project with GSSHAModel with roughness
        without loading to database
        """

        project_name = "grid_standard_basic_model_land_cover"

        model = GSSHAModel(project_name=project_name,
                           project_directory=self.gssha_project_directory,
                           mask_shapefile=self.shapefile_path,
                           grid_cell_size=1000,
                           elevation_grid_path=self.elevation_path,
                           simulation_timestep=10,
                           out_hydrograph_write_frequency=15,
                           land_use_grid=self.land_use_grid,
                           land_use_grid_id='glcf',
                           load_rasters_to_db=False)

        model.set_event(simulation_start=datetime(2017, 2, 28, 14, 33),
                        simulation_duration=timedelta(seconds=180 * 60),
                        rain_intensity=2.4,
                        rain_duration=timedelta(seconds=30 * 60))
        model.write()

        # compare main project files
        self._compare_basic_model_idx_maps(project_name)


class TestProjectGenerateClean(TestProjectGenerateBase):
    def setUp(self):
        self.compare_path = path.join(self.readDirectory,
                                      'multi_polygon_boundary',
                                      'compare_data')

        self.gssha_project_directory = self.writeDirectory

        self.shapefile_path = path.join(self.writeDirectory,
                                        'corpus_christy.shp')

        self.elevation_path = path.join(self.writeDirectory,
                                        'corpus_christy_dem.tif')

        # copy shapefile
        shapefile_basename = path.join(self.readDirectory,
                                       'multi_polygon_boundary',
                                       'corpus_christy.*')

        for shapefile_part in glob(shapefile_basename):
            try:
                copy(shapefile_part,
                     path.join(self.writeDirectory, path.basename(shapefile_part)))
            except OSError:
                pass

        # copy elevation grid
        try:
            copy(path.join(self.readDirectory, 'multi_polygon_boundary',
                           'corpus_christy_dem.tif'),
                 self.elevation_path)
        except OSError:
            pass


    def test_multi_polygon_error(self):
        """
        Tests generating a basic GSSHA project with GSSHAModel using a
        polygon that has saparate parts
        """

        project_name = "grid_standard_basic_model"

        with pytest.raises(ValueError):
            model = GSSHAModel(project_name=project_name,
                               project_directory=self.gssha_project_directory,
                               mask_shapefile=self.shapefile_path,
                               grid_cell_size=1000,
                               elevation_grid_path=self.elevation_path,
                               simulation_timestep=10,
                               out_hydrograph_write_frequency=15,
                               roughness=0.013,
                               load_rasters_to_db=False)

    def test_multi_polygon_clean(self):
        """
        Tests generating a basic GSSHA project with GSSHAModel using a
        polygon that has saparate parts
        """

        project_name = "grid_standard_basic_model_clean"

        model = GSSHAModel(project_name=project_name,
                           project_directory=self.gssha_project_directory,
                           mask_shapefile=self.shapefile_path,
                           grid_cell_size=1000,
                           elevation_grid_path=self.elevation_path,
                           simulation_timestep=10,
                           out_hydrograph_write_frequency=15,
                           roughness=0.013,
                           load_rasters_to_db=False,
                           auto_clean_mask_shapefile=True,
                           )
        model.write()
        # compare main project files
        self._compare_basic_model(project_name)


if __name__ == '__main__':
    unittest.main()
