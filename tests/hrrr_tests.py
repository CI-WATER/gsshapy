'''
********************************************************************************
* Name: HRRR Tests
* Author: Alan D. Snow
* Created On: September 16, 2016
* License: BSD 3-Clause
********************************************************************************
'''
from netCDF4 import Dataset
from numpy.testing import assert_almost_equal
import unittest, itertools, os
from shutil import copytree, rmtree

from gridtogssha import HRRRtoGSSHA
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

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

class TestHRRRtoGSSHA(unittest.TestCase):
    def setUp(self):
        # Define workspace
        self.readDirectory = os.path.join(SCRIPT_DIR, 'grid_standard')
        self.writeDirectory = os.path.join(SCRIPT_DIR, 'out')

        #define global variables
        self.hmet_read_directory = os.path.join(self.readDirectory, "hrrr_hmet_data")
        self.hmet_write_directory = os.path.join(self.writeDirectory, "hrrr_hmet_data")
        self.gssha_project_folder = os.path.join(self.writeDirectory, "gssha_project")
        self.gssha_grid_name = 'grid_standard.ele'
        self.hrrr_folder = os.path.join(self.writeDirectory,'hrrr_raw_data','20160914')
        self.search_card = "hrrr.t01z.wrfsfcf*.grib2"

        #create folder to dump output HMET into
        try:
            os.mkdir(self.hmet_write_directory)
        except OSError:
            pass

        
        #copy gssha project & HRRR data
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
                                   ['precipitation_rate', 'prate'], 
                                   ['pressure', 'sp'], 
                                   ['relative_humidity', '2r'], 
                                   ['wind_speed', ['10u', '10v']], 
                                   ['direct_radiation_cc', ['dswrf', 'tcc']],
                                   ['diffusive_radiation_cc', ['dswrf', 'tcc']],
                                   ['temperature', 't'],
                                   ['cloud_cover_pc' , 'tcc'],
                                  ]
        
    def test_hrrr_gage_file_write(self):
        '''
        Test HRRR lsm_precip_to_gssha_precip_gage write method
        '''
        os.chdir(self.gssha_project_folder)
        h2g = HRRRtoGSSHA(gssha_project_folder=self.gssha_project_folder,
                          gssha_grid_file_name=self.gssha_grid_name,
                          lsm_input_folder_path=self.hrrr_folder,
                          lsm_search_card=self.search_card, 
                          )
        
        out_gage_file = os.path.join(self.writeDirectory, 'gage_test_hrrr.gag')
        h2g.lsm_precip_to_gssha_precip_gage(out_gage_file,
                                            lsm_data_var='prate',
                                            precip_type='RADAR')

        # Test
        self._compare_files('gage_test_hrrr', 'gage_test_hrrr', 'gag')

    def test_hrrr_netcdf_file_write(self):
        '''
        Test HRRR lsm_data_to_subset_netcdf write method
        '''
        os.chdir(self.gssha_project_folder)
        h2g = HRRRtoGSSHA(gssha_project_folder=self.gssha_project_folder,
                          gssha_grid_file_name=self.gssha_grid_name,
                          lsm_input_folder_path=self.hrrr_folder,
                          lsm_search_card=self.search_card, 
                          )
        
        netcdf_file_path = os.path.join(self.writeDirectory, 'gssha_dynamic_hrrr.nc')
        h2g.lsm_data_to_subset_netcdf(netcdf_file_path, self.data_var_map_array)        

        #compare netcdf files
        self._compare_netcdf_files("gssha_dynamic_hrrr", "gssha_dynamic_hrrr", "nc")

    def test_hrrr_ascii_file_write(self):
        '''
        Test HRRR lsm_data_to_arc_ascii write method
        '''
        os.chdir(self.gssha_project_folder)
        h2g = HRRRtoGSSHA(gssha_project_folder=self.gssha_project_folder,
                          gssha_grid_file_name=self.gssha_grid_name,
                          lsm_input_folder_path=self.hrrr_folder,
                          lsm_search_card=self.search_card, 
                          )
        
        h2g.lsm_data_to_arc_ascii(self.data_var_map_array, self.hmet_write_directory)
        
        # Compare all files
        self._compare_directories("hrrr_hmet_data",
                                  "hrrr_hmet_data",
                                  ignore_file="hmet_file_list.txt")

    def _compare_netcdf_files(self, original, new, ext):
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
        self.assertEqual(dO.getncattr("cell_size"),dN.getncattr("cell_size")) 
        
        dO.close()
        dN.close()


    def _compare_files(self, original, new, ext):
        '''
        Compare the contents of two files
        '''
        filenameO = '%s.%s' % (original, ext)
        filePathO = os.path.join(self.readDirectory, filenameO)
        filenameN = '%s.%s' % (new, ext)
        filePathN = os.path.join(self.writeDirectory, filenameN)
        
        with open(filePathO) as fileO:
            contentsO = fileO.read()
            linesO = contentsO.strip().split()
            
        with open(filePathN) as fileN:
            contentsN = fileN.read()
            linesN = contentsN.strip().split()
            
        self.assertEqual(linesO, linesN)
        
    def _compare_directories(self, dir1, dir2, ignore_file=None):
        '''
        Compare the contents of the files of two directories
        '''
        fileList2 = os.listdir(os.path.join(self.readDirectory, dir2))
        
        for afile in fileList2:
            if not os.path.basename(afile).startswith(".")\
               and not afile==ignore_file:
                name = afile.split('.')[0]
                ext = afile.split('.')[1]
                
                # Compare files with same name
                self._compare_files(os.path.join(dir1, name),
                                    os.path.join(dir2, name),
                                    ext)
            
    def _list_compare(self, listone, listtwo):
        for one, two in itertools.izip(listone, listtwo):
            self.assertEqual(one, two)

#    def tearDown(self):
#        os.chdir(SCRIPT_DIR)
#
#        # Clear out directory
#        fileList = os.listdir(self.writeDirectory)
#        
#        for afile in fileList:
#            if afile != '.gitignote':
#                path = os.path.join(self.writeDirectory, afile)
#                if os.path.isdir(path):
#                    rmtree(path)
#                else:
#                    os.remove(path)

suite = unittest.TestLoader().loadTestsFromTestCase(TestHRRRtoGSSHA)
    

if __name__ == '__main__':
    unittest.main()
