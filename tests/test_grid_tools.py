'''
********************************************************************************
* Name: Test Grid Tools
* Author: Alan D. Snow
* Created On: March 31, 2017
* License: BSD 3-Clause
********************************************************************************
'''
from numpy.testing import assert_almost_equal
from os import path
from pyproj import Proj
import unittest
from shutil import copy

from .template import TestGridTemplate

from gsshapy.lib.grid_tools import GDALGrid, ArrayGrid, GSSHAGrid

class TestResampleShapefile(TestGridTemplate):
    def setUp(self):
        base_input_raster = path.join(self.readDirectory,
                                      'phillipines',
                                      'gmted_elevation.tif')

        self.input_raster = path.join(self.writeDirectory,
                                      'test_grid.tif')

        self.compare_path = path.join(self.readDirectory,
                                      'gdal_grid')


        try:
            copy(base_input_raster, self.input_raster)
        except OSError:
            pass

    def test_gdal_grid(self):
        '''
        Tests rasterize_shapefile default using num cells
        '''
        grid = GDALGrid(self.input_raster)

        # check properties
        assert_almost_equal(grid.geotransform,
                            (120.99986111111112,
                            0.008333333333333333,
                            0.0,
                            16.008194444444445,
                            0.0,
                            -0.008333333333333333))
        assert grid.x_size == 120
        assert grid.y_size == 120
        assert grid.wkt == ('GEOGCS["WGS 84",DATUM["WGS_1984",'
                            'SPHEROID["WGS 84",6378137,298.257223563,'
                            'AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG",'
                            '"6326"]],PRIMEM["Greenwich",0],UNIT["degree",'
                            '0.0174532925199433],AUTHORITY["EPSG","4326"]]')
        assert grid.proj4 == '+proj=longlat +datum=WGS84 +no_defs '
        assert isinstance(grid.proj, Proj)
        assert grid.epsg == '4326'

        # check functions
        assert_almost_equal(grid.bounds(),
                            (120.99986111111112,
                             121.99986111111112,
                             15.008194444444445,
                             16.008194444444445))
        assert_almost_equal(grid.bounds(as_geographic=True),
                            (120.99986111111112,
                             121.99986111111112,
                             15.008194444444445,
                             16.008194444444445))
        assert_almost_equal(grid.bounds(as_utm=True),
                            (284940.2424665766,
                             393009.70510977274,
                             1659170.2715823832,
                             1770872.3212051827))
        x_loc, y_loc = grid.pixel2coord(5,10)
        assert_almost_equal((x_loc, y_loc),
                            (121.04569444444445, 15.920694444444445))

        assert grid.coord2pixel(x_loc, y_loc) == (5, 10)
        lon, lat = grid.pixel2lonlat(5,10)
        assert_almost_equal((lon, lat),
                            (121.04569444444445, 15.920694444444445))
        assert grid.lonlat2pixel(lon, lat) == (5, 10)

        # check write functions
        projection_name = 'test_projection.prj'
        out_projection_file = path.join(self.writeDirectory, projection_name)
        grid.write_prj(out_projection_file)
        compare_projection_file = path.join(self.compare_path, projection_name)
        self._compare_files(compare_projection_file, out_projection_file)

        tif_name = 'test_tif.tif'
        out_tif_file = path.join(self.writeDirectory, tif_name)
        grid.to_tif(out_tif_file)
        compare_tif_file = path.join(self.compare_path, tif_name)
        self._compare_files(out_tif_file, compare_tif_file, raster=True)

        tif_prj_name = 'test_tif_32651.tif'
        out_tif_file = path.join(self.writeDirectory, tif_prj_name)
        grid.to_tif(out_tif_file, out_epsg=32651)
        compare_tif_file = path.join(self.compare_path, tif_prj_name)
        self._compare_files(out_tif_file, compare_tif_file, raster=True)

        grass_name = 'test_grass_ascii.asc'
        out_grass_file = path.join(self.writeDirectory, grass_name)
        grid.to_grass_ascii(out_grass_file)
        compare_grass_file = path.join(self.compare_path, grass_name)
        self._compare_files(out_grass_file, compare_grass_file, raster=True)

        arc_name = 'test_arc_ascii.asc'
        out_arc_file = path.join(self.writeDirectory, arc_name)
        grid.to_grass_ascii(out_arc_file)
        compare_arc_file = path.join(self.compare_path, arc_name)
        self._compare_files(out_arc_file, compare_arc_file, raster=True)

if __name__ == '__main__':
    unittest.main()
