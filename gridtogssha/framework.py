# -*- coding: utf-8 -*-
##
##  framework.py
##  GSSHApy
##
##  Created by Alan D Snow, 2016.
##  BSD 3-Clause

from glob import glob
from datetime import datetime #TODO: Add date filter for GSSHA
from numpy import mean
import os
from osgeo import gdal, osr
from pyproj import Proj, transform
from pytz import timezone, utc
from RAPIDpy import RAPIDDataset
from spt_dataset_manager import ECMWFRAPIDDatasetManager
from subprocess import Popen, PIPE
from timezonefinder import TimezoneFinder

from gridtogssha import LSMtoGSSHA
from gsshapy.lib import db_tools as dbt
from gsshapy.orm import ProjectCard, ProjectFile

class GSSHAFramework(object):
    """
    This class is for automating the connection between RAPID to GSSHA and LSM to GSSHA.
    There are several different configurations depending upon what you choose.
    
    There are three options for RAPID to GSSHA:
    
    1. Download and run using forecast from the Streamflow Prediction Tool (See: https://streamflow-prediction-tool.readthedocs.io)
    2. Run from RAPID Qout file
    3. Don't run using RAPID to GSSHA
    
    There are two options for LSM to GSSHA:
    
    1. Run from LSM to GSSHA
    2. Don't run using LSM to GSSHA
    
    
    Parameters:
        gssha_executable(str): Path to GSSHA executable. 
        gssha_directory(str): Path to directory for GSSHA project.
        project_filename(str): Name of GSSHA project file.
        gssha_simulation_start(Optional[datetime]): Datetime object with date of start of GSSHA simulation.
        gssha_simulation_end(Optional[datetime]): Datetime object with date of end of GSSHA simulation.
        spt_watershed_name(Optional[str]): Streamflow Prediction Tool watershed name.
        spt_subbasin_name(Optional[str]): Streamflow Prediction Tool subbasin name.
        spt_forecast_date_string(Optional[str]): Streamflow Prediction Tool forecast date string.
        ckan_engine_url(Optional[str]): CKAN engine API url.
        ckan_api_key(Optional[str]): CKAN api key.
        ckan_owner_organization(Optional[str]): CKAN owner organization.
        path_to_rapid_qout(Optional[str]): Path to the RAPID Qout file. Use this if you do NOT want to download the forecast and you want to use RAPID streamflows.
        connection_list_file(Optional[str]): CSV file with list connecting GSSHA rivers to RAPID river network. See: http://rapidpy.readthedocs.io/en/latest/rapid_to_gssha.html
        lsm_folder(Optional[str]): Path to folder with land surface model data. See: *lsm_input_folder_path* variable at :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA`.
        lsm_data_var_map_array(Optional[str]): Array with connections for LSM output and GSSHA input. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.`
        lsm_precip_data_var(Optional[list or str]): String of name for precipitation variable name or list of precip variable names.  See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
        lsm_precip_type(Optional[str]): Type of precipitation. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
        lsm_lat_var(Optional[str]): Name of the latitude variable in the LSM netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
        lsm_lon_var(Optional[str]): Name of the longitude variable in the LSM netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
        lsm_file_date_naming_convention(Optional[str]): Array with connections for LSM output and GSSHA input. See: :func:`~gridtogssha.LSMtoGSSHA`.
        lsm_time_var(Optional[str]): Name of the time variable in the LSM netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
        lsm_search_card(Optional[str]): Glob search pattern for LSM files. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA`.
        precip_interpolation_type(Optional[str]): Type of interpolation for LSM precipitation. Can be "INV_DISTANCE" or "THIESSEN". Default is "THIESSEN".
        output_netcdf(Optional[bool]): If you want the HMET data output as a NetCDF4 file for input to GSSHA. Default is False.

    Example modifying parameters during class initialization:
    
    .. code:: python
        
            from gridtogssha.framework import GSSHAFramework

            gssha_executable = 'C:/Program Files/WMS 10.1 64-bit/gssha/gssha.exe'
            gssha_directory = "C:/Users/{username}/Documents/GSSHA"
            project_filename = "gssha_project.prj"
            connection_list_file = "C:/Users/{username}/Documents/GSSHA/rapid_to_gssha_connect.csv"
            
            #WRF INPUTS
            lsm_folder = '"C:/Users/{username}/Documents/GSSHA/wrf-sample-data-v1.0'
            lsm_lat_var = 'XLAT'
            lsm_lon_var = 'XLONG'
            search_card = '*.nc'
            precip_data_var = ['RAINC', 'RAINNC']
            precip_type = 'ACCUM'
            lsm_file_date_naming_convention='gssha_d02_%Y_%m_%d_%H_%M_%S.nc'
            
            data_var_map_array = [
                                  ['precipitation_acc', ['RAINC', 'RAINNC']], 
                                  ['pressure', 'PSFC'], 
                                  ['relative_humidity', ['Q2', 'PSFC', 'T2']], 
                                  ['wind_speed', ['U10', 'V10']], 
                                  ['direct_radiation', ['SWDOWN', 'DIFFUSE_FRAC']],
                                  ['diffusive_radiation', ['SWDOWN', 'DIFFUSE_FRAC']],
                                  ['temperature', 'T2'],
                                  ['cloud_cover' , 'CLDFRA'],
                                 ]
            
            #INITIALIZE CLASS AND RUN
            gr = GSSHAFramework(gssha_executable,
                                gssha_directory, 
                                project_filename,
                                ckan_engine_url='http://ckan/api/3/action',
                                ckan_api_key='your-api-key',
                                ckan_owner_organization='your_organization',
                                spt_watershed_name='watershed_name',
                                spt_subbasin_name='subbasin_name',
                                spt_forecast_date_string='20160721.1200'
                                lsm_folder=lsm_folder,
                                lsm_data_var_map_array=data_var_map_array,
                                lsm_precip_data_var=precip_data_var,
                                lsm_precip_type=precip_type,
                                lsm_lat_var=lsm_lat_var,
                                lsm_lon_var=lsm_lon_var,
                                lsm_file_date_naming_convention=lsm_file_date_naming_convention,
                                connection_list_file=connection_list_file,                                    
                                )
            
            gr.run_forecast()
    """
    
    def __init__(self, 
                 gssha_executable, 
                 gssha_directory, 
                 project_filename,
                 gssha_simulation_start=None,
                 gssha_simulation_end=None,
                 spt_watershed_name=None,
                 spt_subbasin_name=None,
                 spt_forecast_date_string=None,
                 ckan_engine_url=None,
                 ckan_api_key=None,
                 ckan_owner_organization=None,
                 path_to_rapid_qout=None,
                 connection_list_file=None,
                 lsm_folder=None,
                 lsm_data_var_map_array=None,
                 lsm_precip_data_var=None,
                 lsm_precip_type=None,
                 lsm_lat_var=None,
                 lsm_lon_var=None,
                 lsm_file_date_naming_convention=None,
                 lsm_time_var='time',                
                 lsm_search_card="*.nc",
                 precip_interpolation_type="THIESSEN",
                 output_netcdf=False
                 ):
        """
        Initializer
        """
        self.gssha_executable = gssha_executable
        self.gssha_directory = gssha_directory
        self.project_filename = project_filename
        self.project_name = os.path.splitext(project_filename)[0]
        self.gssha_simulation_start = gssha_simulation_start
        self.gssha_simulation_end = gssha_simulation_end
        self.spt_watershed_name = spt_watershed_name
        self.spt_subbasin_name = spt_subbasin_name
        self.spt_forecast_date_string = spt_forecast_date_string
        self.ckan_engine_url = ckan_engine_url
        self.ckan_api_key = ckan_api_key
        self.ckan_owner_organization = ckan_owner_organization
        self.path_to_rapid_qout = path_to_rapid_qout
        self.connection_list_file = connection_list_file
        self.lsm_folder = lsm_folder
        self.lsm_data_var_map_array = lsm_data_var_map_array
        self.lsm_precip_data_var = lsm_precip_data_var
        self.lsm_precip_type = lsm_precip_type
        self.lsm_lat_var = lsm_lat_var
        self.lsm_lon_var = lsm_lon_var
        self.lsm_file_date_naming_convention = lsm_file_date_naming_convention
        self.lsm_time_var = lsm_time_var
        self.lsm_search_card = lsm_search_card
        self.precip_interpolation_type = precip_interpolation_type
        self.output_netcdf = output_netcdf
        
        os.chdir(self.gssha_directory)
        
        # Create Test DB
        sqlalchemy_url, sql_engine = dbt.init_sqlite_memory()
        
        # Create DB Sessions
        self.db_session = dbt.create_session(sqlalchemy_url, sql_engine)
    
        # Instantiate GSSHAPY object for reading to database
        self.project_manager = ProjectFile()
        
        # Call read method
        self.project_manager.read(directory=self.gssha_directory,
                                  filename=self.project_filename,
                                  session=self.db_session)
    
        #update centroid and timezone
        self._update_centroid_timezone()
    
    def _update_class_var(self, var_name, new_value):
        """
        Updates the class attribute if needed
        """
        if new_value:
            setattr(self, var_name, new_value)
            
    def _update_card(self, card_name, new_value, add_quotes=False):
        """
        Adds/updates card for gssha project file
        """
        card_name = card_name.upper()
        gssha_card = self.project_manager.getCard(card_name)
        
        if add_quotes:
            new_value = "\"{0}\"".format(new_value)
            
        if gssha_card is None:
            #add new card
            new_card = ProjectCard(name=card_name, value=new_value)
            self.project_manager.projectCards.append(new_card)
        else:
            gssha_card.value = new_value
    
    def _delete_card(self, card_name):
        """
        Removes card from gssha project file
        """
        card_name = card_name.upper()
        gssha_card = self.project_manager.getCard(card_name)
        if gssha_card is not None:
            self.db_session.delete(gssha_card)
            self.db_session.commit()

    def _update_centroid_timezone(self):
        """
        This function updates the centroid and timezone
        based of off GSSHA elevation grid
        """
        gssha_ele_card = self.project_manager.getCard("ELEVATION")
        if gssha_ele_card is None:
            raise Exception("ERROR: ELEVATION card not found ...")

        gssha_pro_card = self.project_manager.getCard("#PROJECTION_FILE")
        if gssha_pro_card is None:
            raise Exception("ERROR: #PROJECTION_FILE card not found ...")
            
        #GET CENTROID FROM GSSHA GRID
        gssha_grid = gdal.Open(gssha_ele_card.value.strip('"'))
        gssha_srs=osr.SpatialReference()
        with open(gssha_pro_card.value.strip('"')) as pro_file:
            self.gssha_prj_str = pro_file.read()
            gssha_srs.ImportFromWkt(self.gssha_prj_str)
            self.gssha_proj4 = Proj(gssha_srs.ExportToProj4())
        
        min_x, xres, xskew, max_y, yskew, yres  = gssha_grid.GetGeoTransform()
        max_x = min_x + (gssha_grid.RasterXSize * xres)
        min_y = max_y + (gssha_grid.RasterYSize * yres)
        
        x_ext, y_ext = transform(self.gssha_proj4,
                                 Proj(init='epsg:4326'),
                                 [min_x, max_x, min_x, max_x],
                                 [min_y, max_y, max_y, min_y], 
                                 )
        
        self.center_lat = mean(y_ext)
        self.center_lon = mean(x_ext)
        
        #update time zone
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=self.center_lon, lat=self.center_lat)
        
        self.tz = timezone(tz_name)
        
    def _update_gmt(self):
        """
        Based on timzone and start date, the GMT card is updated
        """
        if self.gssha_simulation_start is not None:
            #NOTE: Because of daylight savings time, 
            #offset result depends on time of the year
            offset_string = self.gssha_simulation_start.replace(tzinfo=self.tz).strftime('%z')
            if not offset_string:
                offset_string = '0' #assume UTC 
            else:
                sign = offset_string[0]
                hr_offset = int(offset_string[1:3]) + int(offset_string[-2:])/60.0
                offset_string = "{0}{1:.1f}".format(sign, hr_offset)

            self._update_card('GMT', offset_string)

            
    def download_spt_forecast(self, extract_directory):
        """
        Downloads Streamflow Prediction Tool forecast data
        """
        needed_vars = [self.spt_watershed_name, 
                       self.spt_subbasin_name,
                       self.spt_forecast_date_string,
                       self.ckan_engine_url,
                       self.ckan_api_key,
                       self.ckan_owner_organization]
                       
        if not None in needed_vars:

            er_manager = ECMWFRAPIDDatasetManager(self.ckan_engine_url, 
                                                  self.ckan_api_key,
                                                  self.ckan_owner_organization)
            #TODO: Modify to only download one of the forecasts in the ensemble
            er_manager.download_prediction_dataset(watershed=self.spt_watershed_name, 
                                                   subbasin=self.spt_subbasin_name, 
                                                   date_string=self.spt_forecast_date_string, #'20160711.1200' 
                                                   extract_directory=extract_directory)
                                                   
            return glob(os.path.join(extract_directory, self.spt_forecast_date_string, "Qout*52.nc"))[0]
            
        elif needed_vars.count(None) == len(needed_vars):
            print("Skipping streamflow forecast download ...")
            return None
        else:
            raise ValueError("To download the forecasts, you need to set: \n"
                             "spt_watershed_name, spt_subbasin_name, spt_forecast_date_string \n"
                             "ckan_engine_url, ckan_api_key, and ckan_owner_organization."                             
                             )

    def download_wrf_forecast(self):
        """
        Downloads WRF forecast data
        """
        #TODO: Download WRF Forecasts
        return        
        
        
    def prepare_rapid_streamflow(self, path_to_rapid_qout, connection_list=None):
        """
        Prepares RAPID streamflow for GSSHA simulation
        """
        self._update_class_var('connection_list', connection_list)

        ihg_filename = os.path.join('{0}.ihg'.format(self.project_name))
        
        #write out IHG file
        start_datetime = None
        time_delta = 3600 #1 hr
        time_index_range = []
        with RAPIDDataset(path_to_rapid_qout, out_tzinfo=self.tz) as qout_nc:
        
            time_index_range = qout_nc.get_time_index_range(date_search_start=self.gssha_simulation_start,
                                                            date_search_end=self.gssha_simulation_end)
                                                            
            if len(time_index_range)>0:                                                
                time_array = qout_nc.get_time_array(return_datetime=True,
                                                    time_index_array=time_index_range)
                start_datetime = time_array[0]
                try:
                    time_delta = time_array[1] - start_datetime
                except IndexError:
                    pass
                if self.gssha_simulation_end is None:
                    self.gssha_simulation_end = time_array[-1]
                    
                qout_nc.write_flows_to_gssha_time_series_ihg(ihg_filename,
                                                             self.connection_list_file,
                                                             date_search_start=self.gssha_simulation_start,
                                                             date_search_end=self.gssha_simulation_end,
                                                             )
            else:
                print("WARNING: No streamflow values found in time range ...")
    
        if len(time_index_range)>0:
            # update cards
            if self.gssha_simulation_start is not None:
                #GSSHA CODE SKIPS FIRST TIME STEP, SO HAVE TO MOVE TIME BACK TO CATCH IT ALL
                if (start_datetime-time_delta) <= self.gssha_simulation_start:
                    print("WARNING: GSSHA simulation start time changed from "
                          "{0} to {1} in order to capture the streamflow.".format(self.gssha_simulation_start,
                                                                                  start_datetime-time_delta)
                         )
                    self.gssha_simulation_start = (start_datetime-time_delta)
                         
            else:
                self.gssha_simulation_start = (start_datetime-time_delta)
 
            self._update_card("START_DATE", self.gssha_simulation_start.strftime("%Y %m %d"))
            self._update_card("START_TIME", self.gssha_simulation_start.strftime("%H %M"))

            self._update_card("END_TIME", self.gssha_simulation_end.strftime("%Y %m %d %H %M"))
            self._update_card("CHAN_POINT_INPUT", ihg_filename, True)

            #UPDATE GMT CARD
            self._update_gmt()
        
    def prepare_wrf_data(self):
        """
        Prepares WRF forecast for GSSHA simulation
        """
        needed_vars = [self.lsm_folder, 
                       self.lsm_data_var_map_array,
                       self.lsm_precip_data_var,
                       self.lsm_precip_type,
                       self.lsm_lat_var,
                       self.lsm_lon_var,
                       self.lsm_file_date_naming_convention]

        if None not in needed_vars:
            l2g = LSMtoGSSHA(gssha_project_folder=self.gssha_directory,
                             gssha_grid_file_name='{0}.ele'.format(self.project_name),
                             lsm_input_folder_path=self.lsm_folder,
                             lsm_search_card=self.lsm_search_card, 
                             lsm_lat_var=self.lsm_lat_var,
                             lsm_lon_var=self.lsm_lon_var,
                             lsm_time_var=self.lsm_time_var,
                             lsm_file_date_naming_convention=self.lsm_file_date_naming_convention,
                             output_timezone=self.tz,
                             )
            
            out_gage_file = os.path.join('{0}.gag'.format(self.project_name))
            l2g.lsm_precip_to_gssha_precip_gage(out_gage_file,
                                                lsm_data_var=self.lsm_precip_data_var,
                                                precip_type=self.lsm_precip_type)
            

            if self.output_netcdf:
                netcdf_file_path = os.path.join('{0}_hmet.nc'.format(self.project_name))
                l2g.lsm_data_to_subset_netcdf(netcdf_file_path, self.lsm_data_var_map_array)
                self._update_card("HMET_NETCDF", netcdf_file_path, True)
                self._delete_card("HMET_ASCII")
            else:
                l2g.lsm_data_to_arc_ascii(self.lsm_data_var_map_array)
                self._update_card("HMET_ASCII", os.path.join('hmet_ascii_data', 'hmet_file_list.txt'), True)
                self._delete_card("HMET_NETCDF")
        
            #UPDATE GSSHA CARDS
            #make sure long term added as it is required for reading in HMET
            self._update_card('LONG_TERM', '')
            self._update_card('SEASONAL_RS', '')
            self._update_card('LATITUDE', str(self.center_lat))
            self._update_card('LONGITUDE', str(self.center_lon))
            
            #precip file read in
            self._update_card('PRECIP_FILE', out_gage_file, True)
            if self.precip_interpolation_type.upper() == "INV_DISTANCE":
                self._update_card('RAIN_INV_DISTANCE', '')
                self._delete_card('RAIN_THIESSEN')
            else:
                self._update_card('RAIN_THIESSEN', '')
                self._delete_card('RAIN_INV_DISTANCE')
            
            if self.gssha_simulation_start is None:
                self.gssha_simulation_start = datetime.utcfromtimestamp(l2g.hourly_time_array[0]).replace(tzinfo=utc).astimezone(tz=self.tz).replace(tzinfo=None)
            
                self._update_card("START_DATE", self.gssha_simulation_start.strftime("%Y %m %d"))
                self._update_card("START_TIME", self.gssha_simulation_start.strftime("%H %M"))
                
            if self.gssha_simulation_end is None:
                self.gssha_simulation_end = datetime.utcfromtimestamp(l2g.hourly_time_array[-1]).replace(tzinfo=utc).astimezone(tz=self.tz).replace(tzinfo=None)
                self._update_card("END_TIME", self.gssha_simulation_end.strftime("%Y %m %d %H %M"))

            #UPDATE GMT CARD
            self._update_gmt()

            
        elif needed_vars.count(None) == len(needed_vars):
            print("Skipping WRF process ...")
            return
            
        else:
            raise ValueError("To download the forecasts, you need to set: \n"
                             "lsm_folder, lsm_data_var_map_array, lsm_precip_data_var \n"
                             "lsm_precip_type, lsm_lat_var, lsm_lon_var, \n"
                             "and lsm_file_date_naming_convention."                             
                             )
        
    def run(self):
        """
        Write out project file and run GSSHA simulation
        """
        #WRITE OUT UPDATED GSSHA PROJECT FILE
        self.project_manager.write(session=self.db_session, 
                                   directory=self.gssha_directory, 
                                   name=self.project_name)
        
        #RUN SIMULATION
        print("RUNNING GSSHA SIMULATION ...")
        run_gssha_command = [self.gssha_executable, 
                             os.path.join(self.gssha_directory, self.project_filename)]

        process = Popen(run_gssha_command, 
                        stdout=PIPE, stderr=PIPE, shell=False)
        out, err = process.communicate()
        if out:
            for line in out.split(b'\n'):
                print(line)
        if err:
            print("ERROR: {0}".format(err))

    def run_forecast(self, 
                     path_to_rapid_qout=None,
                     connection_list_file=None,
                     lsm_folder=None,
                     lsm_data_var_map_array=None,
                     lsm_precip_data_var=None,
                     lsm_precip_type=None,
                     lsm_lat_var=None,
                     lsm_lon_var=None,
                     lsm_file_date_naming_convention=None,
                     lsm_time_var=None,                
                     lsm_search_card=None,
                     precip_interpolation_type=None,
                     output_netcdf=None
                     ):
        
        """
        Updates card & runs for RAPID to GSSHA & LSM to GSSHA

        .. warning:: This code assumes the time zone is UTC or GMT 0.
       
        Args:
            path_to_rapid_qout(Optional[str]): Path to the RAPID Qout file. Use this if you do NOT want to download the forecast and you want to use RAPID streamflows.
            connection_list_file(Optional[list]): List connecting GSSHA rivers to RAPID river network.
            lsm_folder(Optional[str]): Path to folder with land surface model data. See: *lsm_input_folder_path* variable at :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA`.
            lsm_data_var_map_array(Optional[str]): Array with connections for LSM output and GSSHA input. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.`
            lsm_precip_data_var(Optional[list or str]): String of name for precipitation variable name or list of precip variable names.  See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
            lsm_precip_type(Optional[str]): Type of precipitation. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
            lsm_lat_var(Optional[str]): Name of the latitude variable in the LSM netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
            lsm_lon_var(Optional[str]): Name of the longitude variable in the LSM netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
            lsm_file_date_naming_convention(Optional[str]): Array with connections for LSM output and GSSHA input. See: :func:`~gridtogssha.LSMtoGSSHA`.
            lsm_time_var(Optional[str]): Name of the time variable in the LSM netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
            lsm_search_card(Optional[str]): Glob search pattern for LSM files. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA`.
            precip_interpolation_type(Optional[str]): Type of interpolation for LSM precipitation. Can be "INV_DISTANCE" or "THIESSEN". Default is "THIESSEN".
            output_netcdf(Optional[bool]): If you want the HMET data output as a NetCDF4 file for input to GSSHA. Default is False.
            
        Example modifying parameters after class initialization:
        
        .. code:: python
            
                from gridtogssha.framework import GSSHAFramework
                
                gssha_executable = 'C:/Program Files/WMS 10.1 64-bit/gssha/gssha.exe'
                gssha_directory = "C:/Users/{username}/Documents/GSSHA"
                project_filename = "gssha_project.prj"
                
                #RAPID INPUTS
                path_to_rapid_qout = 'C:/Users/{username}/Documents/GSSHA/Qout_rapid_watershed.nc'
                #list to connect the RAPID rivers to GSSHA rivers
                connection_list_file = "C:/Users/{username}/Documents/GSSHA/rapid_to_gssha_connect.csv"

                #WRF INPUTS
                lsm_folder = '"C:/Users/{username}/Documents/GSSHA/wrf-sample-data-v1.0'
                lsm_lat_var = 'XLAT'
                lsm_lon_var = 'XLONG'
                search_card = '*.nc'
                precip_data_var = ['RAINC', 'RAINNC']
                precip_type = 'ACCUM'
                lsm_file_date_naming_convention='gssha_d02_%Y_%m_%d_%H_%M_%S.nc'
                
                data_var_map_array = [
                                      ['precipitation_acc', ['RAINC', 'RAINNC']], 
                                      ['pressure', 'PSFC'], 
                                      ['relative_humidity', ['Q2', 'PSFC', 'T2']], 
                                      ['wind_speed', ['U10', 'V10']], 
                                      ['direct_radiation', ['SWDOWN', 'DIFFUSE_FRAC']],
                                      ['diffusive_radiation', ['SWDOWN', 'DIFFUSE_FRAC']],
                                      ['temperature', 'T2'],
                                      ['cloud_cover' , 'CLDFRA'],
                                     ]
                
                #INITIALIZE CLASS AND RUN
                gr = GSSHAFramework(gssha_executable,
                                    gssha_directory, 
                                    project_filename)
                
                gr.run_forecast(lsm_folder=lsm_folder,
                                lsm_data_var_map_array=data_var_map_array,
                                lsm_precip_data_var=precip_data_var,
                                lsm_precip_type=precip_type,
                                lsm_lat_var=lsm_lat_var,
                                lsm_lon_var=lsm_lon_var,
                                lsm_file_date_naming_convention=lsm_file_date_naming_convention,
                                path_to_rapid_qout=path_to_rapid_qout, 
                                connection_list_file=connection_list_file,
                                )
 
        """
        #self._update_card("PROJECT_PATH", self.gssha_directory)
        self._update_card("PROJECT_PATH", "", True)
        
        self._update_class_var('path_to_rapid_qout', path_to_rapid_qout)
        self._update_class_var('connection_list_file', connection_list_file)
        self._update_class_var('lsm_folder', lsm_folder)
        self._update_class_var('lsm_data_var_map_array', lsm_data_var_map_array)
        self._update_class_var('lsm_precip_data_var', lsm_precip_data_var)
        self._update_class_var('lsm_precip_type', lsm_precip_type)
        self._update_class_var('lsm_lat_var', lsm_lat_var)
        self._update_class_var('lsm_lon_var', lsm_lon_var)
        self._update_class_var('lsm_file_date_naming_convention', lsm_file_date_naming_convention)
        self._update_class_var('lsm_time_var', lsm_time_var)
        self._update_class_var('lsm_search_card', lsm_search_card)
        self._update_class_var('precip_interpolation_type', precip_interpolation_type)
        self._update_class_var('output_netcdf', output_netcdf)

        #----------------------------------------------------------------------
        #RAPID to GSSHA
        #----------------------------------------------------------------------
        #if no streamflow given, download forecast
        if self.path_to_rapid_qout is None:
            rapid_qout_directory = os.path.join(self.gssha_directory, 'rapid_streamflow')
            try:
                os.mkdir(rapid_qout_directory)
            except OSError:
                pass
            self.path_to_rapid_qout = self.download_spt_forecast(rapid_qout_directory)
            
        #prepare input for GSSHA if user wants
        if self.path_to_rapid_qout is not None:
            self.prepare_rapid_streamflow(self.path_to_rapid_qout)

        #----------------------------------------------------------------------
        #LSM to GSSHA
        #----------------------------------------------------------------------
        self.download_wrf_forecast()
        self.prepare_wrf_data()
                               
        #----------------------------------------------------------------------
        #Run GSSHA
        #----------------------------------------------------------------------
        self.run()
        
        
class GSSHA_WRF_Framework(GSSHAFramework):
    """
    This class is for automating the connection between RAPID to GSSHA and WRF to GSSHA.
    There are several different configurations depending upon what you choose.
    
    There are three options for RAPID to GSSHA:
    
    1. Download and run using forecast from the Streamflow Prediction Tool (See: https://streamflow-prediction-tool.readthedocs.io)
    2. Run from RAPID Qout file
    3. Don't run using RAPID to GSSHA
    
    There are two options for WRF to GSSHA:
    
    1. Run from WRF to GSSHA
    2. Don't run using WRF to GSSHA
    
    
    Parameters:
        gssha_executable(str): Path to GSSHA executable. 
        gssha_directory(str): Path to directory for GSSHA project.
        project_filename(str): Name of GSSHA project file.
        gssha_simulation_start(Optional[datetime]): Datetime object with date of start of GSSHA simulation.
        gssha_simulation_end(Optional[datetime]): Datetime object with date of end of GSSHA simulation.
        spt_watershed_name(Optional[str]): Streamflow Prediction Tool watershed name.
        spt_subbasin_name(Optional[str]): Streamflow Prediction Tool subbasin name.
        spt_forecast_date_string(Optional[str]): Streamflow Prediction Tool forecast date string.
        ckan_engine_url(Optional[str]): CKAN engine API url.
        ckan_api_key(Optional[str]): CKAN api key.
        ckan_owner_organization(Optional[str]): CKAN owner organization.
        path_to_rapid_qout(Optional[str]): Path to the RAPID Qout file. Use this if you do NOT want to download the forecast and you want to use RAPID streamflows.
        connection_list_file(Optional[str]): CSV file with list connecting GSSHA rivers to RAPID river network. See: http://rapidpy.readthedocs.io/en/latest/rapid_to_gssha.html
        lsm_folder(Optional[str]): Path to folder with land surface model data. See: *lsm_input_folder_path* variable at :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA`.
        lsm_data_var_map_array(Optional[str]): Array with connections for WRF output and GSSHA input. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.`
        lsm_precip_data_var(Optional[list or str]): String of name for precipitation variable name or list of precip variable names.  See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
        lsm_precip_type(Optional[str]): Type of precipitation. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
        lsm_lat_var(Optional[str]): Name of the latitude variable in the WRF netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
        lsm_lon_var(Optional[str]): Name of the longitude variable in the WRF netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
        lsm_file_date_naming_convention(Optional[str]): Array with connections for WRF output and GSSHA input. See: :func:`~gridtogssha.LSMtoGSSHA`.
        lsm_time_var(Optional[str]): Name of the time variable in the WRF netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
        lsm_search_card(Optional[str]): Glob search pattern for WRF files. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA`.
        precip_interpolation_type(Optional[str]): Type of interpolation for WRF precipitation. Can be "INV_DISTANCE" or "THIESSEN". Default is "THIESSEN".
        output_netcdf(Optional[bool]): If you want the HMET data output as a NetCDF4 file for input to GSSHA. Default is False.

    Example running full framework with RAPID and LSM locally stored:
    
    .. code:: python
        
            from gridtogssha.framework import GSSHA_WRF_Framework

            gssha_executable = 'C:/Program Files/WMS 10.1 64-bit/gssha/gssha.exe'
            gssha_directory = "C:/Users/{username}/Documents/GSSHA"
            project_filename = "gssha_project.prj"

            #LSM TO GSSHA
            lsm_folder = '"C:/Users/{username}/Documents/GSSHA/wrf-sample-data-v1.0'
            lsm_file_date_naming_convention = 'gssha_d02_%Y_%m_%d_%H_%M_%S.nc'

            #RAPID TO GSSHA
            path_to_rapid_qout = "C:/Users/{username}/Documents/GSSHA/Qout.nc"
            connection_list_file = "C:/Users/{username}/Documents/GSSHA/rapid_to_gssha_connect.csv"
            
            #INITIALIZE CLASS AND RUN
            gr = GSSHA_WRF_Framework(gssha_executable,
                                     gssha_directory, 
                                     project_filename,
                                     lsm_folder=lsm_folder,
                                     lsm_file_date_naming_convention=lsm_file_date_naming_convention,
                                     path_to_rapid_qout=path_to_rapid_qout,
                                     connection_list_file=connection_list_file,                                    
                                    )
            
            gr.run_forecast()

    Example connecting SPT to GSSHA:
    
    .. code:: python
        
            from gridtogssha.framework import GSSHA_WRF_Framework

            gssha_executable = 'C:/Program Files/WMS 10.1 64-bit/gssha/gssha.exe'
            gssha_directory = "C:/Users/{username}/Documents/GSSHA"
            project_filename = "gssha_project.prj"
            
            #LSM TO GSSHA
            lsm_folder = '"C:/Users/{username}/Documents/GSSHA/wrf-sample-data-v1.0'
            lsm_file_date_naming_convention = 'gssha_d02_%Y_%m_%d_%H_%M_%S.nc'

            #RAPID TO GSSHA
            connection_list_file = "C:/Users/{username}/Documents/GSSHA/rapid_to_gssha_connect.csv"
            
            #SPT TO GSSHA
            ckan_engine_url='http://ckan/api/3/action'
            ckan_api_key='your-api-key'
            ckan_owner_organization='your_organization'
            spt_watershed_name='watershed_name'
            spt_subbasin_name='subbasin_name'
            spt_forecast_date_string='20160721.1200'
            
            #INITIALIZE CLASS AND RUN
            gr = GSSHA_WRF_Framework(gssha_executable,
                                     gssha_directory, 
                                     project_filename,
                                     lsm_folder=lsm_folder,
                                     lsm_file_date_naming_convention=lsm_file_date_naming_convention,
                                     connection_list_file=connection_list_file,                                    
                                     ckan_engine_url=ckan_engine_url,
                                     ckan_api_key=ckan_api_key,
                                     ckan_owner_organization=ckan_owner_organization,
                                     spt_watershed_name=spt_watershed_name,
                                     spt_subbasin_name=spt_subbasin_name,
                                     spt_forecast_date_string=spt_forecast_date_string,
                                    )
            
            gr.run_forecast()
    """
    
    def __init__(self, 
                 gssha_executable, 
                 gssha_directory, 
                 project_filename,
                 gssha_simulation_start=None,
                 gssha_simulation_end=None,
                 spt_watershed_name=None,
                 spt_subbasin_name=None,
                 spt_forecast_date_string=None,
                 ckan_engine_url=None,
                 ckan_api_key=None,
                 ckan_owner_organization=None,
                 path_to_rapid_qout=None,
                 connection_list_file=None,
                 lsm_folder=None,
                 lsm_data_var_map_array=None,
                 lsm_precip_data_var= ['RAINC', 'RAINNC'],
                 lsm_precip_type='ACCUM',
                 lsm_lat_var='XLAT',
                 lsm_lon_var='XLONG',
                 lsm_file_date_naming_convention=None,
                 lsm_time_var='time',                
                 lsm_search_card="*.nc",
                 precip_interpolation_type="THIESSEN",
                 output_netcdf=False
                 ):
        """
        Initializer
        """
        if lsm_data_var_map_array is None:
            lsm_data_var_map_array = [
                                      ['precipitation_acc', ['RAINC', 'RAINNC']], 
                                      ['pressure', 'PSFC'], 
                                      ['relative_humidity', ['Q2', 'PSFC', 'T2']], 
                                      ['wind_speed', ['U10', 'V10']], 
                                      ['direct_radiation', ['SWDOWN', 'DIFFUSE_FRAC']],
                                      ['diffusive_radiation', ['SWDOWN', 'DIFFUSE_FRAC']],
                                      ['temperature', 'T2'],
                                      ['cloud_cover' , 'CLDFRA'],
                                     ]

        super(GSSHA_WRF_Framework, self).__init__(gssha_executable, gssha_directory, project_filename,
                                                  gssha_simulation_start, gssha_simulation_end, spt_watershed_name,
                                                  spt_subbasin_name, spt_forecast_date_string, ckan_engine_url,
                                                  ckan_api_key, ckan_owner_organization, path_to_rapid_qout, 
                                                  connection_list_file, lsm_folder, lsm_data_var_map_array, 
                                                  lsm_precip_data_var, lsm_precip_type, lsm_lat_var, lsm_lon_var,
                                                  lsm_file_date_naming_convention, lsm_time_var,                
                                                  lsm_search_card, precip_interpolation_type, output_netcdf)

        
