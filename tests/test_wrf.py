"""
********************************************************************************
* Name: WRF Tests
* Author: Alan D. Snow
* Created On: September 16, 2016
* License: BSD 3-Clause
********************************************************************************
"""
from datetime import datetime
from glob import glob
import os
from osgeo import gdalconst
import unittest
from shutil import copytree

from .template import TestGridTemplate
from gsshapy.grid import GRIDtoGSSHA
import pytest


class TestLSMtoGSSHA(TestGridTemplate):
    def setUp(self):
        # define global variables
        self.hmet_read_directory = os.path.join(self.readDirectory,
                                                "wrf_hmet_data")
        self.hmet_write_directory = os.path.join(self.writeDirectory,
                                                 "wrf_hmet_data")
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
            copytree(os.path.join(self.readDirectory, "wrf_raw_data", "gssha_d03_nc"),
                     os.path.join(self.writeDirectory, "wrf_raw_data"))
        except OSError:
            pass

        self.data_var_map_array = [
                                   ['precipitation_acc', ['RAINC', 'RAINNC']],
                                   ['pressure', 'PSFC'],
                                   ['relative_humidity', ['Q2', 'PSFC', 'T2']],
                                   ['wind_speed', ['U10', 'V10']],
                                   ['direct_radiation', ['SWDOWN', 'DIFFUSE_FRAC']],
                                   ['diffusive_radiation', ['SWDOWN', 'DIFFUSE_FRAC']],
                                   ['temperature', 'T2'],
                                   ['cloud_cover', 'CLDFRA'],
                                  ]
        # pre computed
        self.data_var_map_array_pre = [
                                   ['precipitation_acc', 'RUNPCP'],
                                   ['pressure_hg', 'PSFCInHg'],
                                   ['relative_humidity', 'RH2'],
                                   ['direct_radiation', ['SWDOWN', 'DIFFUSE_FRAC']],
                                   ['diffusive_radiation', ['SWDOWN', 'DIFFUSE_FRAC']],
                                   ['wind_speed_kts', 'SPEED10'],
                                   ['temperature_f', 'T2F'],
                                   ['cloud_cover_pc' , 'SKYCOVER'],
                                  ]
        # binary cloud cover
        self.data_var_map_array_bin = [
                                   ['precipitation_acc', 'RUNPCP'],
                                   ['pressure_hg', 'PSFCInHg'],
                                   ['relative_humidity', 'RH2'],
                                   ['direct_radiation', ['SWDOWN', 'DIFFUSE_FRAC']],
                                   ['diffusive_radiation', ['SWDOWN', 'DIFFUSE_FRAC']],
                                   ['wind_speed_kts', 'SPEED10'],
                                   ['temperature_f', 'T2F'],
                                   ['cloud_cover_bin' , 'CLDFRA'],
                                  ]

        wrf_folder = os.path.join(self.writeDirectory, 'wrf_raw_data')
        self.l2g = GRIDtoGSSHA(gssha_project_folder=self.gssha_project_folder,
                               gssha_project_file_name='grid_standard.prj',
                               lsm_input_folder_path=wrf_folder,
                               lsm_search_card="gssha_d03_*.nc",
                               lsm_lat_var='XLAT',
                               lsm_lon_var='XLONG',
                               lsm_time_var='Times',
                               lsm_lat_dim='south_north',
                               lsm_lon_dim='west_east',
                               lsm_time_dim='Time',
                              )

    def _before_teardown(self):
        self.l2g.xd.close()
        self.l2g = None

    @pytest.mark.xfail(reason="Arrays are not almost equal to 5 decimals.")
    def test_wrf_gage_file_write(self):
        """
        Test WRF lsm_precip_to_gssha_precip_gage write method
        """
        out_gage_file = os.path.join(self.writeDirectory, 'gage_test_wrf.gag')
        self.l2g.lsm_precip_to_gssha_precip_gage(out_gage_file,
                                                 lsm_data_var=['RAINC', 'RAINNC'],
                                                 precip_type='ACCUM')

        # Test
        compare_gag_file = os.path.join(self.readDirectory, 'gage_test_wrf.gag')
        self._compare_files(out_gage_file, compare_gag_file, precision=5)

    @pytest.mark.xfail(reason="Arrays are not almost equal to 7 decimals.")
    def test_wrf_netcdf_file_write(self):
        """
        Test WRF lsm_data_to_subset_netcdf write method
        """
        netcdf_file_path = os.path.join(self.writeDirectory,
                                        'gssha_dynamic_wrf.nc')
        self.l2g.lsm_data_to_subset_netcdf(netcdf_file_path,
                                           self.data_var_map_array)

        # compare netcdf files
        self._compare_netcdf_files("gssha_dynamic_wrf", "gssha_dynamic_wrf")

    def test_wrf_netcdf_file_write_resample(self):
        """
        Test WRF lsm_data_to_subset_netcdf resample write method
        """
        netcdf_file_path = os.path.join(self.writeDirectory,
                                        'gssha_dynamic_wrf_resample.nc')
        self.l2g.lsm_data_to_subset_netcdf(netcdf_file_path,
                                           self.data_var_map_array,
                                           resample_method=gdalconst.GRA_Average)

        # compare netcdf files
        self._compare_netcdf_files("gssha_dynamic_wrf_resample",
                                   "gssha_dynamic_wrf_resample")

    @pytest.mark.xfail(reason="Arrays are not almost equal to 5 decimals.")
    def test_wrf_ascii_file_write(self):
        """
        Test WRF lsm_data_to_arc_ascii write method
        """
        self.l2g.lsm_data_to_arc_ascii(self.data_var_map_array,
                                       self.hmet_write_directory)

        # Compare all files
        compare_directory = os.path.join(self.readDirectory, "wrf_hmet_data")
        self._compare_directories(self.hmet_write_directory,
                                  compare_directory,
                                  ignore_file="hmet_file_list.txt",
                                  raster=True,
                                  precision=4)

    @pytest.mark.xfail(reason="Arrays are not almost equal to 5 decimals.")
    def test_wrf_ascii_file_write_pre(self):
        """
        Test WRF lsm_data_to_arc_ascii write method pre-computed
        """
        self.l2g.lsm_data_to_arc_ascii(self.data_var_map_array_pre,
                                       self.hmet_write_directory)

        # Compare all files
        compare_directory = os.path.join(self.readDirectory, "wrf_hmet_data")
        self._compare_directories(self.hmet_write_directory,
                                  compare_directory,
                                  ignore_file="hmet_file_list.txt",
                                  raster=True,
                                  precision=1)

    @pytest.mark.xfail(reason="Arrays are not almost equal to 5 decimals.")
    def test_wrf_ascii_file_write_bin(self):
        """
        Test WRF lsm_data_to_arc_ascii write method with binary cloud cover
        """
        self.l2g.lsm_data_to_arc_ascii(self.data_var_map_array_bin,
                                       self.hmet_write_directory)

        # Compare all cloud files
        compare_files = sorted(glob(os.path.join(self.readDirectory,
                                                 "wrf_hmet_clod_bin_data",
                                                 "*_Clod_bin.asc")))
        output_files = sorted(glob(os.path.join(self.hmet_write_directory,
                                                "*_Clod.asc")))

        assert len(compare_files) == len(output_files)
        for compare_file, output_file in zip(compare_files, output_files):
            self._compare_files(compare_file,
                                output_file,
                                raster=True,
                                precision=4)

    def test_wrf_grid_snow_file_write(self):
        """
        Test WRF lsm_var_to_grid write method
        """
        out_grid_file = os.path.join(self.writeDirectory, 'swe_grid_wrf.asc')
        self.l2g.lsm_var_to_grid(out_grid_file=out_grid_file,
                                 lsm_data_var='RAINC',
                                 gssha_convert_var='swe')

        # Test
        compare_grid_file = os.path.join(self.readDirectory, 'swe_grid_wrf.asc')
        self._compare_files(out_grid_file, compare_grid_file, precision=5)

    def test_wrf_grid_snow_file_write_time(self):
        """
        Test WRF lsm_var_to_grid write method
        """
        out_grid_file = os.path.join(self.writeDirectory, 'swe_grid_wrf.asc')
        self.l2g.lsm_var_to_grid(out_grid_file=out_grid_file,
                                 lsm_data_var='RAINC',
                                 gssha_convert_var='swe',
                                 time_step=datetime(2016, 8, 23, 22))

        # Test
        compare_grid_file = os.path.join(self.readDirectory, 'swe_grid_wrf.asc')
        self._compare_files(out_grid_file, compare_grid_file, precision=5)


if __name__ == '__main__':
    unittest.main()
