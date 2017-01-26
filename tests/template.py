'''
********************************************************************************
* Name: Test Grid Template
* Author: Alan D. Snow
* Created On: September 16, 2016
* License: BSD 3-Clause
********************************************************************************
'''
import itertools
from netCDF4 import Dataset
from numpy import array
from numpy.testing import assert_almost_equal
import os
from osgeo import gdal
from shutil import rmtree
import unittest

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))


class TestGridTemplate(unittest.TestCase):
    # Define workspace
    readDirectory = os.path.join(SCRIPT_DIR, 'grid_standard')
    writeDirectory = os.path.join(SCRIPT_DIR, 'out')

    def _compare_netcdf_files(self, original, new, ext="nc"):
        '''
        Compare the contents of two netcdf files
        '''
        filenameO = '%s.%s' % (original, ext)
        filePathO = os.path.join(self.readDirectory, filenameO)
        filenameN = '%s.%s' % (new, ext)
        filePathN = os.path.join(self.writeDirectory, filenameN)

        dO = Dataset(filePathO)
        dN = Dataset(filePathN)

        assert_almost_equal(dO.variables['time'][:], dN.variables['time'][:], decimal=5)
        assert_almost_equal(dO.variables['lon'][:], dN.variables['lon'][:], decimal=5)
        assert_almost_equal(dO.variables['lat'][:], dN.variables['lat'][:], decimal=5)
        assert_almost_equal(dO.variables['precipitation'][:], dN.variables['precipitation'][:], decimal=5)
        assert_almost_equal(dO.variables['pressure'][:], dN.variables['pressure'][:], decimal=5)
        assert_almost_equal(dO.variables['relative_humidity'][:], dN.variables['relative_humidity'][:], decimal=5)
        assert_almost_equal(dO.variables['wind_speed'][:], dN.variables['wind_speed'][:], decimal=5)
        assert_almost_equal(dO.variables['direct_radiation'][:], dN.variables['direct_radiation'][:], decimal=5)
        assert_almost_equal(dO.variables['diffusive_radiation'][:], dN.variables['diffusive_radiation'][:], decimal=5)
        assert_almost_equal(dO.variables['temperature'][:], dN.variables['temperature'][:], decimal=5)
        assert_almost_equal(dO.variables['cloud_cover'][:], dN.variables['cloud_cover'][:], decimal=5)

        self.assertEqual(dO.getncattr("north"),dN.getncattr("north"))
        self.assertEqual(dO.getncattr("south"),dN.getncattr("south"))
        self.assertEqual(dO.getncattr("east"),dN.getncattr("east"))
        self.assertEqual(dO.getncattr("west"),dN.getncattr("west"))
        assert_almost_equal(dO.getncattr("cell_size"), dN.getncattr("cell_size"), decimal=9)

        dO.close()
        dN.close()

    def _compare_files(self, original, new, raster=False):
        '''
        Compare the contents of two files
        '''
        if raster:
            dsO = gdal.Open(original)
            dsN = gdal.Open(new)

            # compare data
            rO = array(dsO.ReadAsArray())
            rN = array(dsN.ReadAsArray())
            assert_almost_equal(rO, rN)

            # compare geotransform
            assert dsO.GetGeoTransform() == dsN.GetGeoTransform()
        else:
            with open(original) as fileO:
                contentsO = fileO.read()
                linesO = contentsO.strip().split()

            with open(new) as fileN:
                contentsN = fileN.read()
                linesN = contentsN.strip().split()
            self.assertEqual(linesO, linesN)

    def _compare_directories(self, dir1, dir2, ignore_file=None, raster=False):
        '''
        Compare the contents of the files of two directories
        '''

        for afile in os.listdir(dir2):
            if not os.path.basename(afile).startswith(".")\
               and not afile == ignore_file:

                # Compare files with same name
                try:
                    self._compare_files(os.path.join(dir1, afile),
                                        os.path.join(dir2, afile),
                                        raster=raster)
                except AssertionError:
                    print(os.path.join(dir1, afile))
                    print(os.path.join(dir2, afile))
                    raise
                    
    def _list_compare(self, listone, listtwo):
        for one, two in itertools.izip(listone, listtwo):
            self.assertEqual(one, two)

    def tearDown(self):
        os.chdir(SCRIPT_DIR)

        # Clear out directory
        fileList = os.listdir(self.writeDirectory)

        for afile in fileList:
            if afile != '.gitignote':
                path = os.path.join(self.writeDirectory, afile)
                if os.path.isdir(path):
                    rmtree(path)
                else:
                    os.remove(path)
