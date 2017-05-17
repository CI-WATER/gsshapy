"""
********************************************************************************
* Name: NWM Tests
* Author: Alan D. Snow
* Created On: September 16, 2016
* License: BSD 3-Clause
********************************************************************************
"""
import os
from osgeo import gdalconst
import unittest
from shutil import copytree

from .template import TestGridTemplate
from gsshapy.grid import NWMtoGSSHA


class TestNWMtoGSSHA(TestGridTemplate):
    def setUp(self):
        gssha_project_folder = os.path.join(self.writeDirectory,
                                            "gssha_project")
        nwm_input_folder = os.path.join(self.writeDirectory, "nwm_raw_data")
        # copy gssha project & NWM data
        try:
            copytree(os.path.join(self.readDirectory, "gssha_project"),
                     gssha_project_folder)
        except OSError:
            pass
        try:
            copytree(os.path.join(self.readDirectory, "nwm_raw_data"),
                     nwm_input_folder)
        except OSError:
            pass

        self.l2g = NWMtoGSSHA(gssha_project_folder=gssha_project_folder,
                              gssha_project_file_name='grid_standard.prj',
                              lsm_input_folder_path=nwm_input_folder)

    def _before_teardown(self):
        self.l2g.xd.close()
        self.l2g = None

    def test_wrf_gage_file_write(self):
        """
        Test WRF lsm_precip_to_gssha_precip_gage write method
        """
        out_gage_file = os.path.join(self.writeDirectory, 'gage_test_nwm.gag')
        self.l2g.lsm_precip_to_gssha_precip_gage(out_gage_file,
                                                 lsm_data_var='RAINRATE',
                                                 precip_type='ACCUM')

        # Test
        compare_gag_file = os.path.join(self.readDirectory, 'gage_test_nwm.gag')
        self._compare_files(out_gage_file, compare_gag_file, precision=5)

if __name__ == '__main__':
    unittest.main()
