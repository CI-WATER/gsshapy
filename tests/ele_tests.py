'''
********************************************************************************
* Name: Elevation Tests
* Author: Alan D. Snow
* Created On: February 10, 2016
* License: BSD 3-Clause
********************************************************************************
'''
from glob import glob
from os import path, chdir
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

        self.compare_path = path.join(self.readDirectory,
                                      'phillipines',
                                      'compare_data')

        # copy gssh project
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

        # Create Test DB
        sqlalchemy_url, sql_engine = dbt.init_sqlite_memory()

        # Create DB Sessions
        self.db_session = dbt.create_session(sqlalchemy_url, sql_engine)

        # Instantiate GSSHAPY object for reading to database
        self.project_manager = ProjectFile(name='grid_standard_ele')

        # read project file
        self.project_manager.readInput(directory=self.gssha_project_directory,
                                       projectFileName=self.gssha_project_file,
                                       session=self.db_session)
        self.ele_file = ElevationGridFile(project_file=self.project_manager,
                                          session=self.db_session)
        chdir(self.gssha_project_directory)

    def test_generate_elevation_grid(self):
        '''
        Tests generating an elevation grid from raster
        '''
        self.ele_file.generateFromRaster(self.elevation_path)

        # WRITE OUT UPDATED GSSHA PROJECT FILE
        self.project_manager.writeInput(session=self.db_session,
                                        directory=self.gssha_project_directory,
                                        name='grid_standard_ele')
        # compare ele
        new_mask_grid = path.join(self.gssha_project_directory, 'grid_standard_basic.ele')
        compare_msk_file = path.join(self.compare_path, 'grid_standard_ele.ele')
        self._compare_files(compare_msk_file, new_mask_grid, raster=True)
        # compare project files
        generated_prj_file = path.join(self.gssha_project_directory, 'grid_standard_ele.prj')
        compare_prj_file = path.join(self.compare_path, 'grid_standard_ele.prj')
        self._compare_files(generated_prj_file, compare_prj_file)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
