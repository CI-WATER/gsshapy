'''
********************************************************************************
* Name: Land Cver Tests
* Author: Alan D. Snow
* Created On: February 6, 2016
* License: BSD 3-Clause
********************************************************************************
'''
from glob import glob
from os import path
import os
import unittest
from shutil import copy

from .template import TestGridTemplate

from gsshapy.lib.grid_tools import rasterize_shapefile

class TestResampleShapefile(TestGridTemplate):
    def setUp(self):
        # define global variables
        self.wkt = ('PROJCS["WGS 84 / UTM zone 51N",GEOGCS["WGS 84",'
                    'DATUM["WGS_1984",SPHEROID["WGS 84",6378137,'
                    '298.257223563,AUTHORITY["EPSG","7030"]],'
                    'AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,'
                    'AUTHORITY["EPSG","8901"]],UNIT["degree",'
                    '0.01745329251994328,AUTHORITY["EPSG","9122"]],'
                    'AUTHORITY["EPSG","4326"]],UNIT["metre",1,'
                    'AUTHORITY["EPSG","9001"]],'
                    'PROJECTION["Transverse_Mercator"],'
                    'PARAMETER["latitude_of_origin",0],'
                    'PARAMETER["central_meridian",123],'
                    'PARAMETER["scale_factor",0.9996],'
                    'PARAMETER["false_easting",500000],'
                    'PARAMETER["false_northing",0],'
                    'AUTHORITY["EPSG","32651"],AXIS["Easting",EAST],'
                    'AXIS["Northing",NORTH]]')

        self.shapefile_path = path.join(self.writeDirectory,
                                        'phillipines_5070115700.shp')

        self.projected_shapefile = path.join(self.writeDirectory,
                                             'phillipines_5070115700_projected.shp')
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

    def _before_teardown(self):
        '''
        Method to execute at beginning of tearDown
        '''
        # make sure cleanup worked (fails on Windows)
        if os.name != 'nt':
            assert not path.exists(self.projected_shapefile)

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
        mask_name = 'mask_50.msk'
        new_mask_grid = path.join(self.writeDirectory, mask_name)
        rasterize_shapefile(self.shapefile_path,
                            new_mask_grid,
                            x_num_cells=50,
                            y_num_cells=50,
                            )
        # compare msk
        self._compare_masks(mask_name)

    def test_rasterize_num_cells_utm(self):
        '''
        Tests rasterize_shapefile default using num cells and utm
        '''
        mask_name = 'mask_50_utm.msk'
        new_mask_grid = path.join(self.writeDirectory, mask_name)
        rasterize_shapefile(self.shapefile_path,
                            new_mask_grid,
                            x_num_cells=50,
                            y_num_cells=50,
                            raster_nodata=0,
                            convert_to_utm=True,
                            )
        # compare msk
        self._compare_masks(mask_name)

    def test_rasterize_num_cells_wkt(self):
        '''
        Tests rasterize_shapefile default using num cells and wkt
        '''
        mask_name = 'mask_50_wkt.msk'
        new_mask_grid = path.join(self.writeDirectory, mask_name)
        rasterize_shapefile(self.shapefile_path,
                            new_mask_grid,
                            x_num_cells=50,
                            y_num_cells=50,
                            raster_nodata=0,
                            raster_wkt_proj=self.wkt,
                            )
        # compare msk
        self._compare_masks(mask_name)

    def test_rasterize_num_cells_utm_ascii(self):
        '''
        Tests rasterize_shapefile default using num cells and utm to ascii
        '''
        mask_name = 'mask_50_utm_ascii.msk'
        new_mask_grid = path.join(self.writeDirectory, mask_name)
        gr = rasterize_shapefile(self.shapefile_path,
                                 x_num_cells=50,
                                 y_num_cells=50,
                                 raster_nodata=0,
                                 convert_to_utm=True,
                                 as_gdal_grid=True,
                                 )
        gr.to_grass_ascii(new_mask_grid, print_nodata=False)
        # compare msk
        self._compare_masks(mask_name)

    def test_rasterize_num_cells_ascii(self):
        '''
        Tests rasterize_shapefile default using num cells to ascii
        '''
        mask_name = 'mask_50_ascii.msk'
        new_mask_grid = path.join(self.writeDirectory, mask_name)
        gr = rasterize_shapefile(self.shapefile_path,
                                 x_num_cells=50,
                                 y_num_cells=50,
                                 raster_nodata=0,
                                 as_gdal_grid=True,
                                 )
        gr.to_grass_ascii(new_mask_grid, print_nodata=False)
        # compare msk
        self._compare_masks(mask_name)

    def test_rasterize_num_cells_wkt_ascii(self):
        '''
        Tests rasterize_shapefile default using num cells
        '''
        mask_name = 'mask_50_wkt_ascii.msk'
        new_mask_grid = path.join(self.writeDirectory, mask_name)
        gr = rasterize_shapefile(self.shapefile_path,
                                 x_num_cells=50,
                                 y_num_cells=50,
                                 raster_nodata=0,
                                 raster_wkt_proj=self.wkt,
                                 as_gdal_grid=True,
                                 )
        gr.to_grass_ascii(new_mask_grid, print_nodata=False)
        # compare msk
        self._compare_masks(mask_name)

    def test_rasterize_cell_size_ascii(self):
        '''
        Tests rasterize_shapefile default using cell size to ascii
        '''
        mask_name = 'mask_cell_size_ascii.msk'
        new_mask_grid = path.join(self.writeDirectory, mask_name)
        gr = rasterize_shapefile(self.shapefile_path,
                                 x_cell_size=0.01,
                                 y_cell_size=0.01,
                                 raster_nodata=0,
                                 as_gdal_grid=True,
                                 )
        gr.to_grass_ascii(new_mask_grid, print_nodata=False)
        # compare msk
        self._compare_masks(mask_name)

    def test_rasterize_cell_size_ascii_utm(self):
        '''
        Tests rasterize_shapefile using cell size to ascii in utm
        '''
        mask_name = 'mask_cell_size_ascii_utm.msk'
        new_mask_grid = path.join(self.writeDirectory, mask_name)
        gr = rasterize_shapefile(self.shapefile_path,
                                 x_cell_size=1000,
                                 y_cell_size=1000,
                                 raster_nodata=0,
                                 as_gdal_grid=True,
                                 convert_to_utm=True,
                                 )
        gr.to_grass_ascii(new_mask_grid, print_nodata=False)

        # compare msk
        self._compare_masks(mask_name)

if __name__ == '__main__':
    unittest.main()
