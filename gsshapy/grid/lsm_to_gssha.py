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

        from gsshapy.grid import LSMtoGSSHA

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
        self.lsm_proj4 = Proj(init='epsg:4326')
        if 'MAP_PROJ' in lsm_nc:
            # WRF GRID
            return

    def _get_subset_lat_lon(self, gssha_y_min, gssha_y_max, gssha_x_min, gssha_x_max):
        """
        #subset lat lon list based on GSSHA extent
        """
        ######
        #STEP 1: Load latitude and longiute
        ######

        lsm_nc = Dataset(self.lsm_nc_list[0])
        lsm_lon_array = lsm_nc.variables[self.lsm_lon_var][:] #assume [-180, 180]
        lsm_lat_array = lsm_nc.variables[self.lsm_lat_var][:] #assume [-90,90]
        lsm_nc.close()

        #convert 3d to 2d if time dimension
        if(len(lsm_lon_array.shape) == 3):
            lsm_lon_array = lsm_lon_array[0]
            lsm_lat_array = lsm_lat_array[0]

        ######
        #STEP 2: Determine range within LSM Grid
        ######

        lsm_dx = np.max(np.absolute(np.diff(lsm_lon_array)))

        # Extract the lat and lon within buffered extent
        #IF LAT LON IS !D:
        if len(lsm_lat_array.shape) == 1:
            lsm_dy = np.max(np.absolute(np.diff(lsm_lat_array)))

            self.lsm_lat_indices = np.where((lsm_lat_array >= (gssha_y_min - lsm_dy)) & (lsm_lat_array <= (gssha_y_max + lsm_dy)))[0]
            self.lsm_lon_indices = np.where((lsm_lon_array >= (gssha_x_min - lsm_dx)) & (lsm_lon_array <= (gssha_x_max + lsm_dx)))[0]

            lsm_lon_list, lsm_lat_list = np.meshgrid(lsm_lon_array[self.lsm_lon_indices], lsm_lat_array[self.lsm_lat_indices])
        #IF LAT LON IS 2D:
        elif len(lsm_lat_array.shape) == 2:
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
            # EXTRACT DATA WITHIN EXTENT
            lsm_var = lsm_nc.variables[data_var]
            if lsm_var.ndim == 4:
                if four_dim_var_calc_method is None:
                    raise ValueError("The variable {var} has 4 dimension. "
                                     "Need 'four_dim_var_calc_method' to proceed ..."
                                     .format(var=data_var))
                data = lsm_nc.variables[data_var][0, :, self.lsm_lat_indices, self.lsm_lon_indices]
                self.data_np_array[lsm_idx] = four_dim_var_calc_method(data * conversion_factor, axis=0)
            else:
                if lsm_var.ndim == 3:
                    # assume size of time dimension is one
                    data = lsm_var[0, self.lsm_lat_indices, self.lsm_lon_indices]
                else:  # lsm_var.ndim == 2
                    data = lsm_var[self.lsm_lat_indices, self.lsm_lon_indices]

                self.data_np_array[lsm_idx] = data*conversion_factor

            lsm_nc.close()
