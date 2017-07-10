"""
********************************************************************************
* Name: ERA Interim Tests
* Author: Alan D. Snow
* Created On: April 27, 2017
* License: BSD 3-Clause
********************************************************************************
"""
from datetime import datetime
import os
import unittest
from shutil import copytree

from .template import TestGridTemplate
from gsshapy.grid import ERAtoGSSHA


class TestERAItoGSSHA(TestGridTemplate):
    def setUp(self):
        # define global variables
        self.hmet_read_directory = os.path.join(self.readDirectory,
                                                "erai_hmet_data")
        self.hmet_write_directory = os.path.join(self.writeDirectory,
                                                 "erai_hmet_data")
        self.gssha_project_folder = os.path.join(self.writeDirectory,
                                                 "gssha_project")
        # create folder to dump output HMET into
        try:
            os.mkdir(self.hmet_write_directory)
        except OSError:
            pass

        # copy gssha project & WRF data
        try:
            copytree(os.path.join(self.readDirectory, "gssha_project"),
                     self.gssha_project_folder)
        except OSError:
            pass
        try:
            copytree(os.path.join(self.readDirectory, "erai_raw_data"),
                     os.path.join(self.writeDirectory, "erai_raw_data"))
        except OSError:
            pass

        self.data_var_map_array = [
           ['precipitation_inc', 'tp'],
           ['pressure', 'sp'],
           ['relative_humidity_dew', ['d2m','t2m']],
           ['wind_speed', ['u10', 'v10']],
           ['direct_radiation_j', ['ssrd', 'tcc']],
           ['diffusive_radiation_j', ['ssrd', 'tcc']],
           ['temperature', 't2m'],
           ['cloud_cover', 'tcc'],
        ]

        erai_folder = os.path.join(self.writeDirectory, 'erai_raw_data')
        # from datetime import datetime
        self.l2g = ERAtoGSSHA(gssha_project_folder=self.gssha_project_folder,
                              gssha_project_file_name='grid_standard.prj',
                              lsm_input_folder_path=erai_folder,
                              # download_end_datetime=datetime(2016, 1, 4),
                              # download_start_datetime=datetime(2016, 1, 2)
                              )

    def _before_teardown(self):
        self.l2g.xd.close()
        self.l2g = None

    def test_erai_gage_file_write(self):
        """
        Test ERA Interim lsm_precip_to_gssha_precip_gage write method
        """
        out_gage_file = os.path.join(self.writeDirectory, 'gage_test_erai.gag')
        self.l2g.lsm_precip_to_gssha_precip_gage(out_gage_file,
                                                 lsm_data_var='tp',
                                                 precip_type='GAGES')
        # Test
        compare_gag_file = os.path.join(self.readDirectory, 'gage_test_erai.gag')
        self._compare_files(out_gage_file, compare_gag_file, precision=5)

    def test_erai_netcdf_file_write(self):
        """
        Test ERA Interim lsm_data_to_subset_netcdf write method
        """
        netcdf_file_path = os.path.join(self.writeDirectory,
                                        'gssha_dynamic_erai.nc')
        self.l2g.lsm_data_to_subset_netcdf(netcdf_file_path,
                                           self.data_var_map_array)

        # compare netcdf files
        self._compare_netcdf_files("gssha_dynamic_erai", "gssha_dynamic_erai")

    def test_erai_ascii_file_write(self):
        """
        Test ERA Interim lsm_data_to_arc_ascii write method
        """
        self.l2g.lsm_data_to_arc_ascii(self.data_var_map_array,
                                       self.hmet_write_directory)

        # Compare all files
        compare_directory = os.path.join(self.readDirectory, "erai_hmet_data")
        self._compare_directories(self.hmet_write_directory,
                                  compare_directory,
                                  ignore_file="hmet_file_list.txt",
                                  raster=True)

    def test_erai_grid_snow_file_write(self):
        """
        Test lsm_var_to_grid write method
        """
        out_grid_file = os.path.join(self.writeDirectory, 'swe_grid_erai.asc')
        self.l2g.lsm_var_to_grid(out_grid_file=out_grid_file,
                                 lsm_data_var='sp',
                                 gssha_convert_var='swe')

        # Test
        compare_grid_file = os.path.join(self.readDirectory, 'swe_grid_erai.asc')
        self._compare_files(out_grid_file, compare_grid_file, precision=5)

    def test_erai_grid_snow_file_write_time(self):
        """
        Test WRF lsm_var_to_grid write method
        """
        out_grid_file = os.path.join(self.writeDirectory, 'swe_grid_erai.asc')
        self.l2g.lsm_var_to_grid(out_grid_file=out_grid_file,
                                 lsm_data_var='sp',
                                 gssha_convert_var='swe',
                                 time_step=datetime(2016, 1, 2))

        # Test
        compare_grid_file = os.path.join(self.readDirectory, 'swe_grid_erai.asc')
        self._compare_files(out_grid_file, compare_grid_file, precision=5)


if __name__ == '__main__':
    unittest.main()
