# -*- coding: utf-8 -*-
##
##  lsm_to_gssha.py
##  GSSHApy
##
##  Created by Alan D Snow, 2016.
##  License BSD 3-Clause

from csv import writer as csv_writer
from datetime import datetime, timedelta
from dateutil import parser
from glob import glob
from io import open as io_open
import math
from os import mkdir, path, remove, rename
from os import name as os_name
from shutil import copy
import time

#extra dependencies
try:
    import numpy as np
    from pyproj import Proj, transform
    from osgeo import gdal, osr
    from netCDF4 import Dataset
except ImportError:
    print("To use LSMtoGSSHA, you must have the numpy, pyproj, osgeo, and netCDF4 packages installed.")
    raise
    
#------------------------------------------------------------------------------
# HELPER FUNCTIONS
#------------------------------------------------------------------------------
def update_hmet_card_file(hmet_card_file_path, new_hmet_data_path):
    """This function updates the paths in the HMET card file to the new 
    location of the HMET data. This is necessary because the file paths
    are absolute and will need to be updated if moved.

    Args:
        hmet_card_file_path(str): Location of the file used for the HMET_ASCII card.
        new_hmet_data_path(str): Location where the HMET ASCII files are currently. 

    Example::

        new_hmet_data_path = "E:\\GSSHA\\new_hmet_directory"
        hmet_card_file_path = "E:\\GSSHA\\hmet_card_file.txt"
        
        update_hmet_card_file(hmet_card_file_path, new_hmet_data_path)

    """
    hmet_card_file_path_temp = "{0}_tmp".format(hmet_card_file_path)
    try:
        remove(hmet_card_file_path_temp)
    except OSError:
        pass
        
    copy(hmet_card_file_path, hmet_card_file_path_temp)
    
    with io_open(hmet_card_file_path_temp, 'w', newline='\r\n') as out_hmet_list_file:
        with open(hmet_card_file_path) as old_hmet_list_file:
            for date_path in old_hmet_list_file:
                out_hmet_list_file.write(u"{0}\n".format(path.join(new_hmet_data_path, 
                                                        path.basename(date_path))))
    try:
        remove(hmet_card_file_path)
    except OSError:
        pass
    
    rename(hmet_card_file_path_temp, hmet_card_file_path)

#------------------------------------------------------------------------------
# MAIN CLASS
#------------------------------------------------------------------------------
class LSMtoGSSHA(object):
    """This class converts the LSM output data to GSSHA formatted input.
    
    Attributes:
        gssha_project_folder(str): Path to the GSSHA project folder
        gssha_grid_file_name(str): Name of the GSSHA elevation grid file.
        lsm_input_folder_path(str): Path to the input folder for the LSM files.
        lsm_search_card(str): Glob search pattern for LSM files. Ex. "*.nc".
        lsm_lat_var(Optional[str]): Name of the latitude variable in the LSM netCDF files. Defaults to 'lat'.
        lsm_lon_var(Optional[str]): Name of the longitude variable in the LSM netCDF files. Defaults to 'lon'.
        lsm_time_var(Optional[str]): Name of the time variable in the LSM netCDF files. Defaults to 'time'.
        lsm_file_date_naming_convention(Optional[str]): Use Pythons datetime conventions to find file. 
                                              Ex. "gssha_ddd_%Y_%m_%d_%H_%M_%S.nc".
        time_step_seconds(Optional[int]): If the time step is not able to be determined automatically, 
                                this parameter defines the time step in seconds for the LSM files.
        output_unix_format(Optional[str]): If True, it will output to "unix" format. 
                                        Otherwise, it will output in "dos" (Windows) format. Default is False. 

    Example::

        l2g = LSMtoGSSHA(gssha_project_folder='E:\\GSSHA',
                         gssha_grid_file_name='gssha.ele',
                         lsm_input_folder_path='E:\\GSSHA\\wrf-data',
                         lsm_search_card="*.nc", 
                         lsm_lat_var='XLAT',
                         lsm_lon_var='XLONG',
                         lsm_file_date_naming_convention='gssha_d02_%Y_%m_%d_%H_%M_%S.nc'
                         )
                         
    """
    def __init__(self,
                 gssha_project_folder,
                 gssha_grid_file_name,
                 lsm_input_folder_path,
                 lsm_search_card, 
                 lsm_lat_var='lat',
                 lsm_lon_var='lon',
                 lsm_time_var='time',
                 lsm_grid_type='geographic',
                 lsm_file_date_naming_convention=None,
                 time_step_seconds=None,
                 output_unix_format=False,
                 ):
        """
        Initializer function for the LSMtoGSSHA class
        """
        self.gssha_project_folder = gssha_project_folder
        self.gssha_grid_file_name = gssha_grid_file_name
        self.lsm_input_folder_path = lsm_input_folder_path
        self.lsm_search_card = lsm_search_card
        self.lsm_lat_var = lsm_lat_var
        self.lsm_lon_var = lsm_lon_var
        self.lsm_time_var = lsm_time_var
        self.lsm_grid_type = lsm_grid_type
        self.lsm_file_date_naming_convention = lsm_file_date_naming_convention
        self.time_step_seconds = time_step_seconds
        self.output_unix_format = output_unix_format
        
        self.default_line_ending = '\r\n'
        if output_unix_format:
            self.default_line_ending = ''
            
        ##INIT FUNCTIONS
        self._load_sorted_lsm_list_and_time()
        self._load_gssha_and_lsm_extent()
       
        ##DEFAULT GSSHA NetCDF Attributes
        self.netcdf_attributes = { 
                                    'precipitation_rate' : 
                                        #NOTE: LSM INFO
                                        #units = "kg m-2 s-1" ; i.e. mm s-1
                                        { 
                                          'units' : {
                                                        'gage': 'mm hr-1',
                                                        'ascii': 'mm hr-1',
                                                        'netcdf': 'mm hr-1',
                                                    },
                                          'units_netcdf' : 'mm hr-1',
                                          'standard_name' : 'rainfall_flux',
                                          'long_name' : 'Rain precipitation rate',
                                          'gssha_name' : 'precipitation',
                                          'hmet_name' : 'Prcp',
                                          'conversion_factor' : {
                                                                    'gage': 3600,
                                                                    'ascii' : 3600,
                                                                    'netcdf' : 3600,
                                                                },
                                        },
                                    'precipitation_acc' : 
                                        #NOTE: LSM INFO
                                        #units = "kg m-2" ; i.e. mm
                                        {
                                          'units' : {
                                                        'gage': 'mm hr-1',
                                                        'ascii': 'mm hr-1',
                                                        'netcdf': 'mm hr-1',
                                                    },
                                          'units_netcdf' : 'mm hr-1',
                                          'standard_name' : 'rainfall_flux',
                                          'long_name' : 'Rain precipitation rate',
                                          'gssha_name' : 'precipitation',
                                          'hmet_name' : 'Prcp',
                                          'conversion_factor' : {
                                                                    'gage' : 1,
                                                                    'ascii' : 1,
                                                                    'netcdf' : 1,
                                                                },
                                        },
                                    'precipitation_inc' : 
                                        #NOTE: LSM INFO
                                        #units = "kg m-2" ; i.e. mm
                                        {
                                          'units' : {
                                                        'gage': 'mm hr-1',
                                                        'ascii': 'mm hr-1',
                                                        'netcdf': 'mm hr-1',
                                                    },
                                          'units_netcdf' : 'mm hr-1',
                                          'standard_name' : 'rainfall_flux',
                                          'long_name' : 'Rain precipitation rate',
                                          'gssha_name' : 'precipitation',
                                          'hmet_name' : 'Prcp',
                                          'conversion_factor' : {
                                                                    'gage' : 1,
                                                                    'ascii' : 1,
                                                                    'netcdf' : 1,
                                                                },
                                        },
                                    'pressure' : 
                                        #NOTE: LSM INFO
                                        #units = "Pa" ;
                                        {
                                          'units' : {
                                                        'ascii': 'in. Hg',
                                                        'netcdf': 'mb',
                                                    },
                                          'standard_name' : 'surface_air_pressure',
                                          'long_name' : 'Pressure',
                                          'gssha_name' : 'pressure',
                                          'hmet_name' : 'Pres',
                                          'conversion_factor' : {
                                                                    'ascii' : 0.000295299830714,
                                                                    'netcdf' : 0.01,
                                                                },
                                        },
                                    'pressure_hg' : 
                                        {
                                          'units' : {
                                                        'ascii': 'in. Hg',
                                                        'netcdf': 'mb',
                                                    },
                                          'standard_name' : 'surface_air_pressure',
                                          'long_name' : 'Pressure',
                                          'gssha_name' : 'pressure',
                                          'hmet_name' : 'Pres',
                                          'conversion_factor' : {
                                                                    'ascii' : 1,
                                                                    'netcdf' : 33.863886667,
                                                                },
                                        },
                                    'relative_humidity' : 
                                        #NOTE: LSM Usually Specific Humidity
                                        #units = "kg kg-1" ;
                                        #standard_name = "specific_humidity" ;
                                        #long_name = "Specific humidity" ;
                                        {
                                          'units' : {
                                                        'ascii': '%',
                                                        'netcdf': '%',
                                                    },
                                          'standard_name' : 'relative_humidity',
                                          'long_name' : 'Relative humidity',
                                          'gssha_name' : 'relative_humidity',
                                          'hmet_name' : 'RlHm',
                                          'conversion_factor' : {
                                                                    'ascii' : 1,
                                                                    'netcdf' : 1,
                                                                },
                                        },
                                    'wind_speed' : 
                                        #NOTE: LSM
                                        #units = "m s-1" ;
                                        {
                                          'units' : {
                                                        'ascii': 'kts',
                                                        'netcdf': 'kts',
                                                    },
                                          'standard_name' : 'wind_speed',
                                          'long_name' : 'Wind speed',
                                          'gssha_name' : 'wind_speed',
                                          'hmet_name' : 'WndS',
                                          'conversion_factor' : {
                                                                    'ascii' : 1.94,
                                                                    'netcdf' : 1.94,
                                                                },
                                        },
                                    'wind_speed_kts' : 
                                        {
                                          'units' : {
                                                        'ascii': 'kts',
                                                        'netcdf': 'kts',
                                                    },
                                          'standard_name' : 'wind_speed',
                                          'long_name' : 'Wind speed',
                                          'gssha_name' : 'wind_speed',
                                          'hmet_name' : 'WndS',
                                          'conversion_factor' : {
                                                                    'ascii' : 1,
                                                                    'netcdf' : 1,
                                                                },
                                        },
                                    'temperature' :
                                        #NOTE: LSM
                                        #units = "K" ;
                                        {
                                          'units' : {
                                                        'ascii': 'F',
                                                        'netcdf': 'C',
                                                    },
                                          'standard_name' : 'air_temperature',
                                          'long_name' : 'Temperature',
                                          'gssha_name' : 'temperature',
                                          'hmet_name' : 'Temp',
                                          'conversion_factor' : {
                                                                    'ascii' : 1,
                                                                    'netcdf' : 1,
                                                                },
                                          'conversion_function' : {
                                                                    'ascii' : lambda temp_kelvin: temp_kelvin * 9.0/5.0 - 459.67,
                                                                    'netcdf' : lambda temp_celcius: temp_celcius - 273.15,
                                                                },
                                        },
                                    'temperature_f' :
                                        {
                                          'units' : {
                                                        'ascii': 'F',
                                                        'netcdf': 'C',
                                                    },
                                          'standard_name' : 'air_temperature',
                                          'long_name' : 'Temperature',
                                          'gssha_name' : 'temperature',
                                          'hmet_name' : 'Temp',
                                          'conversion_factor' : {
                                                                    'ascii' : 1,
                                                                    'netcdf' : 1,
                                                                },
                                          'conversion_function' : {
                                                                    'ascii' : lambda temp_farenheight: temp_farenheight,
                                                                    'netcdf' : lambda temp_farenheight: temp_farenheight * 5.0/9.0 - 32,
                                                                },
                                        },
                                    'direct_radiation' :
                                        #DIRECT/BEAM/SOLAR RADIATION
                                        #NOTE: LSM
                                        #WRF: global_radiation * (1-DIFFUSIVE_FRACTION)
                                        #units = "W m-2" ;
                                        {
                                          'units' : {
                                                        'ascii': 'W hr m-2',
                                                        'netcdf': 'W hr m-2',
                                                    },
                                          'standard_name' : 'surface_net_downward_shortwave_flux',
                                          'long_name' : 'Net short wave radiation flux',
                                          'gssha_name' : 'direct_radiation',
                                          'hmet_name' : 'DRad',
                                          'conversion_factor' : {
                                                                    'ascii' : 1,
                                                                    'netcdf' : 1,
                                                                },
                                        },
                                    'diffusive_radiation' :
                                        #DIFFUSIVE RADIATION
                                        #NOTE: LSM
                                        #WRF: global_radiation * DIFFUSIVE_FRACTION
                                        #units = "W m-2" ;
                                        {
                                          'units' : {
                                                        'ascii': 'W hr m-2',
                                                        'netcdf': 'W hr m-2',
                                                    },
                                          'standard_name' : 'surface_diffusive_shortwave_flux_in_air',
                                          'long_name' : 'Diffusive short wave radiation flux',
                                          'gssha_name' : 'diffusive_radiation',
                                          'hmet_name' : 'GRad', #6.1 GSSHA CODE INCORRECTLY SAYS IT IS GRAD
                                          'conversion_factor' : {
                                                                    'ascii' : 1,
                                                                    'netcdf' : 1,
                                                                },
                                        },
                                    'cloud_cover' :
                                        #NOTE: LSM
                                        #Between 0-1 (0=No Clouds; 1=Clouds) ;
                                        {
                                          'units' : {
                                                        'ascii': '%',
                                                        'netcdf': '%/10',
                                                    },
                                          'standard_name' : 'surface_net_downward_delta_flux',
                                          'long_name' : 'Global radiation flux',
                                          'gssha_name' : 'cloud_cover',
                                          'hmet_name' : 'Clod',
                                          'conversion_factor' : {
                                                                    'ascii' : 100,
                                                                    'netcdf' : 10,
                                                                },
                                          'four_dim_var_calc_method' : np.amax,
                                        },
                                    'cloud_cover_pc' :
                                        {
                                          'units' : {
                                                        'ascii': '%',
                                                        'netcdf': '%/10',
                                                    },
                                          'standard_name' : 'surface_net_downward_delta_flux',
                                          'long_name' : 'Global radiation flux',
                                          'gssha_name' : 'cloud_cover',
                                          'hmet_name' : 'Clod',
                                          'conversion_factor' : {
                                                                    'ascii' : 1,
                                                                    'netcdf' : 0.1,
                                                                },
                                        },

                                }
    
    def _load_lsm_projection(self):
        """
        Loads the LSM projection in Proj4
        """
        self.lsm_projection = None
        if self.lsm_grid_type=='geographic':
            self.lsm_proj4 = Proj(init='epsg:4326')
        elif self.lsm_grid_type=='wrf':
            lsm_nc = Dataset(self.lsm_nc_list[0])

            #####################Start of script adaption###############################################################
            #BASED ON: CreateWeightTableFromWRFGeogrid.py at github.com/Esri/python-toolbox-for-rapid

            # read projection information from global attributes
            map_proj = lsm_nc.__dict__['MAP_PROJ']
            standard_parallel_1 = lsm_nc.__dict__['TRUELAT1']
            standard_parallel_2 = lsm_nc.__dict__['TRUELAT2']
            central_meridian = lsm_nc.__dict__['STAND_LON']
            latitude_of_origin = lsm_nc.__dict__['CEN_LAT']

            if map_proj == 1:
                # Lambert Conformal Conic
                if 'standard_parallel_2' in locals():
                    print('    Using Standard Parallel 2 in Lambert Conformal Conic map projection.')
                    #http://www.remotesensing.org/geotiff/proj_list/lambert_conic_conformal_2sp.html
                else:
                    # According to http://webhelp.esri.com/arcgisdesktop/9.2/index.cfm?TopicName=Lambert_Conformal_Conic
                    #http://www.remotesensing.org/geotiff/proj_list/lambert_conic_conformal_1sp.html
                    standard_parallel_2 = standard_parallel_1
                    latitude_of_origin = standard_parallel_1

                lsm_proj4_str = ('+proj=lcc'
                                 ' +lat_0={0}'   #latitude_of_origin
                                 ' +lat_1={1}'   #standard_parallel_1
                                 ' +lat_2={2}'   #standard_parallel_2
                                 ' +lon_0={3}'   #central_meridian
                                 ' +x_0=0.0'     #false_easting
                                 ' +y_0=0.0'     #false_northing
                                 ).format(latitude_of_origin,
                                          standard_parallel_1,
                                          standard_parallel_2,
                                          central_meridian)

                self.lsm_proj4 = Proj(lsm_proj4_str)

            elif map_proj == 2:
                # Polar Stereographic

                # Set up pole latitude
                phi1 = float(standard_parallel_1)

                ### Back out the central_scale_factor (minimum scale factor?) using formula below using Snyder 1987 p.157 (USGS Paper 1395)
                ##phi = math.copysign(float(pole_latitude), float(latitude_of_origin))    # Get the sign right for the pole using sign of CEN_LAT (latitude_of_origin)
                ##central_scale_factor = (1 + (math.sin(math.radians(phi1))*math.sin(math.radians(phi))) + (math.cos(math.radians(float(phi1)))*math.cos(math.radians(phi))))/2

                # Method where central scale factor is k0, Derivation from C. Rollins 2011, equation 1: http://earth-info.nga.mil/GandG/coordsys/polar_stereographic/Polar_Stereo_phi1_from_k0_memo.pdf
                # Using Rollins 2011 to perform central scale factor calculations. For a sphere, the equation collapses to be much  more compact (e=0, k90=1)
                central_scale_factor = (1 + math.sin(math.radians(abs(phi1))))/2                            # Equation for k0, assumes k90 = 1, e=0. This is a sphere, so no flattening

                lsm_prj_str = ('PROJCS["Sphere_Stereographic",'
                               'GEOGCS["GCS_Sphere",'
                               'DATUM["D_Sphere",'
                               'SPHEROID["Sphere",6370000.0,0.0]],'
                               'PRIMEM["Greenwich",0.0],'
                               'UNIT["Degree",0.0174532925199433]],'
                               'PROJECTION["Stereographic"],'
                               'PARAMETER["False_Easting",0.0],'
                               'PARAMETER["False_Northing",0.0],'
                               'PARAMETER["Central_Meridian",{0}],'
                               'PARAMETER["Scale_Factor",{1}],'
                               'PARAMETER["Latitude_Of_Origin",{2}],'
                               'UNIT["Meter",1.0]]').format(central_meridian, 
                                                            central_scale_factor, 
                                                            standard_parallel_1)

                lsm_srs=osr.SpatialReference()
                lsm_srs.ImportFromWkt(lsm_prj_str)
                self.lsm_proj4 = Proj(lsm_srs.ExportToProj4())
            elif map_proj == 3:
                # Mercator Projection
                lsm_prj_str = ('ESRI::PROJCS["Sphere_Mercator",'
                               'GEOGCS["GCS_Sphere",'
                               'DATUM["D_Sphere",'
                               'SPHEROID["Sphere",6370000.0,0.0]],'
                               'PRIMEM["Greenwich",0.0],'
                               'UNIT["Degree",0.0174532925199433]],'
                               'PROJECTION["Mercator"],'
                               'PARAMETER["False_Easting",0.0],'
                               'PARAMETER["False_Northing",0.0],'
                               'PARAMETER["Central_Meridian",{0}],'
                               'PARAMETER["Standard_Parallel_1",{1}],'
                               'UNIT["Meter",1.0],AUTHORITY["ESRI",53004]]').format(central_meridian,
                                                                                    standard_parallel_1)
                lsm_srs=osr.SpatialReference()
                lsm_srs.ImportFromWkt(lsm_prj_str)
                self.lsm_proj4 = Proj(lsm_srs.ExportToProj4())
            elif map_proj == 6:
                # Cylindrical Equidistant (or Rotated Pole)
                # Check units (linear unit not used in this projection).  GCS?
                lsm_prj_str = ('ESRI::PROJCS["Sphere_Equidistant_Cylindrical",'
                               'GEOGCS["GCS_Sphere",'
                               'DATUM["D_Sphere",'
                               'SPHEROID["Sphere",6370000.0,0.0]],'
                               'PRIMEM["Greenwich",0.0],'
                               'UNIT["Degree",0.0174532925199433]],'
                               'PROJECTION["Equidistant_Cylindrical"],'
                               'PARAMETER["False_Easting",0.0],'
                               'PARAMETER["False_Northing",0.0],'
                               'PARAMETER["Central_Meridian",{0}],'
                               'PARAMETER["Standard_Parallel_1",{1}],'
                               'UNIT["Meter",1.0],AUTHORITY["ESRI",53002]]').format(central_meridian,
                                                                                    standard_parallel_1)
        
                lsm_srs=osr.SpatialReference()
                lsm_srs.ImportFromWkt(lsm_prj_str)
                self.lsm_proj4 = Proj(lsm_srs.ExportToProj4())
        else:
            raise IndexError("Invalid mode to retrieve LSM projection ...")
            
    def _get_lsm_lon_lat_list(self):
        """
        This retrieves the list of longitudes and latitudes
        in the LSM grid projection
        """
        if self.lsm_grid_type=='geographic':
            lsm_nc = Dataset(self.lsm_nc_list[0])
            lsm_lon = lsm_nc.variables[self.lsm_lon_var][:] #assume [-180, 180]
            lsm_lat = lsm_nc.variables[self.lsm_lat_var][:] #assume [-90,90]
            lsm_nc.close()
            
            #convert 3d to 2d if time dimension
            if(len(lsm_lon.shape) == 3):
                lsm_lon = lsm_lon[0]
                lsm_lat = lsm_lat[0]
                
        elif self.lsm_grid_type=='wrf':
            #generate grid from information
            lsm_nc = Dataset(self.lsm_nc_list[0])

            #METHOD 1: USE CORNER LATS/LONS FROM METADATA
            #LOWER LEFT CELL CENTER FROM LOWER LEFT CORNER
            #map_projection = getattr(lsm_nc, "MAP_PROJECTION")
            #south_west_corner_lat = getattr(lsm_nc, "SOUTH_WEST_CORNER_LAT")
            #south_west_corner_lon = getattr(lsm_nc, "SOUTH_WEST_CORNER_LON")
            """
            x_min, y_min = transform(Proj(init='epsg:4326'),
                                     self.lsm_proj4,
                                     [float(lsm_nc.__dict__['corner_lons'][0])],
                                     [float(lsm_nc.__dict__['corner_lats'][0])], 
                                     )
            DX = float(lsm_nc.__dict__['DX'])
            DY = float(lsm_nc.__dict__['DY'])
            min_lon_cell_center = x_min[0]+DX/2.0
            min_lat_cell_center = y_min[0]+DY/2.0

            size_xdim = len(lsm_nc.dimensions['west_east'])
            size_ydim = len(lsm_nc.dimensions['south_north'])
            lsm_lon = np.array([min_lon_cell_center + DX*i_x for i_x in range(size_xdim)])
            lsm_lat = np.array([min_lat_cell_center + DX*i_y for i_y in range(size_ydim)])
            """
            #METHOD 2: USE LAT/LON FROM LSM
            lsm_lon, lsm_lat = transform(Proj(init='epsg:4326'),
                                         self.lsm_proj4,
                                         lsm_nc.variables[self.lsm_lon_var][:],
                                         lsm_nc.variables[self.lsm_lat_var][:], 
                                         )
            #convert 3d to 2d if time dimension
            if(len(lsm_lon.shape) == 3):
                lsm_lon = lsm_lon[0]
                lsm_lat = lsm_lat[0]
            
        else:
            raise IndexError("Invalid mode to retrieve LSM Lat/Lon lists ...")
        
        return lsm_lon, lsm_lat
        
    def _load_gssha_and_lsm_extent(self):
        """
        #Get extent from GSSHA Grid in Geographic coordinates
        #Determine range within LSM Grid
        """
        ####
        #STEP 1: Get extent from GSSHA Grid in LSM coordinates
        ####
        gssha_grid_path = path.join(self.gssha_project_folder,
                                    self.gssha_grid_file_name)
                                    
        gssha_grid = gdal.Open(gssha_grid_path)
        gssha_srs=osr.SpatialReference()
        #The projection file is named DIFFERENT as it is stored in the .PRO
        #file in the GSSHA folder. This searched for the file.
        gssha_projection_file_path = "{0}.pro".format(path.splitext(gssha_grid_path)[0])
        if not gssha_projection_file_path or not path.exists(gssha_projection_file_path):
            gssha_projection_file_list = glob(path.join(self.gssha_project_folder, "*.pro"))
            if len(gssha_projection_file_list) > 0:
                gssha_projection_file_path = gssha_projection_file_list[0]
                if len(gssha_projection_file_list) > 1:
                    print("WARNING: Multiple GSSHA .pro files found. \n" \
                          " To ensure that the correct .pro file is found, " \
                          "only place one .pro file in the GSSHA directory. \n" \
                          "Using: {}".format(gssha_projection_file_path))
            else:
                raise IndexError("GSSHA .pro file not found ...")
                
        with open(gssha_projection_file_path) as pro_file:
            self.gssha_prj_str = pro_file.read()
            gssha_srs.ImportFromWkt(self.gssha_prj_str)
            self.gssha_proj4 = Proj(gssha_srs.ExportToProj4())
        
        #get projection from LSM file (ASSUME GEOGRAPHIC IF LAT/LON)
        self._load_lsm_projection()

        min_x, xres, xskew, max_y, yskew, yres  = gssha_grid.GetGeoTransform()
        max_x = min_x + (gssha_grid.RasterXSize * xres)
        min_y = max_y + (gssha_grid.RasterYSize * yres)
        x_ext, y_ext = transform(self.gssha_proj4,
                                 self.lsm_proj4,
                                 [min_x, max_x, min_x, max_x],
                                 [min_y, max_y, max_y, min_y], 
                                 )
        
        gssha_y_min = min(y_ext)
        gssha_y_max = max(y_ext)
        gssha_x_min = min(x_ext)
        gssha_x_max = max(x_ext)

        ######
        #STEP 2: Determine range within LSM Grid
        ######
        lsm_lon_array, lsm_lat_array = self._get_lsm_lon_lat_list()

        #get general buffer size
        lsm_dx = None
        lsm_dy = None
        if self.lsm_grid_type=='wrf':
            try:
                lsm_nc = Dataset(self.lsm_nc_list[0])
                lsm_dx = getattr(lsm_nc, "DX")
                lsm_dy = getattr(lsm_nc, "DY")
                lsm_nc.close()
            except AttributeError:
                lsm_nc.close()
                pass

        if lsm_dx is None:
            lsm_dx = np.max(np.absolute(np.diff(lsm_lon_array)))
        
        # Extract the lat and lon within buffered extent
        #IF LAT LON IS !D:
        if len(lsm_lat_array.shape) == 1:
            if lsm_dy is None:
                lsm_dy = np.max(np.absolute(np.diff(lsm_lat_array)))

            self.lsm_lat_indices = np.where((lsm_lat_array >= (gssha_y_min - lsm_dy)) & (lsm_lat_array <= (gssha_y_max + lsm_dy)))[0]
            self.lsm_lon_indices = np.where((lsm_lon_array >= (gssha_x_min - lsm_dx)) & (lsm_lon_array <= (gssha_x_max + lsm_dx)))[0]

            lsm_lon_list, lsm_lat_list = np.meshgrid(lsm_lon_array[self.lsm_lon_indices], lsm_lat_array[self.lsm_lat_indices])
        #IF LAT LON IS 2D:
        elif len(lsm_lat_array.shape) == 2:
            if lsm_dy is None:
                lsm_dy = np.max(np.absolute(np.diff(lsm_lat_array, axis=0)))
            lsm_lat_indices_from_lat, lsm_lon_indices_from_lat = np.where((lsm_lat_array >= (gssha_y_min - lsm_dy)) & (lsm_lat_array <= (gssha_y_max + lsm_dy)))
            lsm_lat_indices_from_lon, lsm_lon_indices_from_lon = np.where((lsm_lon_array >= (gssha_x_min - lsm_dx)) & (lsm_lon_array <= (gssha_x_max + lsm_dx)))

            self.lsm_lat_indices = np.intersect1d(lsm_lat_indices_from_lat, lsm_lat_indices_from_lon)
            self.lsm_lon_indices = np.intersect1d(lsm_lon_indices_from_lat, lsm_lon_indices_from_lon)

            lsm_lat_list = lsm_lat_array[self.lsm_lat_indices,:][:,self.lsm_lon_indices]
            lsm_lon_list = lsm_lon_array[self.lsm_lat_indices,:][:,self.lsm_lon_indices]
            
        else:
            raise IndexError("Only 1D & 2D lat lon dimensions supported ...")
        
        
        self.proj_lon_list, self.proj_lat_list = transform(self.lsm_proj4,
                                                           self.gssha_proj4,
                                                           lsm_lon_list,
                                                           lsm_lat_list, 
                                                           )
                                                 
        #GET BOUNDS BASED ON AVERAGE (NOTE: LAT IS REVERSED)
        #https://grass.osgeo.org/grass64/manuals/r.in.ascii.html
        dy_n_avg = np.mean(np.absolute(self.proj_lat_list[-1] - self.proj_lat_list[-2]))
        dy_s_avg = np.mean(np.absolute(self.proj_lat_list[1] - self.proj_lat_list[0]))
        dx_e_avg = np.mean(np.absolute(self.proj_lon_list[:,-2] - self.proj_lon_list[:,-1]))
        dx_w_avg = np.mean(np.absolute(self.proj_lon_list[:,0] - self.proj_lon_list[:,1]))
                                          
        self.north_bound = np.mean(self.proj_lat_list[-1])+dy_n_avg/2.0
        self.south_bound = np.mean(self.proj_lat_list[0])-dy_s_avg/2.0
        self.east_bound = np.mean(self.proj_lon_list[:,-1])+dx_e_avg/2.0
        self.west_bound = np.mean(self.proj_lon_list[:,0])-dx_w_avg/2.0
        self.cell_size = np.mean([dy_n_avg,dy_s_avg,dx_e_avg,dx_w_avg])

    def _load_sorted_lsm_list_and_time(self):
        """
        Loads in the sorted lsm list and sorted time
        """
        self.lsm_nc_list = np.array(glob(path.join(self.lsm_input_folder_path, self.lsm_search_card)), dtype=str)
        time_array = np.zeros(len(self.lsm_nc_list))
        
        epoch = datetime.utcfromtimestamp(0)
        
        if self.lsm_file_date_naming_convention is not None:
            #METHOD 1: LOAD FROM TIME STRING IN FILES
            for lsm_idx, lsm_nc_file in enumerate(self.lsm_nc_list):
                time_array[lsm_idx] = (datetime.strptime(path.basename(lsm_nc_file),self.lsm_file_date_naming_convention)-epoch).total_seconds()
        else:
            #METHOD 2: LOAD FROM TIME IN NETCDF FILE
            lsm_nc = Dataset(self.lsm_nc_list[0])
            #GET TIME CONVERSION TO SECONDS
            time_info = lsm_nc.variables[self.lsm_time_var].getncattr("units").strip()
            time_units, time_start = time_info.split('since')
            convert_to_seconds = 1
            if 'day' in time_units.lower():
                convert_to_seconds = 24*3600
            elif 'hour' in time_units.lower():
                convert_to_seconds = 3600
            elif 'minute' in time_units.lower():
                convert_to_seconds = 60
            elif 'second' in time_units.lower():
                convert_to_seconds = 1
            else:
                raise IndexError("Unexpected time units: {0} ...".format(time_units))

            
            for lsm_idx, lsm_nc_file in enumerate(self.lsm_nc_list):
                lsm_nc = Dataset(lsm_nc_file)
                #GET TIME IN SECONDS SINCE EPOCH
                time_info = lsm_nc.variables[self.lsm_time_var].getncattr("units").strip()
                time_units, time_start = time_info.split('since')
                datetime_start = parser.parse(time_start)
                lsm_time = lsm_nc.variables[self.lsm_time_var][0]
                time_array[lsm_idx] = (datetime_start+timedelta(seconds=lsm_time*convert_to_seconds)-epoch).total_seconds()
                lsm_nc.close()
        
        #SORT BY TIME
        sorted_indices = np.argsort(time_array)
        self.time_array = time_array[sorted_indices]
        self.lsm_nc_list = self.lsm_nc_list[sorted_indices]
        
        #GET TIME STEP
        if self.time_step_seconds is None:
            try:
                lsm_nc = Dataset(self.lsm_nc_list[0])
                lsm_time = lsm_nc.variables[self.lsm_time_var]
                self.time_step_seconds = int(lsm_time.getncattr("time_increment")) * convert_to_seconds
                lsm_nc.close()
            except (IndexError, KeyError):
                lsm_nc.close()
                try:
                    self.time_step_seconds = self.time_array[1] - self.time_array[0]
                except IndexError:
                    raise IndexError("ERROR: Time delta not found. Please set time_step_seconds" \
                                     " in the LSMtoGSSHA class initialization.")

        #GET HOURLY TIME STEPS
        self.hourly_time_index_array = None
        idx = 0
        current_datetime = datetime.utcfromtimestamp(self.time_array[0])
        self.hourly_time_index_array = [0]
        for time_sec in self.time_array:
            var_datetime = datetime.utcfromtimestamp(time_sec)
            if current_datetime.hour != var_datetime.hour:
                 self.hourly_time_index_array.append(idx)
            current_datetime = var_datetime
            idx += 1
            
        self.num_generated_files_per_timestep = 1
        if self.time_step_seconds > 3600:
            self.num_generated_files_per_timestep = self.time_step_seconds/3600.0
        
        self.len_hourly_time_index_array = len(self.hourly_time_index_array)
        self.hourly_time_array = np.zeros(self.len_hourly_time_index_array*int(self.num_generated_files_per_timestep))
        for hourly_index, time_index in enumerate(self.hourly_time_index_array):
            for i in range(int(self.num_generated_files_per_timestep)):
                self.hourly_time_array[(hourly_index*int(self.num_generated_files_per_timestep)+i)] = self.time_array[time_index]+3600*i
 


    def _time_to_string(self, time_int, conversion_string="%Y %m %d %H %M"):
        """
        This converts a UTC time integer to a string
        """
        return time.strftime(conversion_string, time.gmtime(time_int))
        
    def _load_lsm_data(self, data_var, conversion_factor=1, four_dim_var_calc_method=None):
        """
        This extracts the LSM data from a folder of netcdf files
        """
        self.data_np_array = np.zeros((len(self.lsm_nc_list),
                                       len(self.lsm_lat_indices), 
                                       len(self.lsm_lon_indices)))
        
        for lsm_idx, lsm_nc_file in enumerate(self.lsm_nc_list):
            lsm_nc = Dataset(lsm_nc_file)
            #EXTRACT DATA WITHIN EXTENT
            if four_dim_var_calc_method is None:
                self.data_np_array[lsm_idx] = lsm_nc.variables[data_var][0, self.lsm_lat_indices, self.lsm_lon_indices]*conversion_factor
            else:
                self.data_np_array[lsm_idx] = four_dim_var_calc_method(lsm_nc.variables[data_var][0, :, self.lsm_lat_indices, self.lsm_lon_indices]*conversion_factor, axis=0)
            lsm_nc.close()
        
    
    def _load_converted_gssha_data_from_lsm(self, gssha_var, lsm_var, load_type):
        """
        This function loads data from LSM and converts to GSSHA format
        """
        if 'radiation' in gssha_var:
            if gssha_var == 'direct_radiation' and not isinstance(lsm_var, basestring):
                #direct_radiation = (1-DIFFUSIVE_FRACION)*global_radiation
                global_radiation_var, diffusive_fraction_var = lsm_var
                self._load_lsm_data(global_radiation_var)
                global_radiation = self.data_np_array
                self._load_lsm_data(diffusive_fraction_var)
                diffusive_fraction = self.data_np_array
                self.data_np_array = (1-diffusive_fraction)*global_radiation*self.time_step_seconds/3600.0
            elif gssha_var == 'diffusive_radiation' and not isinstance(lsm_var, basestring):
                #diffusive_radiation = DIFFUSIVE_FRACION*global_radiation
                global_radiation_var, diffusive_fraction_var = lsm_var
                self._load_lsm_data(global_radiation_var)
                global_radiation = self.data_np_array
                self._load_lsm_data(diffusive_fraction_var)
                diffusive_fraction = self.data_np_array
                self.data_np_array = diffusive_fraction*global_radiation*self.time_step_seconds/3600.0
            elif isinstance(lsm_var, basestring):
                self._load_lsm_data(lsm_var, self.netcdf_attributes[gssha_var]['conversion_factor'][load_type])
                self.data_np_array = self.data_np_array*self.time_step_seconds/3600.0
            else:
                raise IndexError("Invalid LSM variable ({0}) for GSSHA variable {1}".format(lsm_var, gssha_var))
                
        elif gssha_var == 'relative_humidity' and not isinstance(lsm_var, basestring):
            ##CONVERSION ASSUMPTIONS:
            ##1) These equations are for liquid water and are less accurate below 0 deg C
            ##2) Not adjusting the pressure for the fact that the temperature
            ##   and moisture measurements are given at 2 m AGL.
            
            ##Neither of these should have a significant impact on RH values
            ##given the uncertainty in the model values themselves.

            specific_humidity_var, pressure_var, temperature_var = lsm_var
            self._load_lsm_data(specific_humidity_var)
            specific_humidity_array = self.data_np_array
            self._load_lsm_data(pressure_var)
            pressure_array = self.data_np_array
            self._load_lsm_data(temperature_var)
            temperature_array = self.data_np_array

            ##METHOD 1:
            ##To compute the relative humidity at 2m,
            ##given T and Q (water vapor mixing ratio) at 2 m and PSFC (surface pressure):
            ##Es(saturation vapor pressure in Pa)=611.2*exp(17.62*(T2-273.16)/(243.12+T2-273.16))
            ##Qs(saturation mixing ratio)=(0.622*es)/(PSFC-es)
            ##RH = 100*Q/Qs

            es_array = 611.2*np.exp(17.62*(temperature_array-273.16)/(243.12+temperature_array-273.16))
            self.data_np_array = 100 * specific_humidity_array/((0.622*es_array)/(pressure_array-es_array))
            
            ##METHOD 2:
            ##http://earthscience.stackexchange.com/questions/2360/how-do-i-convert-specific-humidity-to-relative-humidity
            #pressure in Pa, temperature in K
            ##self.data_np_array = 0.263*pressure_array*specific_humidity_array/np.exp(17.67*(temperature_array-273.16)/(temperature_array-29.65))
            
        elif gssha_var == 'wind_speed' and not isinstance(lsm_var, basestring):
            # WRF:  http://www.meteo.unican.es/wiki/cordexwrf/OutputVariables
            u_vector_var, v_vector_var = lsm_var
            conversion_factor = self.netcdf_attributes[gssha_var]['conversion_factor'][load_type]
            self._load_lsm_data(u_vector_var, conversion_factor)
            u_vector_array = self.data_np_array
            self._load_lsm_data(v_vector_var, conversion_factor)
            v_vector_array = self.data_np_array
            self.data_np_array = np.sqrt(u_vector_array**2 + v_vector_array**2)
        elif 'precipitation' in gssha_var and not isinstance(lsm_var, basestring):
            # WRF:  http://www.meteo.unican.es/wiki/cordexwrf/OutputVariables
            rain_c_var, rain_nc_var = lsm_var
            conversion_factor = self.netcdf_attributes[gssha_var]['conversion_factor'][load_type]
            self._load_lsm_data(rain_c_var, conversion_factor)
            rain_c_array = self.data_np_array
            self._load_lsm_data(rain_nc_var, conversion_factor)
            rain_nc_array = self.data_np_array
            self.data_np_array = rain_c_array + rain_nc_array
        else:
            self._load_lsm_data(lsm_var, 
                                self.netcdf_attributes[gssha_var]['conversion_factor'][load_type],
                                self.netcdf_attributes[gssha_var].get('four_dim_var_calc_method'))
                                
            conversion_function = self.netcdf_attributes[gssha_var].get('conversion_function')
            if conversion_function:
                self.data_np_array = self.netcdf_attributes[gssha_var]['conversion_function'][load_type](self.data_np_array)

        if load_type == 'ascii' or load_type == 'netcdf':
            #CONVERT TO INCREMENTAL
            if gssha_var == 'precipitation_acc':
                self.data_np_array = np.lib.pad(np.diff(self.data_np_array, axis=0),
                                                ((1,0),(0,0),(0,0)),'constant',constant_values=0)
                
            #CONVERT PRECIP TO RADAR (mm/hr) IN FILE
            if gssha_var == 'precipitation_inc' or gssha_var == 'precipitation_acc':
                #convert to mm/hr from mm
                self.data_np_array = self.data_np_array*3600/float(self.time_step_seconds)

                
                
    def _check_lsm_input(self, data_var_map_array):
        """
        This function checks the input var map array
        to ensure the required input variables exist
        """
        REQUIRED_HMET_VAR_LIST = ['Prcp', 'Pres', 'Temp', 'Clod', 'RlHm', 'DRad', 'GRad', 'WndS']
        
        #make sure all required variables exist
        given_hmet_var_list = []
        for data_var_map in data_var_map_array:
            gssha_data_var, lsm_data_var = data_var_map
            gssha_data_hmet_name = self.netcdf_attributes[gssha_data_var]['hmet_name']

            if gssha_data_hmet_name in given_hmet_var_list:
                raise IndexError("Duplicate parameter for HMET variable {0}".format(gssha_data_hmet_name))
            else:
                given_hmet_var_list.append(gssha_data_hmet_name)

        for REQUIRED_HMET_VAR in REQUIRED_HMET_VAR_LIST:
            if REQUIRED_HMET_VAR not in given_hmet_var_list:
                raise Exception("ERROR: HMET param is required to continue {0} ...".format(REQUIRED_HMET_VAR))
            
    def _get_calc_function(self, gssha_data_var):
        """
        This retrives the calc function to convert
        to hourly data for the various HMET parameters
        """
        calc_function = np.mean
        if gssha_data_var == 'precipitation_inc' or gssha_data_var == 'precipitation_acc':
            calc_function = np.sum
            
        return calc_function
       
    def _get_hourly_data(self, hourly_index, calc_function):
        """
        This function gets the data converted into
        hourly data for ASCII or NetCDF output files
        """
        time_index_start = self.hourly_time_index_array[hourly_index]
        if hourly_index+1 < self.len_hourly_time_index_array:
            next_time_index = self.hourly_time_index_array[hourly_index+1]
            return calc_function(self.data_np_array[time_index_start:next_time_index,::-1,:], axis=0)
        elif hourly_index+1 == self.len_hourly_time_index_array:
            if time_index_start < len(self.time_array) - 1:
                return calc_function(self.data_np_array[time_index_start:,::-1,:], axis=0)
            else:
                return self.data_np_array[time_index_start,::-1,:]
                
    def _convert_data_to_hourly(self, gssha_data_var):
        """
        This function converts the data to hourly data
        and then puts it into the data_np_array
        """
        hourly_3d_array = np.zeros((self.len_hourly_time_index_array*int(self.num_generated_files_per_timestep), len(self.lsm_lat_indices), len(self.lsm_lon_indices)))
        calc_function = self._get_calc_function(gssha_data_var)
        
        for hourly_index in xrange(self.len_hourly_time_index_array):
            for i in xrange(int(self.num_generated_files_per_timestep)):
                hourly_3d_array[hourly_index*int(self.num_generated_files_per_timestep)+i,:,:] = self._get_hourly_data(hourly_index, calc_function)
        
        self.data_np_array = hourly_3d_array
        
    def lsm_precip_to_gssha_precip_gage(self, out_gage_file, lsm_data_var, precip_type="RADAR"):
        """This function takes array data and writes out a GSSHA precip gage file.
        See: http://www.gsshawiki.com/Precipitation:Spatially_and_Temporally_Varied_Precipitation
        
        .. note::
            GSSHA CARDS: 
                * PRECIP_FILE card with path to gage file 
                * RAIN_INV_DISTANCE or RAIN_THIESSEN
        
        Parameters:
            out_gage_file(str): Location of gage file to generate.
            lsm_data_var(str or list): This is the variable name for precipitation in the LSM files.
                                          If there is a string, it assumes a single variable. If it is a
                                          list, then it assumes the first element is the variable name for
                                          RAINC and the second is for RAINNC 
                                          (see: http://www.meteo.unican.es/wiki/cordexwrf/OutputVariables).
            precip_type(Optional[str]): This tells if the data is the ACCUM, RADAR, or GAGES data type. Default is 'RADAR'.
            
        Example::

            #STEP 1: Initialize class
            l2g = LSMtoGSSHA(
                             #YOUR INIT PARAMETERS HERE
                            )
    
            #OPTION 1: One precip variable to precip gage data.
            l2g.lsm_precip_to_gssha_precip_gage(out_gage_file="E:\GSSHA\wrf_gage_1.gag",
                                                lsm_data_var=['RAINC', 'RAINNC'],
                                                precip_type='ACCUM')

            #OPTION 2: Two precip variables to precip gage data.
            l2g.lsm_precip_to_gssha_precip_gage(out_gage_file="E:\GSSHA\wrf_gage_2.gag",
                                                lsm_data_var='Rainf_tavg',
                                                precip_type='GAGES')

        """
        VALID_TYPES = ["ACCUM", "RADAR", "GAGES"] #NOTE: "RATES" currently not supported
        if precip_type not in VALID_TYPES:
            raise IndexError("ERROR: {0} is not a valid type. Valid types include: {1}".format(type, VALID_TYPES))

        gssha_precip_type = "precipitation_inc"
        if precip_type == "ACCUM":
            gssha_precip_type = "precipitation_acc"
        elif precip_type == "RADAR":
            gssha_precip_type = "precipitation_rate"
        
        self._load_converted_gssha_data_from_lsm(gssha_precip_type, lsm_data_var, 'gage')
        
        if len(self.data_np_array.shape) > 2:
            #LOOP THROUGH TIME
            with io_open(out_gage_file, 'w', newline=self.default_line_ending ) as gage_file:
                if len(self.time_array)>1:
                    gage_file.write(u"EVENT \"Event of {0} to {1}\"\n".format(self._time_to_string(self.time_array[0]),
                                                                             self._time_to_string(self.time_array[-1])))
                else:
                    gage_file.write(u"EVENT \"Event of {0}\"\n".format(self._time_to_string(self.time_array[0])))
                gage_file.write(u"NRPDS {0}\n".format(self.data_np_array.shape[0]))
                gage_file.write(u"NRGAG {0}\n".format(self.data_np_array.shape[1]*self.data_np_array.shape[2]))

                for lat_idx in range(len(self.lsm_lat_indices)):
                    for lon_idx in range(len(self.lsm_lon_indices)):
                        coord_idx = lat_idx*len(self.lsm_lon_indices) + lon_idx
                        gage_file.write(u"COORD {0} {1} \"center of pixel #{2}\"\n".format(self.proj_lon_list[lat_idx,lon_idx],
                                                                                          self.proj_lat_list[lat_idx,lon_idx], 
                                                                                          coord_idx))
                for time_idx, time_step_array in enumerate(self.data_np_array):
                    date_str = self._time_to_string(self.time_array[time_idx])
                    data_str = " ".join(time_step_array.ravel().astype(str))
                    gage_file.write(u"{0} {1} {2}\n".format(precip_type, date_str, data_str))
                    
        elif len(self.data_np_array.shape) == 2:
            with io_open(out_gage_file, 'w', newline=self.default_line_ending ) as gage_file:
                date_str = self._time_to_string(self.time_array[0])
                gage_file.write(u"EVENT \"Event of {0}\"\n".format(date_str))
                gage_file.write(u"NRPDS 1\n")
                gage_file.write(u"NRGAG {0}\n".format(self.data_np_array.shape[0]*self.data_np_array.shape[1]))
                for lat_idx in range(len(self.lsm_lat_indices)):
                    for lon_idx in range(len(self.lsm_lon_indices)):
                        coord_idx = lat_idx*len(self.lsm_lon_indices) + lon_idx
                        gage_file.write(u"COORD {0} {1} \"center of pixel #{2}\"\n".format(self.proj_lon_list[lat_idx,lon_idx],
                                                                                          self.proj_lat_list[lat_idx,lon_idx], 
                                                                                          coord_idx))
                data_str = " ".join(time_step_array.ravel().astype(str))
                gage_file.write(u"{0} {1} {2}\n".format(precip_type, date_str, data_str))
        else:
            raise Exception("Invalid data array ...")
            
    def _write_hmet_card_file(self, hmet_card_file_path, main_output_folder):
        """
        This function writes the HMET_ASCII card file 
        with ASCII file list for input to GSSHA
        """
        with io_open(hmet_card_file_path, 'w', newline=self.default_line_ending ) as out_hmet_list_file:
            for hour_time in self.hourly_time_array:
                date_str = self._time_to_string(hour_time, "%Y%m%d%H")
                out_hmet_list_file.write(u"{0}\n".format(path.join(main_output_folder, date_str)))
 
    def _lsm_data_to_ascii(self, header_string,
                                 data_var_map_array, 
                                 main_output_folder="",
                                 hmet_card_file=""):
        """
        Writes extracted data to ASCII file format
        required for GSSHA to read it in
        GSSHA CARD: HMET_ASCII
        NOTE: MUST HAVE LONG_TERM GSSHA CARD TO WORK
        See: http://www.gsshawiki.com/Long-term_Simulations:Global_parameters
        
        """
        self._check_lsm_input(data_var_map_array)
        
        if not main_output_folder:
            main_output_folder = path.join(self.gssha_project_folder, "hmet_ascii_data")
            
        try:
            mkdir(main_output_folder)
        except OSError:
            pass
        
        print("Outputting HMET data to {0}".format(main_output_folder))
        
        #the csv module line ending behaves different than io.open in python 2.7 than 3
        csv_newline = '\r\n' #this is the case where we want windows style ending
        if self.output_unix_format:
            csv_newline = '\n'
            
        #PART 2: DATA
        for data_var_map in data_var_map_array:
            gssha_data_var, lsm_data_var = data_var_map
            gssha_data_hmet_name = self.netcdf_attributes[gssha_data_var]['hmet_name']
            self._load_converted_gssha_data_from_lsm(gssha_data_var, lsm_data_var, 'ascii')
            if len(self.data_np_array.shape) == 3:
                self._convert_data_to_hourly(gssha_data_var)
                    
                for hourly_index, hour_time in enumerate(self.hourly_time_array):
                    date_str = self._time_to_string(hour_time, "%Y%m%d%H")
                    ascii_file_path = path.join(main_output_folder,"{0}_{1}.asc".format(date_str, gssha_data_hmet_name))
                    with open(ascii_file_path, 'wb') as out_ascii_grid:
                        out_ascii_grid.write(unicode(header_string))
                        grid_writer = csv_writer(out_ascii_grid, 
                                                 delimiter=" ", 
                                                 lineterminator=csv_newline)
                        grid_writer.writerows(self.data_np_array[hourly_index])
            else:
                raise Exception("Invalid data array ...")

        #PART 3: HMET_ASCII card input file with ASCII file list
        hmet_card_file_path = path.join(main_output_folder, 'hmet_file_list.txt')
        self._write_hmet_card_file(hmet_card_file_path, main_output_folder)
    
    def lsm_data_to_grass_ascii(self, data_var_map_array, 
                                      main_output_folder=""):
        """
        Writes extracted data to GRASS ASCII file format
        DO NOT USE THIS!!!!! IT WILL NOT WORK!!!!
        """
        #PART 1: HEADER
        #get data extremes
        header_string = "north: {0}\n".format(self.north_bound)
        header_string += "south: {0}\n".format(self.south_bound)
        header_string += "east: {0}\n".format(self.east_bound)
        header_string += "west: {0}\n".format(self.west_bound)
        header_string += "rows: {0}\n".format(len(self.lsm_lat_indices))
        header_string += "cols: {0}\n".format(len(self.lsm_lon_indices))
        header_string += "NODATA_value -9999\n"

        #PART 2: DATA
        self._lsm_data_to_ascii(header_string,
                                data_var_map_array, 
                                main_output_folder)
            
    def lsm_data_to_arc_ascii(self, data_var_map_array, 
                                    main_output_folder=""):
        """Writes extracted data to Arc ASCII file format into folder
        to be read in by GSSHA. Also generates the HMET_ASCII card file
        for GSSHA in the folder named 'hmet_file_list.txt'.
        
        .. warning:: For GSSHA 6 Versions, for GSSHA 7 or greater, use lsm_data_to_subset_netcdf.

        .. note::
            GSSHA CARDS:
                * HMET_ASCII pointing to the hmet_file_list.txt
                * LONG_TERM (see: http://www.gsshawiki.com/Long-term_Simulations:Global_parameters)
       
        Parameters:
            data_var_map_array(list): Array to map the variables in the LSM file to the 
                                      matching required GSSHA data.
            main_output_folder(Optional[str]): This is the path to place the generated ASCII files. 
                                        If not included, it defaults to 
                                        os.path.join(self.gssha_project_folder, "hmet_ascii_data").
            
        Example::
        
            #STEP 1: Initialize class
            l2g = LSMtoGSSHA(
                             #YOUR INIT PARAMETERS HERE
                            )
    
            #STEP 2: Generate ASCII DATA
            #EXAMPLE DATA ARRAY 1: WRF GRID DATA BASED
            #SEE: http://www.meteo.unican.es/wiki/cordexwrf/OutputVariables
            
            data_var_map_array = [
                                  ['precipitation_acc', ['RAINC', 'RAINNC']], 
                                  ['pressure', 'PSFC'], 
                                  ['relative_humidity', ['Q2', 'PSFC', 'T2']], #MUST BE IN ORDER: ['SPECIFIC HUMIDITY', 'PRESSURE', 'TEMPERATURE']
                                  ['wind_speed', ['U10', 'V10']], #['U_VELOCITY', 'V_VELOCITY']
                                  ['direct_radiation', ['SWDOWN', 'DIFFUSE_FRAC']], #MUST BE IN ORDER: ['GLOBAL RADIATION', 'DIFFUSIVE FRACTION']
                                  ['diffusive_radiation', ['SWDOWN', 'DIFFUSE_FRAC']], #MUST BE IN ORDER: ['GLOBAL RADIATION', 'DIFFUSIVE FRACTION']
                                  ['temperature', 'T2'],
                                  ['cloud_cover' , 'CLDFRA'], #'CLOUD_FRACTION'
                                 ]
                                 
            l2g.lsm_data_to_arc_ascii(data_var_map_array)
            
        """
        #PART 1: HEADER
        #get data extremes
        header_string = "ncols {0}\n".format(len(self.lsm_lon_indices))
        header_string += "nrows {0}\n".format(len(self.lsm_lat_indices))
        header_string += "xllcorner {0}\n".format(self.west_bound)
        header_string += "yllcorner {0}\n".format(self.south_bound)
        header_string += "cellsize {0}\n".format(self.cell_size)
        header_string += "NODATA_value -9999\n"

        #PART 2: DATA
        self._lsm_data_to_ascii(header_string,
                                data_var_map_array, 
                                main_output_folder)
    
    def lsm_data_to_subset_netcdf(self, netcdf_file_path, data_var_map_array):
        """Writes extracted data to the NetCDF file format 
        
        .. warning:: The NetCDF GSSHA file is only supported in GSSHA 7 or greater.

        .. note::
            GSSHA CARDS:
                * HMET_NETCDF pointing to the netcdf_file_path
                * LONG_TERM (see: http://www.gsshawiki.com/Long-term_Simulations:Global_parameters)
        
        Parameters:
            netcdf_file_path(string): Path to output the NetCDF file for GSSHA.
            data_var_map_array(list): Array to map the variables in the LSM file to the 
                                      matching required GSSHA data.
            
        Example::
        
            #STEP 1: Initialize class
            l2g = LSMtoGSSHA(
                             #YOUR INIT PARAMETERS HERE
                            )
    
            #STEP 2: Generate ASCII DATA
            #EXAMPLE DATA ARRAY 1: WRF GRID DATA BASED
            #SEE: http://www.meteo.unican.es/wiki/cordexwrf/OutputVariables
            
            data_var_map_array = [
                                  ['precipitation_acc', ['RAINC', 'RAINNC']], 
                                  ['pressure', 'PSFC'], 
                                  ['relative_humidity', ['Q2', 'PSFC', 'T2']], #MUST BE IN ORDER: ['SPECIFIC HUMIDITY', 'PRESSURE', 'TEMPERATURE']
                                  ['wind_speed', ['U10', 'V10']], #['U_VELOCITY', 'V_VELOCITY']
                                  ['direct_radiation', ['SWDOWN', 'DIFFUSE_FRAC']], #MUST BE IN ORDER: ['GLOBAL RADIATION', 'DIFFUSIVE FRACTION']
                                  ['diffusive_radiation', ['SWDOWN', 'DIFFUSE_FRAC']], #MUST BE IN ORDER: ['GLOBAL RADIATION', 'DIFFUSIVE FRACTION']
                                  ['temperature', 'T2'],
                                  ['cloud_cover' , 'CLDFRA'], #'CLOUD_FRACTION'
                                 ]
                                 
            l2g.lsm_data_to_subset_netcdf("E:\GSSHA\gssha_wrf_data.nc", 
                                          data_var_map_array)
                                          
        """
        self._check_lsm_input(data_var_map_array)
        
        subset_nc = Dataset(netcdf_file_path, 'w')
        
        #dimensions
        #previously just added data, but needs to be hourly
        #BEFORE: subset_nc.createDimension('time', len(self.time_array))
        #NOW:
        subset_nc.createDimension('time', len(self.hourly_time_array))
        subset_nc.createDimension('lat', len(self.lsm_lat_indices))
        subset_nc.createDimension('lon', len(self.lsm_lon_indices))

        #time
        time_var = subset_nc.createVariable('time', 'i4',
                                            ('time',))
        time_var.long_name = 'time'
        time_var.standard_name = 'time'
        time_var.units = 'seconds since 1970-01-01 00:00:00+00:00'
        time_var.axis = 'T'
        time_var.calendar = 'gregorian'
        #previously just added data, but needs to be hourly
        #BEFORE: time_var[:] = self.time_array
        #NOW:
        time_var[:] = self.hourly_time_array

        ##2D GRID - Not Supported by ArcMap or QGIS
        """
        #longitude
        lon_2d_var = subset_nc.createVariable('longitude', 'f8', ('lat','lon'),
                                            fill_value=-9999.0)
        lon_2d_var.long_name = 'longitude'
        lon_2d_var.standard_name = 'longitude'
        lon_2d_var.units = 'degrees_east'
        lon_2d_var.coordinates = 'lat lon'
        lon_2d_var.axis = 'X'
        
        #latitude
        lat_2d_var = subset_nc.createVariable('latitude', 'f8', ('lat','lon'),
                                              fill_value=-9999.0)
        lat_2d_var.long_name = 'latitude'
        lat_2d_var.standard_name = 'latitude'
        lat_2d_var.units = 'degrees_north'
        lat_2d_var.coordinates = 'lat lon'
        lat_2d_var.axis = 'Y'

        lon_2d_var[:], lat_2d_var[:] = transform(self.gssha_proj4, 
                                                 Proj(init='epsg:4326'),
                                                 self.proj_lon_list,
                                                 self.proj_lat_list, 
                                                 )
        """
        ##1D GRID - Able to display in ArcMap/QGIS, but loose information
        #longitude
        lon_var = subset_nc.createVariable('lon', 'f8', ('lon'),
                                            fill_value=-9999.0)
        lon_var.long_name = 'longitude'
        lon_var.standard_name = 'longitude'
        lon_var.units = 'degrees_east'
        lon_var.axis = 'X'
        
        #latitude
        lat_var = subset_nc.createVariable('lat', 'f8', ('lat'),
                                            fill_value=-9999.0)
        lat_var.long_name = 'latitude'
        lat_var.standard_name = 'latitude'
        lat_var.units = 'degrees_north'
        lat_var.axis = 'Y'

        lon_2d, lat_2d = transform(self.gssha_proj4,
                                   Proj(init='epsg:4326'),
                                   self.proj_lon_list,
                                   self.proj_lat_list, 
                                   )

        lon_var[:] = lon_2d.mean(axis=0)
        lat_var[:] = lat_2d.mean(axis=1)
        
        #DATA
        for gssha_var, lsm_var in data_var_map_array:
            if gssha_var in self.netcdf_attributes:
                gssha_data_var_name = self.netcdf_attributes[gssha_var]['gssha_name']
                net_var = subset_nc.createVariable(gssha_data_var_name, 'f4', 
                                                   ('time', 'lat', 'lon'),
                                                   fill_value=-9999.0)
                net_var.standard_name = self.netcdf_attributes[gssha_var]['standard_name']
                net_var.long_name = self.netcdf_attributes[gssha_var]['long_name']
                net_var.units = self.netcdf_attributes[gssha_var]['units']['netcdf']
                self._load_converted_gssha_data_from_lsm(gssha_var, lsm_var, 'netcdf')
                #previously just added data, but needs to be hourly
                self._convert_data_to_hourly(gssha_var)
                net_var[:] = self.data_np_array
            else:
                raise IndexError("Invalid GSSHA variable name: {0} ...".format(gssha_var))

        #projection
        crs_var = subset_nc.createVariable('crs', 'i4')
        crs_var.grid_mapping_name = 'latitude_longitude'
        crs_var.epsg_code = 'EPSG:4326'  # WGS 84
        crs_var.semi_major_axis = 6378137.0
        crs_var.inverse_flattening = 298.257223563
        
        #add global attributes
        subset_nc.Conventions = 'CF-1.6'
        subset_nc.title = 'GSSHA LSM Input'
        subset_nc.history = 'date_created: {0}'.format(datetime.utcnow())
        subset_nc.gssha_projection = self.gssha_prj_str
        subset_nc.north = self.north_bound
        subset_nc.south = self.south_bound
        subset_nc.east = self.east_bound
        subset_nc.west = self.west_bound
        subset_nc.cell_size = self.cell_size

        subset_nc.close()
"""        
if __name__ == "__main__":
    #gssha_project_folder = 'C:\\Users\\RDCHLADS\\Documents\\GSSHA\\AF_GSSHA\\NK_Texas\\GSSHA'
    #gssha_project_folder = '/Volumes/Seagate Backup Plus Drive/GSSHA'
    gssha_project_folder = 'E:\\GSSHA'
    gssha_grid_name = 'nk_arb2.ele'

    ###### ----------
    ### LSM INPUT
    ###### ----------

##    ##GLDAS
##    lsm_folder = 'E:\\AutoRAPID\\lsm_data\\GLDAS'
##    #lsm_folder = '/Volumes/Seagate Backup Plus Drive/AutoRAPID/lsm_data/GLDAS'
##   lsm_lat_var = 'lat'
##    lsm_lon_var = 'lon'
##    search_card = 'GLDAS_NOAH025_3H.A19890116*.020.nc4'
##    precip_data_var='Rainf_tavg'
##    precip_type = 'RADAR'
##    humidity_gssha_data_var = 'relative_humidity'
##    humidity_lsm_data_var = ['Qair_f_inst', 'Psurf_f_inst', 'Tair_f_inst']
##    lsm_file_date_naming_convention = None
##    main_output_folder = path.join(gssha_project_folder, "gssha_from_gldas")
##    out_gage_file = path.join(main_output_folder, 'gage_test_gldas.gag')
##    netcdf_file_path = path.join(main_output_folder, 'gssha_dynamic_gldas.nc')
##    data_var_map_array = [
##                          ['precipitation_rate', 'Rainf_f_tavg'], 
##                          ['pressure', 'Psurf_f_inst'], 
##                          ['relative_humidity', ['Qair_f_inst', 'Psurf_f_inst', 'Tair_f_inst']], 
##                          ['wind_speed', 'Wind_f_inst'], 
##                          ['temperature', 'Tair_f_inst'],
##                          ['direct_radiation', 'Swnet_tavg'],
##                          ['diffusive_radiation', 'SWdown_f_tavg'],
##                         ]
    ##WRF
    # See: http://www.meteo.unican.es/wiki/cordexwrf/OutputVariables
    lsm_folder = 'E:\\GSSHA\\wrf-sample-data-v1.0'
    #lsm_folder = '/Volumes/Seagate Backup Plus Drive/GSSHA/wrf-sample-data-v1.0'
    lsm_lat_var = 'XLAT'
    lsm_lon_var = 'XLONG'
    search_card = '*.nc'
    precip_data_var = ['RAINC', 'RAINNC']
    precip_type = 'ACCUM'
    lsm_file_date_naming_convention='gssha_d02_%Y_%m_%d_%H_%M_%S.nc'
    
    ##CONVERT FROM RAW WRF DATA
    main_output_folder = path.join(gssha_project_folder, "wrf_hmet_data")
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
    ##EXTRACT FROM CONVERTED WRF DATA
##    main_output_folder = path.join(gssha_project_folder, "gssha_from_wrf_no_conv")
##    data_var_map_array = [
##                          ['precipitation_acc', 'RUNPCP'], 
##                          ['pressure_hg', 'PSFCInHg'], 
##                          ['relative_humidity', 'RH2'], 
##                          ['wind_speed_kts', 'SPEED10'], 
##                          ['temperature_f', 'T2F'],
##                          ['cloud_cover_pc' , 'SKYCOVER'],
##                         ]


    out_gage_file = path.join(main_output_folder, 'gage_test_wrf.gag')
    netcdf_file_path = path.join(main_output_folder, 'gssha_dynamic_wrf.nc')
    ###### ----------
    ### MAIN FUNNCTIONS
    ###### ----------

    l2g = LSMtoGSSHA(gssha_project_folder=gssha_project_folder,
                     gssha_grid_file_name=gssha_grid_name,
                     lsm_input_folder_path=lsm_folder,
                     lsm_search_card=search_card, 
                     lsm_lat_var=lsm_lat_var,
                     lsm_lon_var=lsm_lon_var,
                     #lsm_time_var='time',
                     lsm_file_date_naming_convention=lsm_file_date_naming_convention,
                     #gssha_projection_file_name="",
                     lsm_grid_type='geographic' # geographic, or wrf (to use global projection attributes)
                     )
    
    l2g.lsm_precip_to_gssha_precip_gage(out_gage_file,
                                        lsm_data_var=precip_data_var,
                                        precip_type=precip_type)

    l2g.lsm_data_to_arc_ascii(data_var_map_array, main_output_folder)

    l2g.lsm_data_to_subset_netcdf(netcdf_file_path, data_var_map_array)
"""