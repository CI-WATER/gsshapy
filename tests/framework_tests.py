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
from shutil import copytree

from template import TestGridTemplate
from gridtogssha.framework import GSSHA_WRF_Framework
from RAPIDpy.helper_functions import compare_csv_timeseries_files

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))


class Test_GSSHA_WRF_Framework(TestGridTemplate):
    def setUp(self):
        # define global variables
        self.gssha_project_directory = os.path.join(self.writeDirectory,
                                                    'gssha_project')
        self.gssha_project_file = 'grid_standard.prj'

        self.os_name = os.name
        if os.name != 'nt':
            self.os_name = 'unix'

        # copy gssha project & WRF data
        try:
            copytree(os.path.join(self.readDirectory, "gssha_project"),
                     self.gssha_project_directory)
        except OSError:
            pass

        try:
            copytree(os.path.join(self.readDirectory, "wrf_raw_data", "gssha_d03_nc"),
                     os.path.join(self.writeDirectory, "wrf_raw_data"))
        except OSError:
            pass

        # RAPID TO GSSHA
        self.path_to_rapid_qout = os.path.join(self.readDirectory, 'framework',
                                               'Qout_nasa_lis_3hr_20020830.nc')
        self.connection_list_file = os.path.join(self.gssha_project_directory,
                                                 'rapid_to_gssha_connect.csv')

        # LSM TO GSSHA
        self.lsm_folder = os.path.join(self.writeDirectory, 'wrf_raw_data')
        self.lsm_file_date_naming_convention = 'gssha_d03_%Y_%m_%d_%H_%M_%S.nc'

# -----------------------------------------------------------------------------
# RAPID ONLY SECTION
# -----------------------------------------------------------------------------

    def test_rapid_to_gssha(self):
        '''
        Test RAPID to GSSHA functionality
        '''

        # INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable='',
                                 gssha_directory=self.gssha_project_directory,
                                 project_filename=self.gssha_project_file,
                                 path_to_rapid_qout=self.path_to_rapid_qout,
                                 connection_list_file=self.connection_list_file
                                 )

        gr.run_forecast()

        # COMPARE FILES
        # grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_rapid_200208291800to200208311800_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_file_path('run_200208291800to200208311800'), compare_prj_file)
        # grid_standard.ihg
        compare_igh_file = os.path.join(self.readDirectory, "framework",
                                        "grid_standard_rapid_200208291800to200208311800.ihg")
        assert compare_csv_timeseries_files(self._generated_file_path('run_200208291800to200208311800', extension='ihg'),
                                            compare_igh_file,
                                            header=False)
        # grid_standard.cmt
        # 1 file in main directory not modified
        self._compare_files(os.path.join(self.readDirectory, "gssha_project", "grid_standard.cmt"),
                            os.path.join(self.gssha_project_directory, "grid_standard.cmt"))
        # 2 file in working directory exists
        assert os.path.exists(self._generated_file_path('run_200208291800to200208311800', extension="cmt"))
        # 3 TODO: Check to make sure generated correctly

    def test_rapid_to_gssha_write_hotstart(self):
        '''
        Test RAPID to GSSHA functionality write hotstart
        '''
        # INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable='',
                                 gssha_directory=self.gssha_project_directory,
                                 project_filename=self.gssha_project_file,
                                 path_to_rapid_qout=self.path_to_rapid_qout,
                                 connection_list_file=self.connection_list_file,
                                 write_hotstart=True,
                                 )
        gr.run_forecast()

        # check folders exist
        assert os.path.exists(os.path.join(self.gssha_project_directory, "hotstart"))

        # COMPARE FILES
        # grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_rapid_write_hotstart_200208291800to200208311800_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_file_path('run_200208291800to200208311800'), compare_prj_file)
        # grid_standard.ihg
        compare_igh_file = os.path.join(self.readDirectory, "framework",
                                        "grid_standard_rapid_200208291800to200208311800.ihg")
        assert compare_csv_timeseries_files(self._generated_file_path('run_200208291800to200208311800', extension='ihg'),
                                            compare_igh_file, header=False)

        # grid_standard.cmt
        # 1 file in main directory not modified
        self._compare_files(os.path.join(self.readDirectory, "gssha_project", "grid_standard.cmt"),
                            os.path.join(self.gssha_project_directory, "grid_standard.cmt"))
        # 2 file in working directory exists
        assert os.path.exists(self._generated_file_path('run_200208291800to200208311800', extension="cmt"))
        # 3 TODO: Check to make sure generated correctly

    def test_rapid_to_gssha_read_hotstart(self):
        '''
        Test RAPID to GSSHA functionality read hotstart
        '''
        # INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable='',
                                 gssha_directory=self.gssha_project_directory,
                                 project_filename=self.gssha_project_file,
                                 path_to_rapid_qout=self.path_to_rapid_qout,
                                 connection_list_file=self.connection_list_file,
                                 read_hotstart=True,
                                 )
        gr.run_forecast()

        # COMPARE FILES
        # grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_rapid_read_hotstart_200208291800to200208311800_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_file_path('run_200208291800to200208311800'), compare_prj_file)
        # grid_standard.ihg
        compare_igh_file = os.path.join(self.readDirectory, "framework",
                                        "grid_standard_rapid_200208291800to200208311800.ihg")
        assert compare_csv_timeseries_files(self._generated_file_path('run_200208291800to200208311800', extension='ihg'),
                                            compare_igh_file, header=False)

        # grid_standard.cmt
        # 1 file in main directory not modified
        self._compare_files(os.path.join(self.readDirectory, "gssha_project", "grid_standard.cmt"),
                            os.path.join(self.gssha_project_directory, "grid_standard.cmt"))
        # 2 file in working directory exists
        assert os.path.exists(self._generated_file_path('run_200208291800to200208311800', extension="cmt"))
        # 3 TODO: Check to make sure generated correctly

    def test_rapid_to_gssha_date_range(self):
        '''
        Test RAPID to GSSHA functionality with date filters
        '''
        # INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable="",
                                 gssha_directory=self.gssha_project_directory,
                                 project_filename=self.gssha_project_file,
                                 path_to_rapid_qout=self.path_to_rapid_qout,
                                 connection_list_file=self.connection_list_file,
                                 gssha_simulation_start=datetime(2002,8,30),
                                 gssha_simulation_end=datetime(2002,8,30,23,59),
                                 read_hotstart=True,  # SHOULD NOT CHANGE ANYTHING
                                 )

        gr.run_forecast()

        # COMPARE FILES
        # grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_rapid_200208300000to200208302359_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_file_path('run_200208300000to200208302359'), compare_prj_file)
        # grid_standard.ihg
        compare_igh_file = os.path.join(self.readDirectory, "framework",
                                        "grid_standard_rapid_200208300000to200208302359.ihg")
        assert compare_csv_timeseries_files(self._generated_file_path('run_200208300000to200208302359', extension='ihg'),
                                            compare_igh_file, header=False)
        # grid_standard.cmt
        # 1 file in main directory not modified
        self._compare_files(os.path.join(self.readDirectory, "gssha_project", "grid_standard.cmt"),
                            os.path.join(self.gssha_project_directory, "grid_standard.cmt"))
        # 2 file in working directory exists
        assert os.path.exists(self._generated_file_path('run_200208300000to200208302359', extension="cmt"))
        # 3 TODO: Check to make sure generated correctly

    def test_rapid_to_gssha_date_range_hotstart(self):
        '''
        Test RAPID to GSSHA functionality with date filters
        '''
        # INITIALIZE CLASS AND RUN
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

        # check folder exists
        assert os.path.exists(os.path.join(self.gssha_project_directory, "hotstart"))

        # COMPARE FILES
        # grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_rapid_hotstart_200208300000to200208302359_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_file_path('run_200208300000to200208302359'), compare_prj_file)
        # grid_standard.ihg
        compare_igh_file = os.path.join(self.readDirectory, "framework",
                                        "grid_standard_rapid_200208300000to200208302359.ihg")
        assert compare_csv_timeseries_files(self._generated_file_path('run_200208300000to200208302359', extension='ihg'),
                                            compare_igh_file, header=False)

        # grid_standard.cmt
        # 1 file in main directory not modified
        self._compare_files(os.path.join(self.readDirectory, "gssha_project", "grid_standard.cmt"),
                            os.path.join(self.gssha_project_directory, "grid_standard.cmt"))
        # 2 file in working directory exists
        assert os.path.exists(self._generated_file_path('run_200208300000to200208302359', extension="cmt"))
        # 3 TODO: Check to make sure generated correctly

    def test_rapid_to_gssha_min_hotstart(self):
        '''
        Test RAPID to GSSHA functionality with minmal mode hotstart generation
        '''
        # INITIALIZE CLASS AND RUN
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

        # check folder exists
        assert os.path.exists(os.path.join(self.gssha_project_directory, "hotstart"))

        # COMPARE FILES
        # grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_rapid_minimal_hotstart_200208291800to200208300000_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_file_path('minimal_hotstart_run_200208291800to200208300000'), compare_prj_file)
        # grid_standard.ihg
        compare_igh_file = os.path.join(self.readDirectory, "framework",
                                        "grid_standard_rapid_hotstart_200208291800to2002083000.ihg")
        assert compare_csv_timeseries_files(self._generated_file_path('minimal_hotstart_run_200208291800to200208300000', extension='ihg'),
                                            compare_igh_file, header=False)

        # grid_standard.cmt
        # 1 file in main directory not modified
        self._compare_files(os.path.join(self.readDirectory, "gssha_project", "grid_standard.cmt"),
                            os.path.join(self.gssha_project_directory, "grid_standard.cmt"))
        # 2 file in working directory exists
        assert os.path.exists(self._generated_file_path('minimal_hotstart_run_200208291800to200208300000', extension="cmt"))
        # 3 TODO: Check to make sure generated correctly

# -----------------------------------------------------------------------------
# WRF ONLY SECTION
# -----------------------------------------------------------------------------

    def test_wrf_to_gssha(self):
        '''
        Test WRF to GSSHA functionality
        '''
        # INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable='',
                                 gssha_directory=self.gssha_project_directory,
                                 project_filename=self.gssha_project_file,
                                 lsm_folder=self.lsm_folder,
                                 lsm_file_date_naming_convention=self.lsm_file_date_naming_convention,
                                 )

        gr.run_forecast()

        # COMPARE FILES
        # grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_wrf_201608231600to201608240700_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_file_path('run_201608231600to201608240700'), compare_prj_file)

        # grid_standard.cmt
        # 1 file in main directory not modified
        self._compare_files(os.path.join(self.readDirectory, "gssha_project", "grid_standard.cmt"),
                            os.path.join(self.gssha_project_directory, "grid_standard.cmt"))
        # 2 file in working directory exists
        assert os.path.exists(self._generated_file_path('run_201608231600to201608240700', extension="cmt"))
        # 3 TODO: Check to make sure generated correctly

        # grid_standard.gag
        self._compare_files(os.path.join(self.readDirectory, "framework", "grid_standard_wrf_201608231600to201608240700.gag"),
                            self._generated_file_path('run_201608231600to201608240700', extension="gag"))

        # compare HMET files
        compare_directory = os.path.join(self.readDirectory,
                                         "framework",
                                         "wrf_hmet_data_201608231600to201608240700")
        output_directory = os.path.join(self.gssha_project_directory,
                                        "hmet_data_201608231600to201608240700")

        self._compare_directories(output_directory,
                                  compare_directory,
                                  ignore_file="hmet_file_list.txt",
                                  raster=True)


    def test_wrf_to_gssha_write_hotstart(self):
        '''
        Test WRF to GSSHA functionality write hotstart
        '''
        # INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable='',
                                 gssha_directory=self.gssha_project_directory,
                                 project_filename=self.gssha_project_file,
                                 lsm_folder=self.lsm_folder,
                                 lsm_file_date_naming_convention=self.lsm_file_date_naming_convention,
                                 write_hotstart=True,
                                 )

        gr.run_forecast()

        # COMPARE FILES
        # grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_wrf_write_hotstart_201608231600to201608240700_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_file_path('run_201608231600to201608240700'), compare_prj_file)

        # grid_standard.cmt
        # 1 file in main directory not modified
        self._compare_files(os.path.join(self.readDirectory, "gssha_project", "grid_standard.cmt"),
                            os.path.join(self.gssha_project_directory, "grid_standard.cmt"))
        # 2 file in working directory exists
        assert os.path.exists(self._generated_file_path('run_201608231600to201608240700', extension="cmt"))
        # 3 TODO: Check to make sure generated correctly

        # grid_standard.gag
        self._compare_files(os.path.join(self.readDirectory, "framework", "grid_standard_wrf_201608231600to201608240700.gag"),
                            self._generated_file_path('run_201608231600to201608240700', extension="gag"))

        # compare HMET files
        compare_directory = os.path.join(self.readDirectory,
                                         "framework",
                                         "wrf_hmet_data_201608231600to201608240700")
        output_directory = os.path.join(self.gssha_project_directory,
                                        "hmet_data_201608231600to201608240700")

        self._compare_directories(output_directory,
                                  compare_directory,
                                  ignore_file="hmet_file_list.txt",
                                  raster=True)

    def test_wrf_to_gssha_read_hotstart(self):
        '''
        Test WRF to GSSHA functionality read hotstart
        '''
        # INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable='',
                                 gssha_directory=self.gssha_project_directory,
                                 project_filename=self.gssha_project_file,
                                 lsm_folder=self.lsm_folder,
                                 lsm_file_date_naming_convention=self.lsm_file_date_naming_convention,
                                 read_hotstart=True,
                                 )

        gr.run_forecast()

        # COMPARE FILES
        # grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_wrf_read_hotstart_201608231600to201608240700_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_file_path('run_201608231600to201608240700'), compare_prj_file)

        # grid_standard.cmt
        # 1 file in main directory not modified
        self._compare_files(os.path.join(self.readDirectory, "gssha_project", "grid_standard.cmt"),
                            os.path.join(self.gssha_project_directory, "grid_standard.cmt"))
        # 2 file in working directory exists
        assert os.path.exists(self._generated_file_path('run_201608231600to201608240700', extension="cmt"))
        # 3 TODO: Check to make sure generated correctly

        # grid_standard.gag
        self._compare_files(os.path.join(self.readDirectory, "framework", "grid_standard_wrf_201608231600to201608240700.gag"),
                            self._generated_file_path('run_201608231600to201608240700', extension="gag"))

        # compare HMET files
        compare_directory = os.path.join(self.readDirectory,
                                         "framework",
                                         "wrf_hmet_data_201608231600to201608240700")
        output_directory = os.path.join(self.gssha_project_directory,
                                        "hmet_data_201608231600to201608240700")

        self._compare_directories(output_directory,
                                  compare_directory,
                                  ignore_file="hmet_file_list.txt",
                                  raster=True)

    def test_wrf_to_gssha_date_range(self):
        '''
        Test WRF to GSSHA functionality with date filters
        '''
        # INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable='',
                                 gssha_directory=self.gssha_project_directory,
                                 project_filename=self.gssha_project_file,
                                 lsm_folder=self.lsm_folder,
                                 lsm_file_date_naming_convention=self.lsm_file_date_naming_convention,
                                 gssha_simulation_start=datetime(2016, 8, 23),
                                 gssha_simulation_end=datetime(2002, 8, 24, 3, 59),
                                 read_hotstart=True,
                                 write_hotstart=True,
                                 )

        gr.run_forecast()

        # COMPARE FILES
        # grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_wrf_hotstart_201608230000to200208240359_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_file_path('run_201608230000to200208240359'), compare_prj_file)

        # grid_standard.cmt
        # 1 file in main directory not modified
        self._compare_files(os.path.join(self.readDirectory, "gssha_project", "grid_standard.cmt"),
                            os.path.join(self.gssha_project_directory, "grid_standard.cmt"))
        # 2 file in working directory exists
        assert os.path.exists(self._generated_file_path('run_201608230000to200208240359', extension="cmt"))
        # 3 TODO: Check to make sure generated correctly

        # grid_standard.gag
        self._compare_files(os.path.join(self.readDirectory, "framework", "grid_standard_wrf_201608230000to200208240359.gag"),
                            self._generated_file_path('run_201608230000to200208240359', extension="gag"))

        # compare HMET files
        compare_directory = os.path.join(self.readDirectory,
                                         "framework",
                                         "wrf_hmet_data_201608231600to201608240700")
        output_directory = os.path.join(self.gssha_project_directory,
                                        "hmet_data_201608230000to200208240359")

        self._compare_directories(compare_directory,
                                  output_directory,
                                  ignore_file="hmet_file_list.txt",
                                  raster=True)


    def test_wrf_to_gssha_min_hotstart(self):
        '''
        Test WRF to GSSHA functionality with minmal mode hotstart generation
        '''
        # INITIALIZE CLASS AND RUN
        gr = GSSHA_WRF_Framework(gssha_executable='',
                                 gssha_directory=self.gssha_project_directory,
                                 project_filename=self.gssha_project_file,
                                 lsm_folder=self.lsm_folder,
                                 lsm_file_date_naming_convention=self.lsm_file_date_naming_convention,
                                 gssha_simulation_duration=timedelta(seconds=6*3600),
                                 read_hotstart=True,
                                 write_hotstart=True,
                                 hotstart_minimal_mode=True,
                                 )

        gr.run_forecast()

        # COMPARE FILES
        # grid_standard.prj
        compare_prj_file = os.path.join(self.readDirectory, 'framework',
                                        'grid_standard_wrf_minimal_hotstart_201608231600to201608232200_{0}.prj'.format(self.os_name))
        self._compare_files(self._generated_file_path('minimal_hotstart_run_201608231600to201608232200'), compare_prj_file)

        # grid_standard.cmt
        # 1 file in main directory not modified
        self._compare_files(os.path.join(self.readDirectory, "gssha_project", "grid_standard.cmt"),
                            os.path.join(self.gssha_project_directory, "grid_standard.cmt"))
        # 2 file in working directory exists
        assert os.path.exists(self._generated_file_path('minimal_hotstart_run_201608231600to201608232200', extension="cmt"))
        # 3 TODO: Check to make sure generated correctly

        # grid_standard.gag
        self._compare_files(os.path.join(self.readDirectory, "framework", "grid_standard_wrf_201608231600to201608232200.gag"),
                            self._generated_file_path('minimal_hotstart_run_201608231600to201608232200', extension="gag"))

        # compare HMET files
        compare_directory = os.path.join(self.readDirectory,
                                         "framework",
                                         "wrf_hmet_data_201608231600to201608240700")
        output_directory = os.path.join(self.gssha_project_directory,
                                        "hmet_data_201608231600to201608232200_hotstart")

        self._compare_directories(compare_directory,
                                  output_directory,
                                  ignore_file="hmet_file_list.txt",
                                  raster=True)

    def _generated_file_path(self, output_directory="", extension="prj"):
        '''
        Returns path to generated file
        '''
        return os.path.join(self.gssha_project_directory,
                            output_directory,
                            'grid_standard.{0}'.format(extension))


if __name__ == '__main__':
    unittest.main()
