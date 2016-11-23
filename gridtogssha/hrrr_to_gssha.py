# -*- coding: utf-8 -*-
##
##  lsm_to_gssha.py
##  GSSHApy
##
##  Created by Alan D Snow, 2016.
##  License BSD 3-Clause

from datetime import datetime
from os import mkdir, path, remove

#extra dependencies
try:
    import numpy as np
    from pyproj import Proj
    import requests
except ImportError:
    print("To use HRRRtoGSSHA, you must have the numpy, pyproj, and requests packages installed.")
    raise

try:
    import pygrib
except ImportError:
    print("WARNING: HRRRtoGSSHA will not work as pygrib is not installed properly ...")
    pass

from .grid_to_gssha import GRIDtoGSSHA
    
#------------------------------------------------------------------------------
# HELPER FUNCTIONS
#------------------------------------------------------------------------------

def get_grib_subset(grb,lat0,lat1,lon0,lon1):
    """
    Extracts a subset from the grib file based on lat/lon bounds
    """
    lats,lons = grb.latlons()
    
    ##determine the bounds of the data with grid preservation
    lat_where = np.where((lats >= lat0) & (lats <= lat1))[0]
    lon_where = np.where((lons >= lon0) & (lons <= lon1))[1]
    
    max_lat_index = lat_where.max()    
    min_lat_index = lat_where.min()    
    max_lon_index = lon_where.max()    
    min_lon_index = lon_where.min()    
    
    ##extract the subset of data
    return (grb.values[min_lat_index:max_lat_index, min_lon_index:max_lon_index],
            lats[min_lat_index:max_lat_index, min_lon_index:max_lon_index],
            lons[min_lat_index:max_lat_index, min_lon_index:max_lon_index])

def download_hrrr_for_gssha(main_directory, 
                            forecast_start_date_string, #EX. '20160913'
                            forecast_start_hour_string, #EX. '00' to '23'
                            leftlon=-180, rightlon=180,
                            toplat=90,bottomlat=-90):
    """
    Function to download HRRR data for GSSHA
    
    URL:
        http://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl
                                                          
    Args:
        main_directory(str): Location of the output for the forecast data.
        forecast_start_date_string(str): String for day of forecast. Ex. '20160913'
        forecast_start_hour_string(str): String for hour of forecast start. Ex. '02'
        leftlon(Optional[double,int]): Left bound for longitude. Default is -180.
        rightlon(Optional[double,int]): Right bound for longitude. Default is 180.
        toplat(Optional[double,int]): Top bound for latitude. Default is 90.
        bottomlat(Optional[double,int]): Bottom bound for latitude. Default is -90.

    Returns:
        downloaded_file_list(list): List of paths to downloaded files.

    Example::
    
        from gridtogssha.hrrr_to_gssha import download_hrrr_for_gssha

        hrrr_folder = '/HRRR'
        leftlon = -95
        rightlon = -75
        toplat = 35
        bottomlat = 30
        downloaded_file_list = download_hrrr_for_gssha(hrrr_folder,'20160914','01',
                                                       leftlon,rightlon,toplat,bottomlat)

    """
    out_directory = path.join(main_directory, forecast_start_date_string)
    
    try:
        mkdir(out_directory)
    except OSError:
        pass
    
    forecast_timestep_hour_string_array = ['00', '01', '02', '03', '04', 
                                           '05', '06', '07', '08', '09',
                                           '10', '11', '12', '13', '14',
                                           '15', '16', '17', '18']
    downloaded_file_list = []
    for forecast_timestep_hour_string in forecast_timestep_hour_string_array:
        file_name = 'hrrr.t{0}z.wrfsfcf{1}.grib2'.format(forecast_start_hour_string, forecast_timestep_hour_string)
        payload = {
                   'file': file_name, 
                   'lev_10_m_above_ground': 'on',
                   'lev_2_m_above_ground': 'on', 
                   'lev_entire_atmosphere': 'on',
                   'lev_surface': 'on', 
                   'var_DSWRF': 'on',
                   'var_PRATE': 'on', 
                   'var_PRES': 'on',
                   'var_RH': 'on', 
                   'var_TMP': 'on',
                   'var_UGRD': 'on', 
                   'var_VGRD': 'on',
                   'var_TCDC': 'on',
                   'subregion': '', 
                   'leftlon': str(leftlon),
                   'rightlon': str(rightlon), 
                   'toplat': str(toplat),
                   'bottomlat': str(bottomlat), 
                   'dir': '/hrrr.{0}'.format(forecast_start_date_string),
                   }
                   
        r = requests.get('http://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl', params=payload, stream=True)

        if r.status_code == requests.codes.ok:
            out_file = path.join(out_directory, file_name)
            downloaded_file_list.append(out_file)
            with open(out_file, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=1024):
                    fd.write(chunk)
        else: 
            print("ERROR: Problem downloading {0}".format(file_name))
            for filename in downloaded_file_list:
                try:
                    remove(filename)
                except OSError:
                    pass
            downloaded_file_list = []
            break
            
    return downloaded_file_list

#------------------------------------------------------------------------------
# MAIN CLASS
#------------------------------------------------------------------------------
class HRRRtoGSSHA(GRIDtoGSSHA):
    """This class converts the HRRR output data to GSSHA formatted input.
    This class inheris from class:`GRIDtoGSSHA`.
    
    Attributes:
        gssha_project_folder(str): Path to the GSSHA project folder
        gssha_grid_file_name(str): Name of the GSSHA elevation grid file.
        lsm_input_folder_path(str): Path to the input folder for the LSM files.
        lsm_search_card(str): Glob search pattern for LSM files. Ex. "*.grib2".
        lsm_file_date_naming_convention(Optional[str]): Use Pythons datetime conventions to find file. 
                                              Ex. "gssha_ddd_%Y_%m_%d_%H_%M_%S.nc".
        time_step_seconds(Optional[int]): If the time step is not able to be determined automatically, 
                                this parameter defines the time step in seconds for the LSM files.
        output_unix_format(Optional[bool]): If True, it will output to "unix" format. 
                                        Otherwise, it will output in "dos" (Windows) format. Default is False. 
        output_timezone(Optional[tzinfo]): This is the timezone to output the dates for the data. Default is UTC.

    Example::
    
        from gridtogssha import HRRRtoGSSHA

        l2g = HRRRtoGSSHA(gssha_project_folder='E:\\GSSHA',
                          gssha_grid_file_name='gssha.ele',
                          lsm_input_folder_path='E:\\GSSHA\\hrrr-data',
                          lsm_search_card="*.nc", 
                          lsm_file_date_naming_convention='gssha_d02_%Y_%m_%d_%H_%M_%S.nc'
                          )
                         
    """
    def __init__(self,
                 gssha_project_folder,
                 gssha_grid_file_name,
                 lsm_input_folder_path,
                 lsm_search_card, 
                 lsm_file_date_naming_convention=None,
                 time_step_seconds=None,
                 output_unix_format=False,
                 output_timezone=None,
                 ):
        """
        Initializer function for the HRRRtoGSSHA class
        """
        super(HRRRtoGSSHA, self).__init__(gssha_project_folder,
                                          gssha_grid_file_name,
                                          lsm_input_folder_path,
                                          lsm_search_card, 
                                          lsm_file_date_naming_convention,
                                          time_step_seconds,
                                          output_unix_format,
                                          output_timezone)    
    def _load_lsm_projection(self):
        """
        Loads the LSM projection in Proj4
        """
        self.lsm_proj4 = Proj(init='epsg:4326')
            
    def _get_subset_lat_lon(self, gssha_y_min, gssha_y_max, gssha_x_min, gssha_x_max):
        """
        #subset lat lon list based on GSSHA extent
        """
        ######
        #STEP 1: Load latitude and longiute
        ######
        grb_file = pygrib.open(self.lsm_nc_list[0])[1]
        lsm_lat_array,lsm_lon_array = grb_file.latlons()
        
        ######
        #STEP 2: Determine range within LSM Grid
        ######
        #get general buffer size
        lsm_dx = np.max(np.absolute(np.diff(lsm_lon_array)))
        lsm_dy = np.max(np.absolute(np.diff(lsm_lat_array, axis=0)))

        ##determine the bounds of the data with grid preservation
        lsm_lat_indices_from_lat, lsm_lon_indices_from_lat = np.where((lsm_lat_array >= (gssha_y_min - lsm_dy)) & (lsm_lat_array <= (gssha_y_max + lsm_dy)))
        lsm_lat_indices_from_lon, lsm_lon_indices_from_lon = np.where((lsm_lon_array >= (gssha_x_min - lsm_dx)) & (lsm_lon_array <= (gssha_x_max + lsm_dx)))

        self.lsm_lat_indices = np.intersect1d(lsm_lat_indices_from_lat, lsm_lat_indices_from_lon)
        self.lsm_lon_indices = np.intersect1d(lsm_lon_indices_from_lat, lsm_lon_indices_from_lon)
        
        lsm_lat_list = lsm_lat_array[self.lsm_lat_indices,:][:,self.lsm_lon_indices]
        lsm_lon_list = lsm_lon_array[self.lsm_lat_indices,:][:,self.lsm_lon_indices]
        """
        #TODO: ANOTHER METHOD TO TEST
        lat_where = np.where((lsm_lat_array >= (gssha_y_min - lsm_dy)) & (lsm_lat_array <= (gssha_y_max + lsm_dy)))[0]
        lon_where = np.where((lsm_lon_array >= (gssha_x_min - lsm_dx)) & (lsm_lon_array <= (gssha_x_max + lsm_dx)))[1]

        min_lat_index = lat_where.min()    
        max_lat_index = lat_where.max()
        if(max_lat_index-min_lat_index == 0):
            max_lat_index+=1
        
        max_lon_index = lon_where.max()    
        min_lon_index = lon_where.min()
        if(max_lon_index-min_lon_index == 0):
            max_lon_index+=1

        self.lsm_lat_indices = range(min_lat_index,max_lat_index+1)
        self.lsm_lon_indices = range(min_lon_index,max_lon_index+1)
        
        lsm_lat_list = lsm_lat_array[min_lat_index:max_lat_index,min_lon_index:max_lon_index]
        lsm_lon_list = lsm_lon_array[min_lat_index:max_lat_index,min_lon_index:max_lon_index]
        """
        if lsm_lat_list.size<=0 or lsm_lon_list.size<=0:
            raise IndexError("The GSSHA grid is not inside the HRRR domain ...")
            
        return (lsm_lat_list,
                lsm_lon_list)

 
    def _load_time_from_files(self):
        """
        Loads in the time from the grid files
        """
        epoch = datetime.utcfromtimestamp(0)
        
        if self.lsm_file_date_naming_convention is not None:
            #METHOD 1: LOAD FROM TIME STRING IN FILES
            for lsm_idx, lsm_nc_file in enumerate(self.lsm_nc_list):
                self.time_array[lsm_idx] = (datetime.strptime(path.basename(lsm_nc_file),self.lsm_file_date_naming_convention)-epoch).total_seconds()
        else:
            #METHOD 2: LOAD FROM TIME IN GRIB FILE
            for lsm_idx, lsm_nc_file in enumerate(self.lsm_nc_list):
                grb_file = pygrib.open(lsm_nc_file)[1]
                self.time_array[lsm_idx] = (grb_file.validDate-epoch).total_seconds()

        convert_to_seconds = 1
        return convert_to_seconds
        
    def _load_time_step(self, convert_to_seconds):
        """
        Loads in the time step
        """
        #GET TIME STEP
        if self.time_step_seconds is None:
            try:
                self.time_step_seconds = self.time_array[1] - self.time_array[0]
            except IndexError:
                raise IndexError("ERROR: Time delta not found. Please set time_step_seconds" \
                                 " in the HRRRtoGSSHA class initialization.")

    def _load_lsm_data(self, data_var, conversion_factor=1, four_dim_var_calc_method=None):
        """
        This extracts the LSM data from a folder of netcdf files
        """
        self.data_np_array = np.zeros((len(self.lsm_nc_list),
                                       len(self.lsm_lat_indices), 
                                       len(self.lsm_lon_indices)))
        
        for lsm_idx, lsm_nc_file in enumerate(self.lsm_nc_list):
            grb_file = pygrib.open(lsm_nc_file)
            grb = grb_file.select(shortName=data_var)[0]
            #EXTRACT DATA WITHIN EXTENT
            if four_dim_var_calc_method is None:
                self.data_np_array[lsm_idx] = grb.values[self.lsm_lat_indices,:][:,self.lsm_lon_indices]*conversion_factor
            else:
                self.data_np_array[lsm_idx] = four_dim_var_calc_method(grb.values[:, self.lsm_lat_indices, self.lsm_lon_indices]*conversion_factor, axis=0)
            grb_file.close()
