'''
********************************************************************************
* Name: HRRR Tests
* Author: Alan D. Snow
* Created On: September 16, 2016
* License: BSD 3-Clause
********************************************************************************
'''
import unittest
import os
from shutil import copytree
import sys

import pytest

from .template import TestGridTemplate
from gsshapy.grid import HRRRtoGSSHA
###### ----------
### HRRR INPUT
###### ----------
##FILE VARIABLES
##name, shortName
##Surface pressure, sp
##Temperature, t
##2 metre temperature, 2t
##Surface air relative humidity, 2r
##10 metre U wind component, 10u
##10 metre V wind component, 10v
##Precipitation rate, prate
##Downward short-wave radiation flux, dswrf

@pytest.mark.skipif(sys.version_info > (3, 0),
                    reason="pynio only works on Python 2")
@pytest.mark.skipif(os.name == 'nt',
                    reason="pynio not available on Windows")
class TestHRRRtoGSSHA(TestGridTemplate):
    def setUp(self):
        # define global variables
        self.hmet_read_directory = os.path.join(self.readDirectory,
                                                "hrrr_hmet_data")
        self.hmet_write_directory = os.path.join(self.writeDirectory,
                                                 "hrrr_hmet_data")
        self.gssha_project_folder = os.path.join(self.writeDirectory,
                                                 "gssha_project")

        # create folder to dump output HMET into
        try:
            os.mkdir(self.hmet_write_directory)
        except OSError:
            pass

        # copy gssha project & HRRR data
        try:
            copytree(os.path.join(self.readDirectory, "gssha_project"),
                     self.gssha_project_folder)
        except OSError:
            pass
        try:
            copytree(os.path.join(self.readDirectory, "hrrr_raw_data"),
                     os.path.join(self.writeDirectory, "hrrr_raw_data"))
        except OSError:
            pass
        self.data_var_map_array = [
                                   ['precipitation_rate', 'PRATE_P0_L1_GLC0'],
                                   ['pressure', 'PRES_P0_L1_GLC0'],
                                   ['relative_humidity', 'RH_P0_L103_GLC0'],
                                   ['wind_speed', ['UGRD_P0_L103_GLC0', 'VGRD_P0_L103_GLC0']],
                                   ['direct_radiation_cc', ['DSWRF_P0_L1_GLC0', 'TCDC_P0_L10_GLC0']],
                                   ['diffusive_radiation_cc', ['DSWRF_P0_L1_GLC0', 'TCDC_P0_L10_GLC0']],
                                   ['temperature', 'TMP_P0_L1_GLC0'],
                                   ['cloud_cover_pc', 'TCDC_P0_L10_GLC0'],
                                  ]
        hrrr_folder = os.path.join(self.writeDirectory,
                                   'hrrr_raw_data', '20160914')
        self.h2g = HRRRtoGSSHA(gssha_project_folder=self.gssha_project_folder,
                               gssha_project_file_name='grid_standard.prj',
                               lsm_input_folder_path=hrrr_folder,
                               lsm_search_card="hrrr.t01z.wrfsfcf*.grib2",
                               )

    def test_hrrr_gage_file_write(self):
        '''
        Test HRRR lsm_precip_to_gssha_precip_gage write method
        '''
        out_gage_file = os.path.join(self.writeDirectory,
                                     'gage_test_hrrr.gag')
        self.h2g.lsm_precip_to_gssha_precip_gage(out_gage_file,
                                                 lsm_data_var='PRATE_P0_L1_GLC0',
                                                 precip_type='RADAR')

        # Test
        compare_gag_file = os.path.join(self.readDirectory, 'gage_test_hrrr.gag')
        self._compare_files(out_gage_file, compare_gag_file)

    def test_hrrr_netcdf_file_write(self):
        '''
        Test HRRR lsm_data_to_subset_netcdf write method
        '''
        netcdf_file_path = os.path.join(self.writeDirectory,
                                        'gssha_dynamic_hrrr.nc')
        self.h2g.lsm_data_to_subset_netcdf(netcdf_file_path,
                                           self.data_var_map_array)

        # compare netcdf files
        self._compare_netcdf_files("gssha_dynamic_hrrr",
                                   "gssha_dynamic_hrrr")

    def test_hrrr_ascii_file_write(self):
        '''
        Test HRRR lsm_data_to_arc_ascii write method
        '''
        self.h2g.lsm_data_to_arc_ascii(self.data_var_map_array,
                                       self.hmet_write_directory)

        # Compare all files
        compare_directory = os.path.join(self.readDirectory,
                                         "hrrr_hmet_data")
        self._compare_directories(compare_directory,
                                  self.hmet_write_directory,
                                  ignore_file="hmet_file_list.txt",
                                  raster=True)

if __name__ == '__main__':
    unittest.main()
