# -*- coding: utf-8 -*-
#
#  nwm_to_gssha.py
#  GSSHApy
#
#  Created by Alan D Snow, 2016.
#  License BSD 3-Clause

import logging
from datetime import timedelta
from os import mkdir, path, remove, rename
import xarray as xr

from .grid_to_gssha import GRIDtoGSSHA

log = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# MAIN CLASS
# ------------------------------------------------------------------------------
class NWMtoGSSHA(GRIDtoGSSHA):
    """This class converts the National Water Model output data to GSSHA formatted input.
    This class inherits from class:`GRIDtoGSSHA`.

    Attributes:
        gssha_project_folder(:obj:`str`): Path to the GSSHA project folder
        gssha_project_file_name(:obj:`str`): Name of the GSSHA elevation grid file.
        lsm_input_folder_path(:obj:`str`): Path to the input folder for the LSM files.
        lsm_search_card(:obj:`str`): Glob search pattern for LSM files. Ex. "*.grib2".
        lsm_lat_var(Optional[:obj:`str`]): Name of the latitude variable in the LSM netCDF files. Defaults to 'lat'.
        lsm_lon_var(Optional[:obj:`str`]): Name of the longitude variable in the LSM netCDF files. Defaults to 'lon'.
        lsm_time_var(Optional[:obj:`str`]): Name of the time variable in the LSM netCDF files. Defaults to 'time'.
        lsm_lat_dim(Optional[:obj:`str`]): Name of the latitude dimension in the LSM netCDF files. Defaults to 'lat'.
        lsm_lon_dim(Optional[:obj:`str`]): Name of the longitude dimension in the LSM netCDF files. Defaults to 'lon'.
        lsm_time_dim(Optional[:obj:`str`]): Name of the time dimension in the LSM netCDF files. Defaults to 'time'.
        output_timezone(Optional[:obj:`tzinfo`]): This is the timezone to output the dates for the data. Default is he GSSHA model timezone. This option does NOT currently work for NetCDF output.

    Example::


        from datetime import datetime
        from gsshapy.grid import NWMtoGSSHA

        n2g = NWMtoGSSHA(gssha_project_folder='E:\\GSSHA',
                         gssha_project_file_name='gssha.prj',
                         lsm_input_folder_path='E:\\GSSHA\\nwm-data',
                         lsm_search_card="*.grib")

        # example rain gage
        out_gage_file = 'E:\\GSSHA\\nwm_rain1.gag'
        n2g.lsm_precip_to_gssha_precip_gage(out_gage_file,
                                            lsm_data_var="RAINRATE",
                                            precip_type="RADAR")

        # example data var map array
        # WARNING: This is not complete
        data_var_map_array = [
            ['precipitation_rate', 'RAINRATE'],
            ['pressure', 'PSFC'],
            ['relative_humidity', ['Q2D','T2D', 'PSFC']],
            ['wind_speed', ['U2D', 'V2D']],
            ['direct_radiation', 'SWDOWN'],  # ???
            ['diffusive_radiation', 'SWDOWN'],  # ???
            ['temperature', 'T2D'],
            ['cloud_cover', '????'],
        ]   
        e2g.lsm_data_to_arc_ascii(data_var_map_array)

    """
    def __init__(self,
                 gssha_project_folder,
                 gssha_project_file_name,
                 lsm_input_folder_path,
                 lsm_search_card="*.nc",
                 lsm_lat_var='y',
                 lsm_lon_var='x',
                 lsm_time_var='time',
                 lsm_lat_dim='y',
                 lsm_lon_dim='x',
                 lsm_time_dim='time',
                 output_timezone=None,
                 ):
        """
        Initializer function for the NWMtoGSSHA class
        """
        super(NWMtoGSSHA, self).__init__(gssha_project_folder,
                                         gssha_project_file_name,
                                         lsm_input_folder_path,
                                         lsm_search_card,
                                         lsm_lat_var,
                                         lsm_lon_var,
                                         lsm_time_var,
                                         lsm_lat_dim,
                                         lsm_lon_dim,
                                         lsm_time_dim,
                                         output_timezone)

    @property
    def xd(self):
        """get xarray dataset file handle to LSM files"""
        if self._xd is None:
            path_to_lsm_files = path.join(self.lsm_input_folder_path,
                                          self.lsm_search_card)
            self._xd = super(NWMtoGSSHA, self).xd
            self._xd.lsm.coords_projected = True
        return self._xd

    def _load_converted_gssha_data_from_lsm(self, gssha_var, lsm_var, load_type):
        """
        This function loads data from LSM and converts to GSSHA format
        """
        super(NWMtoGSSHA, self).\
            _load_converted_gssha_data_from_lsm(gssha_var, lsm_var, load_type)
        self.data.lsm.coords_projected = True
