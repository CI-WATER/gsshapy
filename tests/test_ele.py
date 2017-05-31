"""
********************************************************************************
* Name: Elevation Tests
* Author: Alan D. Snow
* Created On: February 10, 2016
* License: BSD 3-Clause
********************************************************************************
"""
from glob import glob
from os import path
import unittest
from shutil import copy, copytree

from .template import TestGridTemplate

from gsshapy.orm import ProjectFile, ElevationGridFile
from gsshapy.lib import db_tools as dbt


class TestElevation(TestGridTemplate):
    def setUp(self):
        self.gssha_project_directory = path.join(self.writeDirectory,
                                                 'gssha_project')
        self.gssha_project_file = 'grid_standard_basic.prj'

        self.elevation_path = path.join(self.writeDirectory,
                                        'gmted_elevation.tif')

        self.shapefile_path = path.join(self.writeDirectory,
                                        'phillipines_5070115700.shp')

        self.compare_path = path.join(self.readDirectory,
                                      'phillipines',
                                      'compare_data')

        # copy gssha project
        try:
            copytree(path.join(self.readDirectory, 'phillipines', 'gssha_project'),
                     self.gssha_project_directory)
        except OSError:
            pass

        # copy elevation grid
        try:
            copy(path.join(self.readDirectory, 'phillipines',
                           'gmted_elevation.tif'),
                 self.elevation_path)
        except OSError:
            pass

        # copy shapefile
        shapefile_basename = path.join(self.readDirectory,
                                       'phillipines',
                                       'phillipines_5070115700.*')

        for shapefile_part in glob(shapefile_basename):
            try:
                copy(shapefile_part,
                     path.join(self.writeDirectory, path.basename(shapefile_part)))
            except OSError:
                pass

        # Create Test DB
        self.project_manager, db_sessionmaker = \
            dbt.get_project_session('grid_standard_ele',
                                    self.gssha_project_directory)

        self.db_session = db_sessionmaker()

        # read project file
        self.project_manager.readInput(directory=self.gssha_project_directory,
                                       projectFileName=self.gssha_project_file,
                                       session=self.db_session)
        self.ele_file = ElevationGridFile(project_file=self.project_manager,
                                          session=self.db_session)

    def test_generate_elevation_grid(self):
        """
        Tests generating an elevation grid from raster
        """
        self.ele_file.generateFromRaster(self.elevation_path,
                                         self.shapefile_path)

        # WRITE OUT UPDATED GSSHA PROJECT FILE
        self.project_manager.writeInput(session=self.db_session,
                                        directory=self.gssha_project_directory,
                                        name='grid_standard_ele')
        # compare ele
        new_mask_grid = path.join(self.gssha_project_directory, 'grid_standard_ele.ele')
        compare_msk_file = path.join(self.compare_path, 'grid_standard_ele.ele')
        self._compare_files(compare_msk_file, new_mask_grid, raster=True)
        # compare project files
        generated_prj_file = path.join(self.gssha_project_directory, 'grid_standard_ele.prj')
        compare_prj_file = path.join(self.compare_path, 'grid_standard_ele.prj')
        self._compare_files(generated_prj_file, compare_prj_file)

if __name__ == '__main__':
    unittest.main()
