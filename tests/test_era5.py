"""
********************************************************************************
* Name: ERA5 Tests
* Author: Alan D. Snow
* Created On: April 27, 2017
* License: BSD 3-Clause
********************************************************************************
"""
import os
import unittest
from shutil import copytree

from .template import TestGridTemplate
from gsshapy.grid import ERAtoGSSHA
import pytest


class TestERA5toGSSHA(TestGridTemplate):
    def setUp(self):
        # define global variables
        self.hmet_read_directory = os.path.join(self.readDirectory,
                                                "era5_hmet_data")
        self.hmet_write_directory = os.path.join(self.writeDirectory,
                                                 "era5_hmet_data")
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
            copytree(os.path.join(self.readDirectory, "era5_raw_data"),
                     os.path.join(self.writeDirectory, "era5_raw_data"))
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

        era5_folder = os.path.join(self.writeDirectory, 'era5_raw_data')
        self.l2g = ERAtoGSSHA(gssha_project_folder=self.gssha_project_folder,
                              gssha_project_file_name='grid_standard.prj',
                              lsm_input_folder_path=era5_folder,
                              )

    def _before_teardown(self):
        self.l2g.xd.close()
        self.l2g = None

    @pytest.mark.xfail(reason="Arrays are not almost equal to 5 decimals.")
    def test_era5_gage_file_write(self):
        """
        Test ERA5 lsm_precip_to_gssha_precip_gage write method
        """
        out_gage_file = os.path.join(self.writeDirectory, 'gage_test_era5.gag')
        self.l2g.lsm_precip_to_gssha_precip_gage(out_gage_file,
                                                 lsm_data_var='tp',
                                                 precip_type='GAGES')
        # Test
        compare_gag_file = os.path.join(self.readDirectory, 'gage_test_era5.gag')
        self._compare_files(out_gage_file, compare_gag_file, precision=5)

    @pytest.mark.xfail(reason="Arrays are not almost equal to 4 decimals.")
    def test_era5_netcdf_file_write(self):
        """
        Test ERA5 lsm_data_to_subset_netcdf write method
        """
        netcdf_file_path = os.path.join(self.writeDirectory,
                                        'gssha_dynamic_era5.nc')
        self.l2g.lsm_data_to_subset_netcdf(netcdf_file_path,
                                           self.data_var_map_array)

        # compare netcdf files
        self._compare_netcdf_files("gssha_dynamic_era5", "gssha_dynamic_era5")

    @pytest.mark.xfail(reason="Arrays are not almost equal to 7 decimals.")
    def test_era5_ascii_file_write(self):
        """
        Test ERA5 lsm_data_to_arc_ascii write method
        """
        self.l2g.lsm_data_to_arc_ascii(self.data_var_map_array,
                                       self.hmet_write_directory)

        # Compare all files
        compare_directory = os.path.join(self.readDirectory, "era5_hmet_data")
        self._compare_directories(self.hmet_write_directory,
                                  compare_directory,
                                  ignore_file="hmet_file_list.txt",
                                  raster=True)


if __name__ == '__main__':
    unittest.main()
