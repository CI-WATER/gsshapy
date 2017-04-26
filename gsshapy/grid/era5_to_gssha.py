# -*- coding: utf-8 -*-
#
#  _to_gssha.py
#  GSSHApy
#
#  Created by Alan D Snow, 2016.
#  License BSD 3-Clause

import logging
import numpy as np
import pandas as pd
from os import mkdir, part
from datetime import timedelta
from ecmwfapi import ECMWFDataServer
from os import mkdir, path
import xarray as xr

from .grid_to_gssha import GRIDtoGSSHA

log = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------


def download_era5_for_gssha(main_directory,
                            start_datetime,
                            end_datetime,
                            leftlon=-180,
                            rightlon=180,
                            toplat=90,
                            bottomlat=-90):
    """
    Function to download ERA5 data for GSSHA

    .. note:: https://software.ecmwf.int/wiki/display/CKB/How+to+download+ERA5+test+data+via+the+ECMWF+Web+API

    Args:
        main_directory(:obj:`str`): Location of the output for the forecast data.
        start_datetime(:obj:`str`): Datetime for download start.
        end_datetime(:obj:`str`): Datetime for download end.
        leftlon(Optional[:obj:`float`]): Left bound for longitude. Default is -180.
        rightlon(Optional[:obj:`float`]): Right bound for longitude. Default is 180.
        toplat(Optional[:obj:`float`]): Top bound for latitude. Default is 90.
        bottomlat(Optional[:obj:`float`]): Bottom bound for latitude. Default is -90.


    Example::

        from gsshapy.grid.era5_to_gssha import download_era5_for_gssha

        era5_folder = '/era5'
        leftlon = -95
        rightlon = -75
        toplat = 35
        bottomlat = 30
        download_hrrr_for_gssha(era5_folder, leftlon, rightlon, toplat, bottomlat)

    """
    server = ECMWFDataServer()

    try:
        mkdir(main_directory)
    except OSError:
        pass

    while start_datetime < end_datetime:
        download_file = path.join(main_directory, "era5_gssha_{0}.grib".format(start_datetime.strftime("%Y%m%d")))
        server.retrieve({
            'dataset': "era5_test",
            #  'oper' specifies the high resolution daily data, as opposed to monthly means, wave, eda edmm, etc.
            'stream': "oper",
            #  We want instantaneous parameters, which are archived as type Analysis ('an') as opposed to forecast (fc)
            'type': "an",
            #  Surface level, as opposed to pressure level (pl) or model level (ml)
            'levtype': "sfc",
            # For parameter codes see the ECMWF parameter database at http://apps.ecmwf.int/codes/grib/param-db
            'param': "tcrw/2t/168.128/sp/10u/10v/aluvp/aluvd/tcc",
            # The spatial resolution in ERA5 is 31 km globally on a Gaussian grid.
            # Here we us lat/long with 0.25 degrees, which is approximately the equivalent of 31km.
            'grid': "0.25/0.25",
            # ERA5 provides hourly analysis
            'time': "00/to/23/by/1",
            # area:  N/W/S/E
            'area': "{toplat}/{leftlon}/{bottomlat)/{rightlon}".format(toplat=toplat,
                                                                       leftlon=leftlon,
                                                                       bottomlat=bottomlat,
                                                                       rightlon=rightlon),
            'date': start_datetime.strftime("%Y-%m-%d"),
            'target': download_file  # Default output format is GRIB
        })
        start_datetime += timedelta(1)


# ------------------------------------------------------------------------------
# MAIN CLASS
# ------------------------------------------------------------------------------
class ERA5toGSSHA(GRIDtoGSSHA):
    """This class converts the ERA5 output data to GSSHA formatted input.
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

        from gsshapy.grid import ERA5toGSSHA

        e2g = ERA5toGSSHA(gssha_project_folder='E:\\GSSHA',
                          gssha_project_file_name='gssha.prj',
                          lsm_input_folder_path='E:\\GSSHA\\era5-data',
                          lsm_search_card="*.grib",
                          )

        # example data var map
        data_var_map_array = [
                               ['precipitation_acc', 'TCRW_GDS0_SFC'],
                               ['pressure', 'SP_GDS0_SFC'],
                               ['relative_humidity', ['2D_GDS0_SFC','2T_GDS0_SFC']],
                               ['wind_speed', ['UGRD_P0_L103_GLC0', 'VGRD_P0_L103_GLC0']],
                               ['direct_radiation', 'ALUVD_GDS0_SFC'],
                               ['diffusive_radiation', 'ALUVP_GDS0_SFC'],
                               ['temperature', '2T_GDS0_SFC'],
                               ['cloud_cover', 'TCC_GDS0_SFC'],
                              ]

    """
    def __init__(self,
                 gssha_project_folder,
                 gssha_project_file_name,
                 lsm_input_folder_path,
                 lsm_search_card,
                 lsm_lat_var='g0_lat_1',
                 lsm_lon_var='g0_lon_2',
                 lsm_time_var='initial_time0_hours',
                 lsm_lat_dim='g0_lat_1',
                 lsm_lon_dim='g0_lon_2',
                 lsm_time_dim='initial_time0_hours',
                 output_timezone=None,
                 ):
        """
        Initializer function for the HRRRtoGSSHA class
        """
        super(ERA5toGSSHA, self).__init__(gssha_project_folder,
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
            self._xd = xr.open_mfdataset(path_to_lsm_files,
                                         autoclose=True,
                                         engine='pynio')
                                         
            self._xd.lsm.y_var = self.lsm_lat_var
            self._xd.lsm.x_var = self.lsm_lon_var
            self._xd.lsm.time_var = self.lsm_time_var
            self._xd.lsm.y_dim = self.lsm_lat_dim
            self._xd.lsm.x_dim = self.lsm_lon_dim
            self._xd.lsm.time_dim = self.lsm_time_dim
            self._xd.lsm.to_datetime()
        return self._xd
