"""
********************************************************************************
* Name: Land Cover Tests
* Author: Alan D. Snow
* Created On: February 6, 2016
* License: BSD 3-Clause
********************************************************************************
"""
from os import path
import unittest
from shutil import copy, copytree

from .template import TestGridTemplate

from gsshapy.orm import ProjectFile
from gsshapy.lib import db_tools as dbt


class TestLandCover(TestGridTemplate):
    def setUp(self):
        # define global variables
        self.gssha_project_directory = path.join(self.writeDirectory,
                                                 'gssha_project')
        self.gssha_project_file = 'grid_standard.prj'
        self.land_use_grid = path.join(self.writeDirectory, 'LC_hd_global_2012.tif')

        # copy gssha project
        try:
            copytree(path.join(self.readDirectory, "gssha_project"),
                     self.gssha_project_directory)
        except OSError:
            pass

        # copy land cover data
        try:
            copy(path.join(self.readDirectory, 'land_cover', 'LC_hd_global_2012.tif'),
                 self.land_use_grid)
        except OSError:
            pass

    def test_add_land_cover_map_table(self):
        """
        Tests adding land cover to map table
        """
        land_use_to_roughness_table = path.join(path.dirname(path.realpath(__file__)),
                                                '..', 'gsshapy',
                                                'grid', 'land_cover',
                                                'land_cover_glcf_modis.txt'
                                                )
        # Create Test DB
        sqlalchemy_url, sql_engine = dbt.init_sqlite_memory()

        # Create DB Sessions
        db_session = dbt.create_session(sqlalchemy_url, sql_engine)

        # Instantiate GSSHAPY object for reading to database
        project_manager = ProjectFile()

        # Call read method
        project_manager.readInput(directory=self.gssha_project_directory,
                                  projectFileName=self.gssha_project_file,
                                  session=db_session)

        project_manager.mapTableFile.addRoughnessMapFromLandUse("roughness",
                                                                db_session,
                                                                self.land_use_grid,
                                                                land_use_to_roughness_table,
                                                                #land_use_grid_id='glcf',
                                                                )
        # WRITE OUT UPDATED GSSHA PROJECT FILE
        project_manager.writeInput(session=db_session,
                                   directory=self.gssha_project_directory,
                                   name=path.splitext(self.gssha_project_file)[0])

        db_session.close()

        # compare prj
        original_prj_file = path.join(self.readDirectory, 'land_cover', 'grid_standard.prj')
        new_prj_file = path.join(self.gssha_project_directory, 'grid_standard.prj')
        self._compare_files(original_prj_file, new_prj_file)
        # compare cmt
        original_cmt_file = path.join(self.readDirectory, 'land_cover', 'grid_standard.cmt')
        new_cmt_file = path.join(self.gssha_project_directory, 'grid_standard.cmt')
        self._compare_files(original_cmt_file, new_cmt_file)
        # compare idx
        original_idx_file = path.join(self.readDirectory, 'land_cover', 'roughness.idx')
        new_idx_file = path.join(self.gssha_project_directory, 'roughness.idx')
        self._compare_files(original_idx_file, new_idx_file, raster=True)

    def test_add_land_cover_map_table_twice(self):
        """
        Tests adding land cover to map table run twice
        """
        # Create Test DB
        sqlalchemy_url, sql_engine = dbt.init_sqlite_memory()

        # run twice to ensure uniqueness
        for i in range(2):
            # Create DB Sessions
            db_session = dbt.create_session(sqlalchemy_url, sql_engine)

            # Instantiate GSSHAPY object for reading to database
            project_manager = ProjectFile()

            # Call read method
            project_manager.readInput(directory=self.gssha_project_directory,
                                      projectFileName=self.gssha_project_file,
                                      session=db_session)

            project_manager.mapTableFile.addRoughnessMapFromLandUse("roughness",
                                                                    db_session,
                                                                    self.land_use_grid,
                                                                    land_use_grid_id='glcf',
                                                                    )
            # WRITE OUT UPDATED GSSHA PROJECT FILE
            project_manager.writeInput(session=db_session,
                                       directory=self.gssha_project_directory,
                                       name=path.splitext(self.gssha_project_file)[0])

            db_session.close()

        # compare prj
        original_prj_file = path.join(self.readDirectory, 'land_cover', 'grid_standard.prj')
        new_prj_file = path.join(self.gssha_project_directory, 'grid_standard.prj')
        self._compare_files(original_prj_file, new_prj_file)
        # compare cmt
        original_cmt_file = path.join(self.readDirectory, 'land_cover', 'grid_standard.cmt')
        new_cmt_file = path.join(self.gssha_project_directory, 'grid_standard.cmt')
        self._compare_files(original_cmt_file, new_cmt_file)
        # compare idx
        original_idx_file = path.join(self.readDirectory, 'land_cover', 'roughness.idx')
        new_idx_file = path.join(self.gssha_project_directory, 'roughness.idx')
        self._compare_files(original_idx_file, new_idx_file, raster=True)

if __name__ == '__main__':
    unittest.main()
