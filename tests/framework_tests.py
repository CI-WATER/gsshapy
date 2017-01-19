'''
********************************************************************************
* Name: Framework Tests
* Author: Alan D. Snow
* Created On: November 22, 2016
* License: BSD 3-Clause
********************************************************************************
'''
from datetime import datetime, timedelta
import os
import unittest 
from shutil import copytree, rmtree

from gridtogssha.framework import GSSHA_WRF_Framework
from RAPIDpy.helper_functions import compare_csv_timeseries_files

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

class Test_GSSHA_WRF_Framework(unittest.TestCase):
    def setUp(self):
        # Define workspace
        self.readDirectory = os.path.join(SCRIPT_DIR, 'grid_standard')
        self.writeDirectory = os.path.join(SCRIPT_DIR, 'out')

        #define global variables
        self.gssha_project_directory = os.path.join(self.writeDirectory, 'gssha_project')
        self.gssha_project_file = 'grid_standard.prj'
        
        self.os_name = os.name
        if os.name != 'nt':
            self.os_name = 'unix'
        
        #copy gssha project & HRRR data
        try:
            copytree(os.path.join(self.readDirectory, "gssha_project"),
                     self.gssha_project_directory)
        except OSError:
            pass

        #RAPID TO GSSHA
        self.path_to_rapid_qout = os.path.join(self.readDirectory, 'framework', 'Qout_nasa_lis_3hr_20020830.nc')
        self.connection_list_file = os.path.join(self.gssha_project_directory, 'rapid_to_gssha_connect.csv')

        #genereated files
        self.generated_igh_file = os.path.join(self.gssha_project_directory, 'grid_standard.ihg')

    def test_rapid_to_gssha(self):
        '''
        Test RAPID to GSSHA functionality
        '''
        
        #INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable='',
                                 gssha_directory=self.gssha_project_directory, 
                                 project_filename=self.gssha_project_file,
                                 path_to_rapid_qout=self.path_to_rapid_qout,
                                 connection_list_file=self.connection_list_file,                                    
                                )
        
        gr.run_forecast()
        
        #COMPARE FILES
        #grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_rapid_200208291800to200208311800_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_prj_file('output_200208291800to200208311800'), compare_prj_file)
        #grid_standard.ihg
        compare_igh_file = os.path.join(self.readDirectory, "framework", 
                                        "grid_standard_rapid_200208291800to200208311800.ihg")
        assert compare_csv_timeseries_files(self.generated_igh_file, compare_igh_file, header=False)
        #check folder exists
        assert os.path.exists(os.path.join(self.gssha_project_directory, "output_200208291800to200208311800"))

    def test_rapid_to_gssha_write_hotstart(self):
        '''
        Test RAPID to GSSHA functionality write hotstart
        '''
        #INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable='',
                                 gssha_directory=self.gssha_project_directory, 
                                 project_filename=self.gssha_project_file,
                                 path_to_rapid_qout=self.path_to_rapid_qout,
                                 connection_list_file=self.connection_list_file,
                                 write_hotstart=True,
                                )
        gr.run_forecast()
        
        #COMPARE FILES
        #grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_rapid_write_hotstart_200208291800to200208311800_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_prj_file('output_200208291800to200208311800'), compare_prj_file)
        #grid_standard.ihg
        compare_igh_file = os.path.join(self.readDirectory, "framework", 
                                        "grid_standard_rapid_200208291800to200208311800.ihg")
        assert compare_csv_timeseries_files(self.generated_igh_file, compare_igh_file, header=False)

        #check folders exist
        assert os.path.exists(os.path.join(self.gssha_project_directory, "output_200208291800to200208311800"))
        assert os.path.exists(os.path.join(self.gssha_project_directory, "hotstart"))

    def test_rapid_to_gssha_read_hotstart(self):
        '''
        Test RAPID to GSSHA functionality read hotstart
        '''
        #INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable='',
                                 gssha_directory=self.gssha_project_directory, 
                                 project_filename=self.gssha_project_file,
                                 path_to_rapid_qout=self.path_to_rapid_qout,
                                 connection_list_file=self.connection_list_file,
                                 read_hotstart=True,
                                )
        gr.run_forecast()
        
        #COMPARE FILES
        #grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_rapid_read_hotstart_200208291800to200208311800_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_prj_file('output_200208291800to200208311800'), compare_prj_file)
        #grid_standard.ihg
        compare_igh_file = os.path.join(self.readDirectory, "framework", 
                                        "grid_standard_rapid_200208291800to200208311800.ihg")
        assert compare_csv_timeseries_files(self.generated_igh_file, compare_igh_file, header=False)

        #check folders exist
        assert os.path.exists(os.path.join(self.gssha_project_directory, "output_200208291800to200208311800"))

    def test_rapid_to_gssha_date_range(self):
        '''
        Test RAPID to GSSHA functionality with date filters
        '''
        #INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable="",
                                 gssha_directory=self.gssha_project_directory, 
                                 project_filename=self.gssha_project_file,
                                 path_to_rapid_qout=self.path_to_rapid_qout,
                                 connection_list_file=self.connection_list_file,
                                 gssha_simulation_start=datetime(2002,8,30),
                                 gssha_simulation_end=datetime(2002,8,30,23,59),
                                 read_hotstart=True, #SHOULD NOT CHANGE ANYTHING
                                )
        
        gr.run_forecast()
        
        #COMPARE FILES
        #grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_rapid_200208300000to200208302359_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_prj_file('output_200208300000to200208302359'), compare_prj_file)
        #grid_standard.ihg
        compare_igh_file = os.path.join(self.readDirectory, "framework", 
                                        "grid_standard_rapid_200208300000to200208302359.ihg")
        assert compare_csv_timeseries_files(self.generated_igh_file, compare_igh_file, header=False)
        #check folder exists
        assert os.path.exists(os.path.join(self.gssha_project_directory, "output_200208300000to200208302359"))
 
    def test_rapid_to_gssha_date_range_hotstart(self):
        '''
        Test RAPID to GSSHA functionality with date filters
        '''
        #INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable="",
                                 gssha_directory=self.gssha_project_directory, 
                                 project_filename=self.gssha_project_file,
                                 path_to_rapid_qout=self.path_to_rapid_qout,
                                 connection_list_file=self.connection_list_file,
                                 gssha_simulation_start=datetime(2002,8,30),
                                 gssha_simulation_end=datetime(2002,8,30,23,59),
                                 read_hotstart=True,
                                 write_hotstart=True,
                                )
        
        gr.run_forecast()
        
        #COMPARE FILES
        #grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_rapid_hotstart_200208300000to200208302359_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_prj_file('output_200208300000to200208302359'), compare_prj_file)
        #grid_standard.ihg
        compare_igh_file = os.path.join(self.readDirectory, "framework", 
                                        "grid_standard_rapid_200208300000to200208302359.ihg")
        assert compare_csv_timeseries_files(self.generated_igh_file, compare_igh_file, header=False)

        #check folder exists
        assert os.path.exists(os.path.join(self.gssha_project_directory, "output_200208300000to200208302359"))
        assert os.path.exists(os.path.join(self.gssha_project_directory, "hotstart"))
 
    def test_rapid_to_gssha_min_hotstart(self):
        '''
        Test RAPID to GSSHA functionality with minmal mode hotstart generation
        '''
        #INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable="",
                                 gssha_directory=self.gssha_project_directory, 
                                 project_filename=self.gssha_project_file,
                                 path_to_rapid_qout=self.path_to_rapid_qout,
                                 connection_list_file=self.connection_list_file,
                                 gssha_simulation_duration=timedelta(seconds=6*3600),
                                 write_hotstart=True,
                                 hotstart_minimal_mode=True,
                                )
        gr.run_forecast()
        
        #COMPARE FILES
        #grid_standard.prj
        generated_prj_file = os.path.join(self.gssha_project_directory,'grid_standard_minimal_hotstart.prj')
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_minimal_hotstart_rapid_200208291800to2002083000_{0}.prj'.format(self.os_name))
        self._compare_files(generated_prj_file, compare_prj_file)
        #grid_standard.ihg
        generated_igh_file = os.path.join(self.gssha_project_directory, "grid_standard_hotstart.ihg")
        compare_igh_file = os.path.join(self.readDirectory, "framework", 
                                        "grid_standard_hotstart_rapid_200208291800to2002083000.ihg")
        assert compare_csv_timeseries_files(generated_igh_file, compare_igh_file, header=False)
        
        #check folder exists
        assert os.path.exists(os.path.join(self.gssha_project_directory, "hotstart"))

    def test_wrf_to_gssha(self):
        '''
        Test WRF to GSSHA functionality
        '''
        #TODO
        return
 
    def _generated_prj_file(self, output_directory=""):
        """
        Returns path to generated prj file
        """
        return os.path.join(self.gssha_project_directory, output_directory, 'grid_standard.prj')
 

    def _compare_files(self, original, new):
        '''
        Compare the contents of two files
        '''
        with open(original) as fileO:
            contentsO = fileO.read()
            linesO = contentsO.strip().split()
            
        with open(new) as fileN:
            contentsN = fileN.read()
            linesN = contentsN.strip().split()
            
        self.assertEqual(linesO, linesN)

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

if __name__ == '__main__':
    unittest.main()
