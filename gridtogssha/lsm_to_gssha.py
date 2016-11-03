# -*- coding: utf-8 -*-
##
##  lsm_to_gssha.py
##  GSSHApy
##
##  Created by Alan D Snow, 2016.
##  License BSD 3-Clause

from datetime import datetime, timedelta
from dateutil import parser
from io import open as io_open
import math
from os import path, remove, rename
from shutil import copy

#extra dependencies
try:
    import numpy as np
    from pyproj import Proj, transform
    from osgeo import osr
    from netCDF4 import Dataset
except ImportError:
    print("To use LSMtoGSSHA, you must have the numpy, pyproj, gdal, and netCDF4 packages installed.")
    raise

from .grid_to_gssha import GRIDtoGSSHA
    
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
class LSMtoGSSHA(GRIDtoGSSHA):
    """This class converts the LSM output data to GSSHA formatted input.
    This class inheris from class:`GRIDtoGSSHA`.
    
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
        output_unix_format(Optional[bool]): If True, it will output to "unix" format. 
                                        Otherwise, it will output in "dos" (Windows) format. Default is False. 
        output_timezone(Optional[tzinfo]): This is the timezone to output the dates for the data. Default is UTC.

    Example::
    
        from gridtogssha import LSMtoGSSHA
        
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
                 output_timezone=None,
                 ):
        """
        Initializer function for the LSMtoGSSHA class
        """
        self.lsm_lat_var = lsm_lat_var
        self.lsm_lon_var = lsm_lon_var
        self.lsm_time_var = lsm_time_var
        self.lsm_grid_type = lsm_grid_type
        
        super(LSMtoGSSHA, self).__init__(gssha_project_folder,
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
            
    def _get_subset_lat_lon(self, gssha_y_min, gssha_y_max, gssha_x_min, gssha_x_max):
        """
        #subset lat lon list based on GSSHA extent
        """
        ######
        #STEP 1: Load latitude and longiute
        ######
        
        if self.lsm_grid_type=='geographic':
            lsm_nc = Dataset(self.lsm_nc_list[0])
            lsm_lon_array = lsm_nc.variables[self.lsm_lon_var][:] #assume [-180, 180]
            lsm_lat_array = lsm_nc.variables[self.lsm_lat_var][:] #assume [-90,90]
            lsm_nc.close()
            
            #convert 3d to 2d if time dimension
            if(len(lsm_lon_array.shape) == 3):
                lsm_lon_array = lsm_lon_array[0]
                lsm_lat_array = lsm_lat_array[0]
                
        elif self.lsm_grid_type=='wrf':
            #EXPERIMENTAL CODE
        
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
            lsm_lon_array, lsm_lat_array = transform(Proj(init='epsg:4326'),
                                                     self.lsm_proj4,
                                                     lsm_nc.variables[self.lsm_lon_var][:],
                                                     lsm_nc.variables[self.lsm_lat_var][:], 
                                                     )
            #convert 3d to 2d if time dimension
            if(len(lsm_lon_array.shape) == 3):
                lsm_lon_array = lsm_lat_array[0]
                lsm_lat_array = lsm_lat_array[0]
            
        else:
            raise IndexError("Invalid mode to retrieve LSM Lat/Lon lists ...")
        

        ######
        #STEP 2: Determine range within LSM Grid
        ######

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

        return lsm_lat_list, lsm_lon_list
        
 
    def _load_time_from_files(self):
        """
        Loads in the time from the grid files
        """
        epoch = datetime.utcfromtimestamp(0)
        convert_to_seconds = 1
        
        if self.lsm_file_date_naming_convention is not None:
            #METHOD 1: LOAD FROM TIME STRING IN FILES
            for lsm_idx, lsm_nc_file in enumerate(self.lsm_nc_list):
                self.time_array[lsm_idx] = (datetime.strptime(path.basename(lsm_nc_file),self.lsm_file_date_naming_convention)-epoch).total_seconds()
        else:
            #METHOD 2: LOAD FROM TIME IN NETCDF FILE
            lsm_nc = Dataset(self.lsm_nc_list[0])
            #GET TIME CONVERSION TO SECONDS
            time_info = lsm_nc.variables[self.lsm_time_var].getncattr("units").strip()
            time_units, time_start = time_info.split('since')
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
                self.time_array[lsm_idx] = (datetime_start+timedelta(seconds=lsm_time*convert_to_seconds)-epoch).total_seconds()
                lsm_nc.close()
                
        return convert_to_seconds
        
    def _load_time_step(self, convert_to_seconds):
        """
        Loads in the time step
        """
        #GET TIME STEP
        if self.time_step_seconds is None:
            lsm_nc = Dataset(self.lsm_nc_list[0])
            try:
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
