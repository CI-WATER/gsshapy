# -*- coding: utf-8 -*-
#
#  grid_to_gssha.py
#  GSSHApy
#
#  Created by Alan D Snow, 2016.
#  License BSD 3-Clause

from builtins import range
from datetime import datetime
from io import open as io_open
import logging
import numpy as np
from os import mkdir, path, remove, rename
import pangaea as pa
from past.builtins import basestring
from pytz import utc
from shutil import copy
import xarray as xr
import xarray.ufuncs as xu

from gazar.grid import ArrayGrid
from ..lib import db_tools as dbt

log = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------
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


def esat(temp):
    """
    saturation water vapour pressure is expressed with the Teten’s formula
    http://www.ecmwf.int/sites/default/files/elibrary/2016/16648-part-iv-physical-processes.pdf
    7.2.1 (b) eqn. 7.5
    esat(T) = a1*exp(a3*((T − T0)/(T − a4)))
    a1 = 611.21 Pa, a3 = 17.502 and a4 = 32.19 K for saturation over water
    T0 = 273.16 K
    note: ignoring saturation over ice & mixed
    """
    return 611.21*xu.exp(17.502*(temp-273.16)/(temp-32.19))


# ------------------------------------------------------------------------------
# MAIN CLASS
# ------------------------------------------------------------------------------
class GRIDtoGSSHA(object):
    """This class converts the LSM output data to GSSHA formatted input.

    Attributes:
        gssha_project_folder(:obj:`str`): Path to the GSSHA project folder
        gssha_project_file_name(:obj:`str`): Name of the GSSHA elevation grid file.
        lsm_input_folder_path(:obj:`str`): Path to the input folder for the LSM files.
        lsm_search_card(:obj:`str`): Glob search pattern for LSM files. Ex. "*.nc".
        lsm_lat_var(Optional[:obj:`str`]): Name of the latitude variable in the LSM netCDF files. Defaults to 'lat'.
        lsm_lon_var(Optional[:obj:`str`]): Name of the longitude variable in the LSM netCDF files. Defaults to 'lon'.
        lsm_time_var(Optional[:obj:`str`]): Name of the time variable in the LSM netCDF files. Defaults to 'time'.
        lsm_lat_dim(Optional[:obj:`str`]): Name of the latitude dimension in the LSM netCDF files. Defaults to 'lat'.
        lsm_lon_dim(Optional[:obj:`str`]): Name of the longitude dimension in the LSM netCDF files. Defaults to 'lon'.
        lsm_time_dim(Optional[:obj:`str`]): Name of the time dimension in the LSM netCDF files. Defaults to 'time'.
        output_timezone(Optional[:obj:`tzinfo`]): This is the timezone to output the dates for the data. Default is the timezone of your GSSHA model. This option does NOT currently work for NetCDF output.

    Example::

        from gsshapy.grid import GRIDtoGSSHA

        g2g = GRIDtoGSSHA(gssha_project_folder='E:/GSSHA',
                          gssha_project_file_name='gssha.prj',
                          lsm_input_folder_path='E:/GSSHA/lsm-data',
                          lsm_search_card="*.nc",
                         )

    """
    # DEFAULT GSSHA NetCDF Attributes
    netcdf_attributes = {
                        'precipitation_rate':
                            # NOTE: LSM INFO
                            # units = "kg m-2 s-1" ; i.e. mm s-1
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
                                                        'ascii': 3600,
                                                        'netcdf': 3600,
                                                    },
                            },
                        'precipitation_acc':
                            # NOTE: LSM INFO
                            # assumes units = "kg m-2" ; i.e. mm
                            # checks for units: "m"
                            {
                              'units' : {
                                            'gage': 'mm hr-1',
                                            'ascii': 'mm hr-1',
                                            'netcdf': 'mm hr-1',
                                        },
                              'units_netcdf' : 'mm hr-1',
                              'standard_name' : 'rainfall_flux',
                              'long_name': 'Rain precipitation rate',
                              'gssha_name': 'precipitation',
                              'hmet_name': 'Prcp',
                              'conversion_factor': {
                                                        'gage': 1,
                                                        'ascii': 1,
                                                        'netcdf': 1,
                                                    },
                            },
                        'precipitation_inc':
                            # NOTE: LSM INFO
                            # assumes units = "kg m-2" ; i.e. mm
                            # checks for units: "m"
                            {
                              'units' : {
                                            'gage': 'mm hr-1',
                                            'ascii': 'mm hr-1',
                                            'netcdf': 'mm hr-1',
                                        },
                              'units_netcdf': 'mm hr-1',
                              'standard_name': 'rainfall_flux',
                              'long_name': 'Rain precipitation rate',
                              'gssha_name': 'precipitation',
                              'hmet_name': 'Prcp',
                              'conversion_factor': {
                                                        'gage' : 1,
                                                        'ascii' : 1,
                                                        'netcdf' : 1,
                                                    },
                            },
                        'pressure':
                            # NOTE: LSM INFO
                            # units = "Pa" ;
                            {
                              'units': {
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
                        'pressure_hg':
                            {
                              'units': {
                                            'ascii': 'in. Hg',
                                            'netcdf': 'mb',
                                        },
                              'standard_name' : 'surface_air_pressure',
                              'long_name' : 'Pressure',
                              'gssha_name' : 'pressure',
                              'hmet_name' : 'Pres',
                              'conversion_factor' : {
                                                        'ascii': 1,
                                                        'netcdf': 33.863886667,
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
                        'relative_humidity_dew' :
                            #NOTE: ECMWF provides dew point temperature
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
                        'wind_speed_kmd' :
                            #NOTE: LSM
                            #units = "km/day" ;
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
                                                        'ascii' : 0.0224537037,
                                                        'netcdf' : 0.0224537037,
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
                                                        'netcdf' : lambda temp_farenheight: (temp_farenheight - 32) * 5.0/9.0,
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
                              'standard_name' : 'surface_direct_downward_shortwave_flux',
                              'long_name' : 'Direct short wave radiation flux',
                              'gssha_name' : 'direct_radiation',
                              'hmet_name' : 'Drad',
                              'conversion_factor' : {
                                                        'ascii' : 1,
                                                        'netcdf' : 1,
                                                    },
                            },
                        'direct_radiation_j' :
                            #DIRECT/BEAM/SOLAR RADIATION
                            #NOTE: LSM
                            #units = "J m-2" ;
                            {
                              'units' : {
                                            'ascii': 'W hr m-2',
                                            'netcdf': 'W hr m-2',
                                        },
                              'standard_name' : 'surface_direct_downward_shortwave_flux',
                              'long_name' : 'Direct short wave radiation flux',
                              'gssha_name' : 'direct_radiation',
                              'hmet_name' : 'Drad',
                              'conversion_factor' : {
                                                        'ascii' : 1/3600.0,
                                                        'netcdf' : 1/3600.0,
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
                              'standard_name' : 'surface_diffusive_downward_shortwave_flux',
                              'long_name' : 'Diffusive short wave radiation flux',
                              'gssha_name' : 'diffusive_radiation',
                              'hmet_name' : 'Grad', #6.1 GSSHA CODE INCORRECTLY SAYS IT IS GRAD
                              'conversion_factor' : {
                                                        'ascii' : 1,
                                                        'netcdf' : 1,
                                                    },
                            },
                        'diffusive_radiation_j' :
                            #DIFFUSIVE RADIATION
                            #NOTE: LSM
                            #ERA5: global_radiation - diffusive_radiation
                            #units = "J m-2" ;
                            {
                              'units' : {
                                            'ascii': 'W hr m-2',
                                            'netcdf': 'W hr m-2',
                                        },
                              'standard_name' : 'surface_diffusive_downward_shortwave_flux',
                              'long_name' : 'Diffusive short wave radiation flux',
                              'gssha_name' : 'diffusive_radiation',
                              'hmet_name' : 'Grad', #6.1 GSSHA CODE INCORRECTLY SAYS IT IS GRAD
                              'conversion_factor' : {
                                                        'ascii' : 1/3600.0,
                                                        'netcdf' : 1/3600.0,
                                                    },
                            },
                        'direct_radiation_cc' :
                            #DIRECT/BEAM/SOLAR RADIATION
                            #NOTE: LSM
                            #DIFFUSIVE_FRACTION = cloud_cover_pc/100
                            #WRF: global_radiation * (1-DIFFUSIVE_FRACTION)
                            #units = "W m-2" ;
                            {
                              'units' : {
                                            'ascii': 'W hr m-2',
                                            'netcdf': 'W hr m-2',
                                        },
                              'standard_name' : 'surface_direct_downward_shortwave_flux',
                              'long_name' : 'Direct short wave radiation flux',
                              'gssha_name' : 'direct_radiation',
                              'hmet_name' : 'Drad',
                              'conversion_factor' : {
                                                        'ascii' : 1,
                                                        'netcdf' : 1,
                                                    },
                            },
                        'diffusive_radiation_cc' :
                            #DIFFUSIVE RADIATION
                            #NOTE: LSM
                            #DIFFUSIVE_FRACTION = cloud_cover_pc/100
                            #WRF: global_radiation * DIFFUSIVE_FRACTION
                            #units = "W m-2" ;
                            {
                              'units' : {
                                            'ascii': 'W hr m-2',
                                            'netcdf': 'W hr m-2',
                                        },
                              'standard_name' : 'surface_diffusive_downward_shortwave_flux',
                              'long_name' : 'Diffusive short wave radiation flux',
                              'gssha_name' : 'diffusive_radiation',
                              'hmet_name' : 'Grad', #6.1 GSSHA CODE INCORRECTLY SAYS IT IS GRAD
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
                              'standard_name' : 'cloud_cover_fraction',
                              'long_name' : 'Cloud cover fraction',
                              'gssha_name' : 'cloud_cover',
                              'hmet_name' : 'Clod',
                              'conversion_factor' : {
                                                        'ascii' : 100,
                                                        'netcdf' : 10,
                                                    },
                              'calc_4d_method' : 'max',
                              'calc_4d_dim' : 'bottom_top',
                            },
                        'cloud_cover_pc' :
                            {
                              'units' : {
                                            'ascii': '%',
                                            'netcdf': '%/10',
                                        },
                              'standard_name' : 'cloud_cover_fraction',
                              'long_name' : 'Cloud cover fraction',
                              'gssha_name' : 'cloud_cover',
                              'hmet_name' : 'Clod',
                              'conversion_factor' : {
                                                        'ascii' : 1,
                                                        'netcdf' : 0.1,
                                                    },
                            },

                    }

    def __init__(self,
                 gssha_project_folder,
                 gssha_project_file_name,
                 lsm_input_folder_path,
                 lsm_search_card,
                 lsm_lat_var='lat',
                 lsm_lon_var='lon',
                 lsm_time_var='time',
                 lsm_lat_dim='lat',
                 lsm_lon_dim='lon',
                 lsm_time_dim='time',
                 output_timezone=None,
                 ):
        """
        Initializer function for the GRIDtoGSSHA class
        """
        self.gssha_project_folder = gssha_project_folder
        self.gssha_project_file_name = gssha_project_file_name
        self.lsm_input_folder_path = lsm_input_folder_path
        self.lsm_search_card = lsm_search_card
        self.lsm_lat_var = lsm_lat_var
        self.lsm_lon_var = lsm_lon_var
        self.lsm_time_var = lsm_time_var
        self.lsm_lat_dim = lsm_lat_dim
        self.lsm_lon_dim = lsm_lon_dim
        self.lsm_time_dim = lsm_time_dim
        self.output_timezone = output_timezone
        self._xd = None

        # load in GSSHA model files
        project_manager, db_sessionmaker = \
            dbt.get_project_session(path.splitext(self.gssha_project_file_name)[0],
                                    self.gssha_project_folder)

        db_session = db_sessionmaker()
        project_manager.read(directory=self.gssha_project_folder,
                             filename=self.gssha_project_file_name,
                             session=db_session)

        self.gssha_grid = project_manager.getGrid()
        if self.output_timezone is None:
            self.output_timezone = project_manager.timezone
        db_session.close()

        # load in modeling extent
        self._load_modeling_extent()

    @property
    def xd(self):
        """get xarray dataset file handle to LSM files"""
        if self._xd is None:
            path_to_lsm_files = path.join(self.lsm_input_folder_path,
                                          self.lsm_search_card)

            self._xd = pa.open_mfdataset(path_to_lsm_files,
                                         lat_var=self.lsm_lat_var,
                                         lon_var=self.lsm_lon_var,
                                         time_var=self.lsm_time_var,
                                         lat_dim=self.lsm_lat_dim,
                                         lon_dim=self.lsm_lon_dim,
                                         time_dim=self.lsm_time_dim)

        return self._xd

    def _set_subset_indices(self, y_min, y_max, x_min, x_max):
        """
        load subset based on extent
        """
        y_coords, x_coords = self.xd.lsm.coords
        dx = self.xd.lsm.dx
        dy = self.xd.lsm.dy

        lsm_y_indices_from_y, lsm_x_indices_from_y = \
            np.where((y_coords >= (y_min - 2*dy)) &
                     (y_coords <= (y_max + 2*dy)))
        lsm_y_indices_from_x, lsm_x_indices_from_x = \
            np.where((x_coords >= (x_min - 2*dx)) &
                     (x_coords <= (x_max + 2*dx)))

        lsm_y_indices = np.intersect1d(lsm_y_indices_from_y,
                                       lsm_y_indices_from_x)
        lsm_x_indices = np.intersect1d(lsm_x_indices_from_y,
                                       lsm_x_indices_from_x)

        self.xslice = slice(np.amin(lsm_x_indices),
                            np.amax(lsm_x_indices)+1)
        self.yslice = slice(np.amin(lsm_y_indices),
                            np.amax(lsm_y_indices)+1)

    def _load_modeling_extent(self):
        """
        # Get extent from GSSHA Grid in LSM coordinates
        # Determine range within LSM Grid
        """
        ####
        # STEP 1: Get extent from GSSHA Grid in LSM coordinates
        ####
        # reproject GSSHA grid and get bounds
        min_x, max_x, min_y, max_y = self.gssha_grid.bounds(as_projection=self.xd.lsm.projection)

        # set subset indices
        self._set_subset_indices(min_y,
                                 max_y,
                                 min_x,
                                 max_x)


    def _time_to_string(self, dt, conversion_string="%Y %m %d %H %M"):
        """
        This converts a UTC time integer to a string
        """
        if self.output_timezone is not None:
            dt = dt.replace(tzinfo=utc) \
                   .astimezone(self.output_timezone)
        return dt.strftime(conversion_string)

    def _load_lsm_data(self, data_var,
                       conversion_factor=1,
                       calc_4d_method=None,
                       calc_4d_dim=None):
        """
        This extracts the LSM data from a folder of netcdf files
        """
        data = self.xd.lsm.getvar(data_var,
                                  yslice=self.yslice,
                                  xslice=self.xslice,
                                  calc_4d_method=calc_4d_method,
                                  calc_4d_dim=calc_4d_dim,
                                  )
        data = data.fillna(0)
        data.values *= conversion_factor
        return data

    def _load_converted_gssha_data_from_lsm(self, gssha_var, lsm_var, load_type):
        """
        This function loads data from LSM and converts to GSSHA format
        """
        if 'radiation' in gssha_var:
            conversion_factor = self.netcdf_attributes[gssha_var]['conversion_factor'][load_type]
            if gssha_var.startswith('direct_radiation') and not isinstance(lsm_var, basestring):
                # direct_radiation = (1-DIFFUSIVE_FRACION)*global_radiation
                global_radiation_var, diffusive_fraction_var = lsm_var
                global_radiation = self._load_lsm_data(global_radiation_var, conversion_factor)
                diffusive_fraction = self._load_lsm_data(diffusive_fraction_var)
                if gssha_var.endswith("cc"):
                    diffusive_fraction /= 100.0

                self.data = ((1-diffusive_fraction)*global_radiation)

            elif gssha_var.startswith('diffusive_radiation') and not isinstance(lsm_var, basestring):
                # diffusive_radiation = DIFFUSIVE_FRACION*global_radiation
                global_radiation_var, diffusive_fraction_var = lsm_var
                global_radiation = self._load_lsm_data(global_radiation_var, conversion_factor)
                diffusive_fraction = self._load_lsm_data(diffusive_fraction_var)
                if gssha_var.endswith("cc"):
                    diffusive_fraction /= 100
                self.data = (diffusive_fraction*global_radiation)

            elif isinstance(lsm_var, basestring):
                self.data = self._load_lsm_data(lsm_var, self.netcdf_attributes[gssha_var]['conversion_factor'][load_type])
            else:
                raise ValueError("Invalid LSM variable ({0}) for GSSHA variable {1}".format(lsm_var, gssha_var))

        elif gssha_var == 'relative_humidity' and not isinstance(lsm_var, str):
            ##CONVERSION ASSUMPTIONS:
            ##1) These equations are for liquid water and are less accurate below 0 deg C
            ##2) Not adjusting the pressure for the fact that the temperature
            ##   and moisture measurements are given at 2 m AGL.

            ##Neither of these should have a significant impact on RH values
            ##given the uncertainty in the model values themselves.

            specific_humidity_var, pressure_var, temperature_var = lsm_var
            specific_humidity = self._load_lsm_data(specific_humidity_var)
            pressure = self._load_lsm_data(pressure_var)
            temperature = self._load_lsm_data(temperature_var)
            ##To compute the relative humidity at 2m,
            ##given T, Q (water vapor mixing ratio) at 2 m and PSFC (surface pressure):
            ##Es(saturation vapor pressure in Pa)
            ##Qs(saturation mixing ratio)=(0.622*es)/(PSFC-es)
            ##RH = 100*Q/Qs
            es = esat(temperature)
            self.data = 100 * specific_humidity/((0.622*es)/(pressure-es))

        elif gssha_var == 'relative_humidity_dew':
            # https://software.ecmwf.int/wiki/display/CKB/Do+ERA+datasets+contain+parameters+for+near-surface+humidity
            # temperature in Kelvin
            # RH = 100 * es(Td)/es(T)
            dew_point_temp_var, temperature_var = lsm_var
            dew_point_temp = self._load_lsm_data(dew_point_temp_var)
            temperature = self._load_lsm_data(temperature_var)
            self.data = 100 * esat(dew_point_temp)/esat(temperature)

        elif gssha_var == 'wind_speed' and not isinstance(lsm_var, str):
            # WRF:  http://www.meteo.unican.es/wiki/cordexwrf/OutputVariables
            u_vector_var, v_vector_var = lsm_var
            conversion_factor = self.netcdf_attributes[gssha_var]['conversion_factor'][load_type]
            u_vector = self._load_lsm_data(u_vector_var, conversion_factor)
            v_vector = self._load_lsm_data(v_vector_var, conversion_factor)
            self.data = (xu.sqrt(u_vector**2 + v_vector**2))

        elif 'precipitation' in gssha_var and not isinstance(lsm_var, str):
            # WRF:  http://www.meteo.unican.es/wiki/cordexwrf/OutputVariables
            rain_c_var, rain_nc_var = lsm_var
            conversion_factor = self.netcdf_attributes[gssha_var]['conversion_factor'][load_type]
            rain_c = self._load_lsm_data(rain_c_var, conversion_factor)
            rain_nc = self._load_lsm_data(rain_nc_var, conversion_factor)
            self.data = rain_c + rain_nc

        else:
            self.data = self._load_lsm_data(lsm_var,
                                            self.netcdf_attributes[gssha_var]['conversion_factor'][load_type],
                                            self.netcdf_attributes[gssha_var].get('calc_4d_method'),
                                            self.netcdf_attributes[gssha_var].get('calc_4d_dim'),
                                            )
            conversion_function = self.netcdf_attributes[gssha_var].get('conversion_function')
            if conversion_function:
                self.data.values = self.netcdf_attributes[gssha_var]['conversion_function'][load_type](self.data.values)

        if 'precipitation' in gssha_var:
            # NOTE: Precipitation is converted from mm/s to mm/hr
            # with the conversion factor when it is a rate.
            if 'units' in self.data.attrs:
                if self.data.attrs['units'] == 'm':
                    # convert from m to mm
                    self.data.values *= 1000

            if load_type == 'ascii' or load_type == 'netcdf':
                # CONVERT TO INCREMENTAL
                if gssha_var == 'precipitation_acc':
                    self.data.values = np.lib.pad(self.data.diff(self.lsm_time_dim).values,
                                                  ((1, 0), (0, 0), (0, 0)),
                                                  'constant',
                                                  constant_values=0)

                # CONVERT PRECIP TO RADAR (mm/hr) IN FILE
                if gssha_var == 'precipitation_inc' or gssha_var == 'precipitation_acc':
                    # convert from mm to mm/hr
                    time_step_hours = np.diff(self.xd[self.lsm_time_var].values)[0]/np.timedelta64(1, 'h')
                    self.data.values /= time_step_hours

        # convert to dataset
        gssha_data_var_name = self.netcdf_attributes[gssha_var]['gssha_name']
        self.data = self.data.to_dataset(name=gssha_data_var_name)
        self.data.rename({self.lsm_time_dim: 'time',
                          self.lsm_lon_dim: 'x',
                          self.lsm_lat_dim: 'y',
                          self.lsm_time_var: 'time',
                          self.lsm_lon_var: 'lon',
                          self.lsm_lat_var: 'lat'
                          },
                         inplace=True)

        self.data.attrs = {'proj4': self.xd.lsm.projection.ExportToProj4()}
        self.data[gssha_data_var_name].attrs = {
           'standard_name': self.netcdf_attributes[gssha_var]['standard_name'],
           'long_name': self.netcdf_attributes[gssha_var]['long_name'],
           'units': self.netcdf_attributes[gssha_var]['units'][load_type],
        }

    def _check_lsm_input(self, data_var_map_array):
        """
        This function checks the input var map array
        to ensure the required input variables exist
        """
        REQUIRED_HMET_VAR_LIST = ['Prcp', 'Pres', 'Temp', 'Clod',
                                  'RlHm', 'Drad', 'Grad', 'WndS']

        # make sure all required variables exist
        given_hmet_var_list = []
        for gssha_data_var, lsm_data_var in data_var_map_array:
            gssha_data_hmet_name = self.netcdf_attributes[gssha_data_var]['hmet_name']

            if gssha_data_hmet_name in given_hmet_var_list:
                raise ValueError("Duplicate parameter for HMET variable {0}"
                                 .format(gssha_data_hmet_name))
            else:
                given_hmet_var_list.append(gssha_data_hmet_name)

        for REQUIRED_HMET_VAR in REQUIRED_HMET_VAR_LIST:
            if REQUIRED_HMET_VAR not in given_hmet_var_list:
                raise ValueError("ERROR: HMET param is required to continue "
                                 "{0} ...".format(REQUIRED_HMET_VAR))

    def _resample_data(self, gssha_var):
        """
        This function resamples the data to match the GSSHA grid
        IN TESTING MODE
        """
        self.data = self.data.lsm.resample(gssha_var, self.gssha_grid)

    @staticmethod
    def _get_calc_function(gssha_data_var):
        """
        This retrives the calc function to convert
        to hourly data for the various HMET parameters
        """
        calc_function = 'mean'
        if gssha_data_var == 'precipitation_inc' or \
                gssha_data_var == 'precipitation_acc':
            # acc computed as inc previously
            calc_function = 'sum'

        return calc_function

    def _convert_data_to_hourly(self, gssha_data_var):
        """
        This function converts the data to hourly data
        and then puts it into the data_np_array
        USED WHEN GENERATING HMET DATA ONLY
        """
        time_step_hours = np.diff(self.data.time)[0]/np.timedelta64(1, 'h')
        calc_function = self._get_calc_function(gssha_data_var)
        resampled_data = None
        if time_step_hours < 1:
            resampled_data = self.data.resample('1H', dim='time',
                                                how=calc_function,
                                                keep_attrs=True)
        elif time_step_hours > 1:
            resampled_data = self.data.resample('1H', dim='time',
                                                keep_attrs=True)

            for time_idx in range(self.data.dims['time']):
                if time_idx+1 < self.data.dims['time']:
                    # interpolate between time steps
                    start_time = self.data.time[time_idx].values
                    end_time = self.data.time[time_idx+1].values
                    slope_timeslice = slice(str(start_time), str(end_time))
                    slice_size = resampled_data.sel(time=slope_timeslice).dims['time'] - 1
                    first_timestep = resampled_data.sel(time=str(start_time))[gssha_data_var]
                    slope = (resampled_data.sel(time=str(end_time))[gssha_data_var]
                             - first_timestep)/float(slice_size)

                    data_timeslice = slice(str(start_time+np.timedelta64(1, 'm')),
                                            str(end_time-np.timedelta64(1, 'm')))
                    data_subset = resampled_data.sel(time=data_timeslice)
                    for xidx in range(data_subset.dims['time']):
                        data_subset[gssha_data_var][xidx] = first_timestep + slope * (xidx+1)
                else:
                    # just continue to repeat the timestep
                    start_time = self.data.time[time_idx].values
                    end_time = resampled_data.time[-1].values
                    if end_time > start_time:
                        first_timestep = resampled_data.sel(time=str(start_time))[gssha_data_var]

                        data_timeslice = slice(str(start_time), str(end_time))
                        data_subset = resampled_data.sel(time=data_timeslice)
                        slice_size = 1
                        if calc_function == "mean":
                            slice_size = data_subset.dims['time']

                        for xidx in range(data_subset.dims['time']):
                            data_subset[gssha_data_var][xidx] = first_timestep/float(slice_size)

        if resampled_data is not None:
            # make sure coordinates copied
            if self.data.lsm.x_var not in resampled_data.coords:
                resampled_data.coords[self.data.lsm.x_var] = self.data.coords[self.data.lsm.x_var]
            if self.data.lsm.y_var not in resampled_data.coords:
                resampled_data.coords[self.data.lsm.y_var] = self.data.coords[self.data.lsm.y_var]
            self.data = resampled_data

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

        GRIDtoGSSHA Example:

        .. code:: python

            from gsshapy.grid import GRIDtoGSSHA

            #STEP 1: Initialize class
            g2g = GRIDtoGSSHA(gssha_project_folder='/path/to/gssha_project',
                              gssha_project_file_name='gssha_project.prj',
                              lsm_input_folder_path='/path/to/wrf-data',
                              lsm_search_card='*.nc',
                              lsm_lat_var='XLAT',
                              lsm_lon_var='XLONG',
                              lsm_time_var='Times',
                              lsm_lat_dim='south_north',
                              lsm_lon_dim='west_east',
                              lsm_time_dim='Time',
                              )

            #STEP 2: Generate GAGE data (from WRF)
            g2g.lsm_precip_to_gssha_precip_gage(out_gage_file="E:/GSSHA/wrf_gage_1.gag",
                                                lsm_data_var=['RAINC', 'RAINNC'],
                                                precip_type='ACCUM')

        HRRRtoGSSHA Example:

        .. code:: python

            from gsshapy.grid import HRRRtoGSSHA

            #STEP 1: Initialize class
            h2g = HRRRtoGSSHA(
                              #YOUR INIT PARAMETERS HERE
                             )

            #STEP 2: Generate GAGE data
            g2g.lsm_precip_to_gssha_precip_gage(out_gage_file="E:/GSSHA/hrrr_gage_1.gag",
                                                lsm_data_var='prate',
                                                precip_type='RADAR')

        """
        VALID_TYPES = ["ACCUM", "RADAR", "GAGES"] #NOTE: "RATES" currently not supported
        if precip_type not in VALID_TYPES:
            raise ValueError("ERROR: {0} is not a valid type. Valid types include: {1}".format(type, VALID_TYPES))

        gssha_precip_type = "precipitation_inc"
        if precip_type == "ACCUM":
            gssha_precip_type = "precipitation_acc"
        elif precip_type == "RADAR":
            gssha_precip_type = "precipitation_rate"

        self._load_converted_gssha_data_from_lsm(gssha_precip_type, lsm_data_var, 'gage')
        gssha_data_var_name = self.netcdf_attributes[gssha_precip_type]['gssha_name']
        self.data = self.data.lsm.to_projection(gssha_data_var_name,
                                                projection=self.gssha_grid.projection)

        #LOOP THROUGH TIME
        with io_open(out_gage_file, 'w') as gage_file:
            if self.data.dims['time']>1:
                gage_file.write(u"EVENT \"Event of {0} to {1}\"\n".format(self._time_to_string(self.data.lsm.datetime[0]),
                                                                          self._time_to_string(self.data.lsm.datetime[-1])))
            else:
                gage_file.write(u"EVENT \"Event of {0}\"\n".format(self._time_to_string(self.data.lsm.datetime[0])))
            gage_file.write(u"NRPDS {0}\n".format(self.data.dims['time']))
            gage_file.write(u"NRGAG {0}\n".format(self.data.dims['x']*self.data.dims['y']))
            y_coords, x_coords = self.data.lsm.coords
            for y_idx in range(self.data.dims['y']):
                for x_idx in range(self.data.dims['x']):
                    coord_idx = y_idx*self.data.dims['x'] + x_idx
                    gage_file.write(u"COORD {0} {1} \"center of pixel #{2}\"\n".format(x_coords[y_idx, x_idx],
                                                                                       y_coords[y_idx, x_idx],
                                                                                       coord_idx))
            for time_idx in range(self.data.dims['time']):
                date_str = self._time_to_string(self.data.lsm.datetime[time_idx])
                data_str = " ".join(self.data[gssha_data_var_name][time_idx].values.ravel().astype(str))
                gage_file.write(u"{0} {1} {2}\n".format(precip_type, date_str, data_str))

    def _write_hmet_card_file(self, hmet_card_file_path, main_output_folder):
        """
        This function writes the HMET_ASCII card file
        with ASCII file list for input to GSSHA
        """
        with io_open(hmet_card_file_path, 'w') as out_hmet_list_file:
            for hour_time in self.data.lsm.datetime:
                date_str = self._time_to_string(hour_time, "%Y%m%d%H")
                out_hmet_list_file.write(u"{0}\n".format(path.join(main_output_folder, date_str)))


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

        GRIDtoGSSHA Example:

        .. code:: python

            from gsshapy.grid import GRIDtoGSSHA

            #STEP 1: Initialize class
            g2g = GRIDtoGSSHA(gssha_project_folder='/path/to/gssha_project',
                              gssha_project_file_name='gssha_project.prj',
                              lsm_input_folder_path='/path/to/wrf-data',
                              lsm_search_card='*.nc',
                              lsm_lat_var='XLAT',
                              lsm_lon_var='XLONG',
                              lsm_time_var='Times',
                              lsm_lat_dim='south_north',
                              lsm_lon_dim='west_east',
                              lsm_time_dim='Time',
                              )

            #STEP 2: Generate ASCII DATA

            #SEE: http://www.meteo.unican.es/wiki/cordexwrf/OutputVariables

            #EXAMPLE DATA ARRAY 1: WRF GRID DATA BASED
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

            g2g.lsm_data_to_arc_ascii(data_var_map_array)

        HRRRtoGSSHA Example:

        .. code:: python

            from gsshapy.grid import HRRRtoGSSHA

            #STEP 1: Initialize class
            h2g = HRRRtoGSSHA(
                              #YOUR INIT PARAMETERS HERE
                             )

            #STEP 2: Generate ASCII DATA

            #EXAMPLE DATA ARRAY 1: HRRR GRID DATA BASED
            data_var_map_array = [
                                  ['precipitation_rate', 'prate'],
                                  ['pressure', 'sp'],
                                  ['relative_humidity', '2r'],
                                  ['wind_speed', ['10u', '10v']],
                                  ['direct_radiation_cc', ['dswrf', 'tcc']],
                                  ['diffusive_radiation_cc', ['dswrf', 'tcc']],
                                  ['temperature', 't'],
                                  ['cloud_cover_pc' , 'tcc'],
                                 ]

            h2g.lsm_data_to_arc_ascii(data_var_map_array)

        """
        self._check_lsm_input(data_var_map_array)

        if not main_output_folder:
            main_output_folder = path.join(self.gssha_project_folder, "hmet_ascii_data")

        try:
            mkdir(main_output_folder)
        except OSError:
            pass

        log.info("Outputting HMET data to {0}".format(main_output_folder))

        #PART 2: DATA
        for data_var_map in data_var_map_array:
            gssha_data_var, lsm_data_var = data_var_map
            gssha_data_hmet_name = self.netcdf_attributes[gssha_data_var]['hmet_name']
            gssha_data_var_name = self.netcdf_attributes[gssha_data_var]['gssha_name']

            self._load_converted_gssha_data_from_lsm(gssha_data_var, lsm_data_var, 'ascii')
            self._convert_data_to_hourly(gssha_data_var_name)
            self.data = self.data.lsm.to_projection(gssha_data_var_name,
                                                    projection=self.gssha_grid.projection)

            for time_idx in range(self.data.dims['time']):
                arr_grid = ArrayGrid(in_array=self.data[gssha_data_var_name][time_idx].values,
                                     wkt_projection=self.data.lsm.projection.ExportToWkt(),
                                     geotransform=self.data.lsm.geotransform,
                                     )
                date_str = self._time_to_string(self.data.lsm.datetime[time_idx], "%Y%m%d%H")
                ascii_file_path = path.join(main_output_folder,"{0}_{1}.asc".format(date_str, gssha_data_hmet_name))
                arr_grid.to_arc_ascii(ascii_file_path)

        #PART 3: HMET_ASCII card input file with ASCII file list
        hmet_card_file_path = path.join(main_output_folder, 'hmet_file_list.txt')
        self._write_hmet_card_file(hmet_card_file_path, main_output_folder)

    def lsm_data_to_subset_netcdf(self, netcdf_file_path,
                                        data_var_map_array,
                                        resample_method=None):
        """Writes extracted data to the NetCDF file format

        .. todo:: NetCDF output data time is always in UTC time. Need to convert to local timezone for GSSHA.

        .. warning:: The NetCDF GSSHA file is only supported in GSSHA 7 or greater.

        .. note::
            GSSHA CARDS:
                * HMET_NETCDF pointing to the netcdf_file_path
                * LONG_TERM (see: http://www.gsshawiki.com/Long-term_Simulations:Global_parameters)

        Parameters:
            netcdf_file_path(string): Path to output the NetCDF file for GSSHA.
            data_var_map_array(list): Array to map the variables in the LSM file to the
                                      matching required GSSHA data.
            resample_method(Optional[gdalconst]): Resample input method to match hmet data to GSSHA grid for NetCDF output. Default is None.


        GRIDtoGSSHA Example:

        .. code:: python

            from gsshapy.grid import GRIDtoGSSHA

            #STEP 1: Initialize class
            g2g = GRIDtoGSSHA(gssha_project_folder='/path/to/gssha_project',
                              gssha_project_file_name='gssha_project.prj',
                              lsm_input_folder_path='/path/to/wrf-data',
                              lsm_search_card='*.nc',
                              lsm_lat_var='XLAT',
                              lsm_lon_var='XLONG',
                              lsm_time_var='Times',
                              lsm_lat_dim='south_north',
                              lsm_lon_dim='west_east',
                              lsm_time_dim='Time',
                              )

            #STEP 2: Generate NetCDF DATA

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

            g2g.lsm_data_to_subset_netcdf("E/GSSHA/gssha_wrf_data.nc",
                                          data_var_map_array)

        HRRRtoGSSHA Example:

        .. code:: python

            from gsshapy.grid import HRRRtoGSSHA

            #STEP 1: Initialize class
            h2g = HRRRtoGSSHA(
                              #YOUR INIT PARAMETERS HERE
                             )

            #STEP 2: Generate NetCDF DATA

            #EXAMPLE DATA ARRAY 2: HRRR GRID DATA BASED
            data_var_map_array = [
                                  ['precipitation_rate', 'prate'],
                                  ['pressure', 'sp'],
                                  ['relative_humidity', '2r'],
                                  ['wind_speed', ['10u', '10v']],
                                  ['direct_radiation_cc', ['dswrf', 'tcc']],
                                  ['diffusive_radiation_cc', ['dswrf', 'tcc']],
                                  ['temperature', 't'],
                                  ['cloud_cover_pc' , 'tcc'],
                                 ]

            h2g.lsm_data_to_subset_netcdf("E:/GSSHA/gssha_wrf_data.nc",
                                          data_var_map_array)
        """
        self._check_lsm_input(data_var_map_array)

        output_datasets = []
        #DATA
        for gssha_var, lsm_var in data_var_map_array:
            if gssha_var in self.netcdf_attributes:
                self._load_converted_gssha_data_from_lsm(gssha_var, lsm_var, 'netcdf')
                #previously just added data, but needs to be hourly
                gssha_data_var_name = self.netcdf_attributes[gssha_var]['gssha_name']
                self._convert_data_to_hourly(gssha_data_var_name)
                if resample_method:
                    self._resample_data(gssha_data_var_name)
                else:
                    self.data = self.data.lsm.to_projection(gssha_data_var_name,
                                                            projection=self.gssha_grid.projection)

                output_datasets.append(self.data)
            else:
                raise ValueError("Invalid GSSHA variable name: {0} ...".format(gssha_var))
        output_dataset = xr.merge(output_datasets)
        #add global attributes
        output_dataset.attrs['Convention'] = 'CF-1.6'
        output_dataset.attrs['title'] = 'GSSHA LSM Input'
        output_dataset.attrs['history'] = 'date_created: {0}'.format(datetime.utcnow())
        output_dataset.attrs['proj4'] = self.data.attrs['proj4']
        output_dataset.attrs['geotransform'] = self.data.attrs['geotransform']

        output_dataset.to_netcdf(netcdf_file_path)
