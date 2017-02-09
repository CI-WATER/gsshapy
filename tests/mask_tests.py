'''
********************************************************************************
* Name: Mask Tests
* Author: Alan D. Snow
* Created On: February 6, 2016
* License: BSD 3-Clause
********************************************************************************
'''
from glob import glob
from os import path
import unittest
from shutil import copy

from .template import TestGridTemplate

from gsshapy.orm import WatershedMaskFile

class TestMask(TestGridTemplate):
    def setUp(self):
        self.msk_file = WatershedMaskFile()
        self.shapefile_path = path.join(self.writeDirectory,
                                        'phillipines_5070115700.shp')

        self.compare_path = path.join(self.readDirectory,
                                      'phillipines',
                                      'compare_data')
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

    def _compare_masks(self, mask_name):
        '''
        compare mask files
        '''
        new_mask_grid = path.join(self.writeDirectory, mask_name)
        compare_msk_file = path.join(self.compare_path, mask_name)
        self._compare_files(compare_msk_file, new_mask_grid, raster=True)

    def test_rasterize_num_cells(self):
        '''
        Tests rasterize_shapefile default using num cells
        '''
        mask_name = 'mask_50_utm_ascii.msk'
        new_mask_grid = path.join(self.writeDirectory, mask_name)
        self.msk_file.generateFromWatershedShapefile(self.shapefile_path,
                                                     new_mask_grid,
                                                     x_num_cells=50,
                                                     y_num_cells=50,
                                                     )
        # compare msk
        self._compare_masks(mask_name)


    def test_rasterize_cell_size_ascii_utm(self):
        '''
        Tests rasterize_shapefile using cell size to ascii in utm
        '''
        mask_name = 'mask_cell_size_ascii_utm.msk'
        new_mask_grid = path.join(self.writeDirectory, mask_name)
        self.msk_file.generateFromWatershedShapefile(self.shapefile_path,
                                                     new_mask_grid,
                                                     x_cell_size=1000,
                                                     y_cell_size=1000,
                                                     )
        # compare msk
        self._compare_masks(mask_name)

#TODO: Add tests from existing project file

if __name__ == '__main__':
    unittest.main()
