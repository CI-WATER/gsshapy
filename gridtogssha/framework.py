# -*- coding: utf-8 -*-
##
##  framework.py
##  GSSHApy
##
##  Created by Alan D Snow, 2016.
##  BSD 3-Clause

from glob import glob
from datetime import datetime #TODO: Add date filter for GSSHA
from pyproj import Proj, transform
import os
from RAPIDpy import RAPIDDataset
from spt_dataset_manager import ECMWFRAPIDDatasetManager
from subprocess import Popen, PIPE

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
        spt_watershed_name(Optional[str]): Streamflow Prediction Tool watershed name.
        spt_subbasin_name(Optional[str]): Streamflow Prediction Tool subbasin name.
        spt_forecast_date_string(Optional[str]): Streamflow Prediction Tool forecast date string.
        ckan_engine_url(Optional[str]): CKAN engine API url.
        ckan_api_key(Optional[str]): CKAN api key.
        ckan_owner_organization(Optional[str]): CKAN owner organization.
        connection_list(Optional[str]): List connecting GSSHA rivers to RAPID river network. See: http://rapidpy.readthedocs.io/en/latest/rapid_to_gssha.html
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
        
            gssha_executable = 'C:/Program Files/WMS 10.1 64-bit/gssha/gssha.exe'
            gssha_directory = "C:/Users/{username}/Documents/GSSHA"
            project_filename = "gssha_project.prj"
            
            #RAPID INPUTS
            #list to connect the RAPID rivers to GSSHA rivers
            connection_list = [
                               {
                                 'link_id': 599,
                                 'node_id': 1,
                                 'baseflow': 0.0,
                                 'rapid_rivid': 80968,
                               },
                             ]
            
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
                                connection_list=connection_list,                                    
                                )
            
            gr.run_forecast()
    """
    
    def __init__(self, 
                 gssha_executable, 
                 gssha_directory, 
                 project_filename,
                 spt_watershed_name=None,
                 spt_subbasin_name=None,
                 spt_forecast_date_string=None,
                 ckan_engine_url=None,
                 ckan_api_key=None,
                 ckan_owner_organization=None,
                 connection_list=None,
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
        self.spt_watershed_name = spt_watershed_name
        self.spt_subbasin_name = spt_subbasin_name
        self.spt_forecast_date_string = spt_forecast_date_string
        self.ckan_engine_url = ckan_engine_url
        self.ckan_api_key = ckan_api_key
        self.ckan_owner_organization = ckan_owner_organization
        self.connection_list = connection_list
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
        #TODO: Filter by date
        start_datetime = None
        end_datetime = None
        time_delta = 3600 #1 hr
        with RAPIDDataset(path_to_rapid_qout) as qout_nc:
            time_array = qout_nc.get_time_array(return_datetime=True)
            start_datetime = time_array[0]
            end_datetime = time_array[-1]
            #GSSHA CODE SKIPS FIRST TIME STEP, SO HAVE TO MOVE TIME BACK TO CATCH IT ALL
            try:
                time_delta = time_array[1] - start_datetime
            except IndexError:
                pass
                
            qout_nc.write_flows_to_gssha_time_series_ihg(ihg_filename,
                                                         self.connection_list,
                                                         mode="max"
                                                         )
    
        # update cards
        self._update_card("START_DATE", (start_datetime-time_delta).strftime("%Y %m %d"))
        self._update_card("START_TIME", (start_datetime-time_delta).strftime("%H %M"))
        self._update_card("END_TIME", end_datetime.strftime("%Y %m %d %H %M"))
        self._update_card("CHAN_POINT_INPUT", ihg_filename, True)
        
    def prepare_wrf_data(self):
        """
        Prepares WRF forecast for GSSHA simulation
        """
        l2g = LSMtoGSSHA(gssha_project_folder=self.gssha_directory,
                         gssha_grid_file_name='{0}.ele'.format(self.project_name),
                         lsm_input_folder_path=self.lsm_folder,
                         lsm_search_card=self.lsm_search_card, 
                         lsm_lat_var=self.lsm_lat_var,
                         lsm_lon_var=self.lsm_lon_var,
                         lsm_time_var=self.lsm_time_var,
                         lsm_file_date_naming_convention=self.lsm_file_date_naming_convention,
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
        
        #precip file read in
        self._update_card('PRECIP_FILE', out_gage_file, True)
        if self.precip_interpolation_type.upper() == "INV_DISTANCE":
            self._update_card('RAIN_INV_DISTANCE ', '')
            self._delete_card("RAIN_THIESSEN")
        else:
            self._update_card('RAIN_THIESSEN ', '')
            self._delete_card("RAIN_INV_DISTANCE")
        
        #assume UTC time zone
        self._update_card('GMT', str(0))
        
        #update centroid
        center_lon, center_lat = transform(l2g.gssha_proj4,
                                           Proj(init='epsg:4326'),
                                           [(l2g.east_bound+l2g.west_bound)/2.0],
                                           [(l2g.north_bound+l2g.south_bound)/2.0], 
                                           )
        
        self._update_card('LATITUDE', str(center_lat[0]))
        self._update_card('LONGITUDE', str(center_lon[0]))
        
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
        if err:
            raise Exception(err)
        else:
            for line in out.split(b'\n'):
                print(line)

    def run_forecast(self, 
                     path_to_rapid_qout=None,
                     connection_list=None,
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
            lsm_folder(Optional[str]): Path to folder with land surface model data. See: *lsm_input_folder_path* variable at :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA`.
            lsm_data_var_map_array(Optional[str]): Array with connections for LSM output and GSSHA input. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.`
            lsm_precip_data_var(Optional[list or str]): String of name for precipitation variable name or list of precip variable names.  See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
            lsm_precip_type(Optional[str]): Type of precipitation. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
            lsm_lat_var(Optional[str]): Name of the latitude variable in the LSM netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
            lsm_lon_var(Optional[str]): Name of the longitude variable in the LSM netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
            lsm_file_date_naming_convention(Optional[str]): Array with connections for LSM output and GSSHA input. See: :func:`~gridtogssha.LSMtoGSSHA`.
            lsm_time_var(Optional[str]): Name of the time variable in the LSM netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
            lsm_search_card(Optional[str]): Glob search pattern for LSM files. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA`.
            connection_list(Optional[list]): List connecting GSSHA rivers to RAPID river network.
            path_to_rapid_qout(Optional[str]): Path to the RAPID Qout file. Use this if you do NOT want to download the forecast and you want to use RAPID streamflows.
            precip_interpolation_type(Optional[str]): Type of interpolation for LSM precipitation. Can be "INV_DISTANCE" or "THIESSEN". Default is "THIESSEN".
            output_netcdf(Optional[bool]): If you want the HMET data output as a NetCDF4 file for input to GSSHA. Default is False.
            
        Example modifying parameters after class initialization:
        
        .. code:: python
            
                gssha_executable = 'C:/Program Files/WMS 10.1 64-bit/gssha/gssha.exe'
                gssha_directory = "C:/Users/{username}/Documents/GSSHA"
                project_filename = "gssha_project.prj"
                
                #RAPID INPUTS
                path_to_rapid_qout = 'C:/Users/{username}/Documents/GSSHA/Qout_rapid_watershed.nc'
                #list to connect the RAPID rivers to GSSHA rivers
                connection_list = [
                                   {
                                     'link_id': 599,
                                     'node_id': 1,
                                     'baseflow': 0.0,
                                     'rapid_rivid': 80968,
                                   },
                                 ]
                
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
                                connection_list=connection_list,
                                )
 
        """
        self._update_class_var('connection_list', connection_list)
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

        self._update_card("PROJECT_PATH", self.gssha_directory)
        
        #----------------------------------------------------------------------
        #RAPID to GSSHA
        #----------------------------------------------------------------------
        #if no streamflow given, download forecast
        if path_to_rapid_qout is None:
            rapid_qout_directory = os.path.join(self.gssha_directory, 'rapid_streamflow')
            try:
                os.mkdir(rapid_qout_directory)
            except OSError:
                pass
            path_to_rapid_qout = self.download_spt_forecast(rapid_qout_directory)
            
        #prepare input for GSSHA if user wants
        if path_to_rapid_qout is not None:
            self.prepare_rapid_streamflow(path_to_rapid_qout)

        #----------------------------------------------------------------------
        #LSM to GSSHA
        #----------------------------------------------------------------------
        self.download_wrf_forecast()
        self.prepare_wrf_data()
                               
        #----------------------------------------------------------------------
        #Run GSSHA
        #----------------------------------------------------------------------
        self.run()
        
        
if __name__ == "__main__":
    gssha_executable = 'C:/Program Files/WMS 10.1 64-bit/gssha/gssha.exe'
    gssha_directory = "C:/Users/RDCHLADS/Documents/GSSHA"
    project_filename = "my_project.prj"
    
    #RAPID
    path_to_rapid_qout = 'C:/Users/RDCHLADS/Documents/GSSHA/Qout_52.nc'
    #list to connect the RAPID rivers to GSSHA rivers
    connection_list = [
                       {
                         'link_id': 599,
                         'node_id': 1,
                         'baseflow': 0.0,
                         'rapid_rivid': 80968,
                       },
                     ]
    
    #LSM
    lsm_folder = 'F:/GSSHA/wrf-sample-data-v1.0'
    lsm_lat_var = 'XLAT'
    lsm_lon_var = 'XLONG'
    search_card = '*.nc'
    precip_data_var = ['RAINC', 'RAINNC']
    precip_type = 'ACCUM'
    lsm_file_date_naming_convention='gssha_d02_%Y_%m_%d_%H_%M_%S.nc'
    
    ##CONVERT FROM RAW WRF DATA
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
    
    gr = GSSHAFramework(gssha_executable,
                        gssha_directory, 
                        project_filename,
                        )
    
    gr.run_forecast(path_to_rapid_qout, 
                    connection_list,
                    lsm_folder,
                    data_var_map_array,
                    precip_data_var,
                    precip_type,
                    lsm_lat_var,
                    lsm_lon_var,
                    lsm_file_date_naming_convention,
                    )