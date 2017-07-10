# -*- coding: utf-8 -*-
#
#  _to_gssha.py
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
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------
def download_era5_for_gssha(main_directory,
                            start_datetime,
                            end_datetime,
                            leftlon=-180,
                            rightlon=180,
                            toplat=90,
                            bottomlat=-90,
                            precip_only=False):
    """
    Function to download ERA5 data for GSSHA

    .. note:: https://software.ecmwf.int/wiki/display/WEBAPI/Access+ECMWF+Public+Datasets

    Args:
        main_directory(:obj:`str`): Location of the output for the forecast data.
        start_datetime(:obj:`str`): Datetime for download start.
        end_datetime(:obj:`str`): Datetime for download end.
        leftlon(Optional[:obj:`float`]): Left bound for longitude. Default is -180.
        rightlon(Optional[:obj:`float`]): Right bound for longitude. Default is 180.
        toplat(Optional[:obj:`float`]): Top bound for latitude. Default is 90.
        bottomlat(Optional[:obj:`float`]): Bottom bound for latitude. Default is -90.
        precip_only(Optional[bool]): If True, will only download precipitation.

    Example::

        from gsshapy.grid.era_to_gssha import download_era5_for_gssha

        era5_folder = '/era5'
        leftlon = -95
        rightlon = -75
        toplat = 35
        bottomlat = 30
        download_era5_for_gssha(era5_folder, leftlon, rightlon, toplat, bottomlat)

    """
    # parameters: https://software.ecmwf.int/wiki/display/CKB/ERA5_test+data+documentation#ERA5_testdatadocumentation-Parameterlistings

    # import here to make sure it is not required to run
    from ecmwfapi import ECMWFDataServer
    server = ECMWFDataServer()

    try:
        mkdir(main_directory)
    except OSError:
        pass

    download_area = "{toplat}/{leftlon}/{bottomlat}/{rightlon}".format(toplat=toplat,
                                                               leftlon=leftlon,
                                                               bottomlat=bottomlat,
                                                               rightlon=rightlon)
    download_datetime = start_datetime
    while download_datetime <= end_datetime:
        download_file = path.join(main_directory, "era5_gssha_{0}.nc".format(download_datetime.strftime("%Y%m%d")))
        download_date = download_datetime.strftime("%Y-%m-%d")
        if not path.exists(download_file) and not precip_only:
            server.retrieve({
                'dataset': "era5_test",
                #  'oper' specifies the high resolution daily data, as opposed to monthly means, wave, eda edmm, etc.
                'stream': "oper",
                #  We want instantaneous parameters, which are archived as type Analysis ('an') as opposed to forecast (fc)
                'type': "an",
                #  Surface level, as opposed to pressure level (pl) or model level (ml)
                'levtype': "sfc",
                # For parameter codes see the ECMWF parameter database at http://apps.ecmwf.int/codes/grib/param-db
                'param': "2t/2d/sp/10u/10v/tcc",
                # The spatial resolution in ERA5 is 31 km globally on a Gaussian grid.
                # Here we us lat/long with 0.25 degrees, which is approximately the equivalent of 31km.
                'grid': "0.25/0.25",
                # ERA5 provides hourly analysis
                'time': "00/to/23/by/1",
                # area:  N/W/S/E
                'area': download_area,
                'date': download_date,
                'target': download_file,
                'format': 'netcdf',
            })

        era5_request = {
            'dataset': "era5_test",
            'stream': "oper",
            'type': "fc",
            'levtype': "sfc",
            'param': "tp/ssrd",
            'grid': "0.25/0.25",
            'area': download_area,
            'format': 'netcdf',
        }
        prec_download_file = path.join(main_directory, "era5_gssha_{0}_fc.nc".format(download_datetime.strftime("%Y%m%d")))
        loc_download_file0 = path.join(main_directory, "era5_gssha_{0}_0_fc.nc".format(download_datetime.strftime("%Y%m%d")))
        loc_download_file1 = path.join(main_directory, "era5_gssha_{0}_1_fc.nc".format(download_datetime.strftime("%Y%m%d")))
        loc_download_file2 = path.join(main_directory, "era5_gssha_{0}_2_fc.nc".format(download_datetime.strftime("%Y%m%d")))
        if download_datetime <= start_datetime and not path.exists(loc_download_file0):
            loc_download_date = (download_datetime-timedelta(1)).strftime("%Y-%m-%d")
            # precipitation 0000-0600
            era5_request['step'] = "6/to/12/by/1"
            era5_request['time'] = "18"
            era5_request['target'] = loc_download_file0
            era5_request['date'] = loc_download_date
            server.retrieve(era5_request)

        if download_datetime == end_datetime and not path.exists(loc_download_file1):
            loc_download_date = download_datetime.strftime("%Y-%m-%d")
            # precipitation 0600-1800
            era5_request['step'] = "1/to/12/by/1"
            era5_request['time'] = "06"
            era5_request['target'] = loc_download_file1
            era5_request['date'] = loc_download_date
            server.retrieve(era5_request)
        if download_datetime == end_datetime and not path.exists(loc_download_file2):
            loc_download_date = download_datetime.strftime("%Y-%m-%d")
            # precipitation 1800-2300
            era5_request['step'] = "1/to/5/by/1"
            era5_request['time'] = "18"
            era5_request['target'] = loc_download_file2
            era5_request['date'] = loc_download_date
            server.retrieve(era5_request)
        if download_datetime < end_datetime and not path.exists(prec_download_file):
            # precipitation 0600-0600 (next day)
            era5_request['step'] = "1/to/12/by/1"
            era5_request['time'] = "06/18"
            era5_request['target'] = prec_download_file
            era5_request['date'] = download_date
            server.retrieve(era5_request)

        download_datetime += timedelta(1)


def download_interim_for_gssha(main_directory,
                               start_datetime,
                               end_datetime,
                               leftlon=-180,
                               rightlon=180,
                               toplat=90,
                               bottomlat=-90,
                               precip_only=False):
    """
    Function to download ERA5 data for GSSHA

    .. note:: https://software.ecmwf.int/wiki/display/WEBAPI/Access+ECMWF+Public+Datasets

    Args:
        main_directory(:obj:`str`): Location of the output for the forecast data.
        start_datetime(:obj:`str`): Datetime for download start.
        end_datetime(:obj:`str`): Datetime for download end.
        leftlon(Optional[:obj:`float`]): Left bound for longitude. Default is -180.
        rightlon(Optional[:obj:`float`]): Right bound for longitude. Default is 180.
        toplat(Optional[:obj:`float`]): Top bound for latitude. Default is 90.
        bottomlat(Optional[:obj:`float`]): Bottom bound for latitude. Default is -90.
        precip_only(Optional[bool]): If True, will only download precipitation.

    Example::

        from gsshapy.grid.era_to_gssha import download_era_interim_for_gssha

        era_interim_folder = '/era_interim'
        leftlon = -95
        rightlon = -75
        toplat = 35
        bottomlat = 30
        download_era_interim_for_gssha(era5_folder, leftlon, rightlon, toplat, bottomlat)

    """
    # parameters: https://software.ecmwf.int/wiki/display/CKB/Details+of+ERA-Interim+parameters

    # import here to make sure it is not required to run
    from ecmwfapi import ECMWFDataServer
    server = ECMWFDataServer()

    try:
        mkdir(main_directory)
    except OSError:
        pass

    download_area = "{toplat}/{leftlon}/{bottomlat}/{rightlon}".format(toplat=toplat,
                                                               leftlon=leftlon,
                                                               bottomlat=bottomlat,
                                                               rightlon=rightlon)
    download_datetime = start_datetime
    interim_request = {
        'dataset': "interim",
        #  'oper' specifies the high resolution daily data, as opposed to monthly means, wave, eda edmm, etc.
        'stream': "oper",
        #  Surface level, as opposed to pressure level (pl) or model level (ml)
        'levtype': "sfc",
        # The spatial resolution in ERA interim is 80 km globally on a Gaussian grid.
        # Here we us lat/long with 0.75 degrees, which is approximately the equivalent of 80km.
        'grid': "0.5/0.5",
        'area': download_area,
        'format': 'netcdf',
    }
    while download_datetime <= end_datetime:
        interim_request['date'] = download_datetime.strftime("%Y-%m-%d")
        if not precip_only:
            download_file = path.join(main_directory, "erai_gssha_{0}_an.nc".format(download_datetime.strftime("%Y%m%d")))
            if not path.exists(download_file):
                #  We want instantaneous parameters, which are archived as type Analysis ('an') as opposed to forecast (fc)
                interim_request['type'] = "an"
                # For parameter codes see the ECMWF parameter database at http://apps.ecmwf.int/codes/grib/param-db
                interim_request['param'] = "2t/2d/sp/10u/10v/tcc"
                # step 0 is analysis, 3-12 is forecast
                interim_request['step'] = "0"
                # ERA Interim provides 6-hourly analysis
                interim_request['time'] = "00/06/12/18"
                interim_request['target'] = download_file
                server.retrieve(interim_request)

            download_file = path.join(main_directory, "erai_gssha_{0}_1_fc.nc".format(download_datetime.strftime("%Y%m%d")))
            if not path.exists(download_file):
                interim_request['type'] = "fc"
                interim_request['param'] = "2t/2d/sp/10u/10v/tcc"
                interim_request['step'] = "3"
                interim_request['time'] = "00/06/12/18"
                interim_request['target'] = download_file
                server.retrieve(interim_request)

        download_file = path.join(main_directory, "erai_gssha_{0}_fc.nc".format(download_datetime.strftime("%Y%m%d")))
        if not path.exists(download_file):
            interim_request['type'] = "fc"
            interim_request['param'] = "tp/ssrd"
            interim_request['step'] = "3/6/9/12"
            interim_request['time'] = "00/12"
            interim_request['target'] = download_file
            server.retrieve(interim_request)
            # TODO: READ FILE AND MODIFY VALUES SO IT IS NOT INCREMENTAL
            # https://software.ecmwf.int/wiki/pages/viewpage.action?pageId=56658233
            # You need  total precipitation for every 6 hours.
            # Daily total precipitation (tp) is only available with a forecast base time 00:00 and 12:00,
            # so to get tp for every 6 hours you will need to extract (and for the second and fourth period calculate):
            # tp(00-06) = (time 00, step 6)
            # tp(06-12) = (time 00, step 12) minus (time 00, step 6)
            # tp(12-18) = (time 12, step 6)
            # tp(18-24) = (time 12, step 12) minus (time 12, step 6)
            # (Note the units for total precipitation is meters.)
            tmp_download_file = download_file + '_tmp'
            with xr.open_dataset(download_file) as xd:
                diff_xd = xd.diff('time')
                xd.tp[1:4] = diff_xd.tp[:3]
                xd.tp[5:] = diff_xd.tp[4:]
                xd.ssrd[1:4] = diff_xd.ssrd[:3]
                xd.ssrd[5:] = diff_xd.ssrd[4:]
                xd.to_netcdf(tmp_download_file)
            remove(download_file)
            rename(tmp_download_file, download_file)

        download_file = path.join(main_directory, "erai_gssha_{0}_0_fc.nc".format(download_datetime.strftime("%Y%m%d")))
        if download_datetime <= start_datetime and not path.exists(download_file):
            loc_download_date = (download_datetime-timedelta(1)).strftime("%Y-%m-%d")
            interim_request['type'] = "fc"
            interim_request['param'] = "tp/ssrd"
            interim_request['step'] = "9/12"
            interim_request['time'] = "12"
            interim_request['target'] = download_file
            interim_request['date'] = loc_download_date
            server.retrieve(interim_request)
            # convert to incremental (see above)
            tmp_download_file = download_file + '_tmp'
            with xr.open_dataset(download_file) as xd:
                inc_xd = xd.diff('time')
                inc_xd.to_netcdf(tmp_download_file)
            remove(download_file)
            rename(tmp_download_file, download_file)
        download_datetime += timedelta(1)


# ------------------------------------------------------------------------------
# MAIN CLASS
# ------------------------------------------------------------------------------
class ERAtoGSSHA(GRIDtoGSSHA):
    """This class converts the ERA5 or ERA Interim output data to GSSHA formatted input.
    This class inherits from class:`GRIDtoGSSHA`.

    .. note:: https://software.ecmwf.int/wiki/display/CKB/How+to+download+ERA5+test+data+via+the+ECMWF+Web+API

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
        download_start_datetime(Optional[:obj:`datetime.datetime`]): Datetime to start download.
        download_end_datetime(Optional[:obj:`datetime.datetime`]): Datetime to end download.
        era_download_data(Optional[:obj:`str`]): You can choose 'era5' or 'interim'. Defaults to 'era5'.

    Example::

        from datetime import datetime
        from gsshapy.grid import ERA5toGSSHA

        e2g = ERA5toGSSHA(gssha_project_folder='E:\\GSSHA',
                          gssha_project_file_name='gssha.prj',
                          lsm_input_folder_path='E:\\GSSHA\\era5-data',
                          lsm_search_card="*.grib",
                          #download_start_datetime=datetime(2016,1,2),
                          #download_end_datetime=datetime(2016,1,4),
                          )


        out_gage_file = 'E:\\GSSHA\\era5_rain1.gag
        e2g.lsm_precip_to_gssha_precip_gage(out_gage_file,
                                            lsm_data_var="tp",
                                            precip_type="GAGES")

        data_var_map_array = [
                               ['precipitation_inc', 'tp'],
                               ['pressure', 'sp'],
                               ['relative_humidity_dew', ['d2m','t2m']],
                               ['wind_speed', ['u10', 'v10']],
                               ['direct_radiation', 'aluvp'],
                               ['diffusive_radiation', 'aluvd'],
                               ['temperature', 't2m'],
                               ['cloud_cover', 'tcc'],
                              ]

        e2g.lsm_data_to_arc_ascii(data_var_map_array)
    """
    def __init__(self,
                 gssha_project_folder,
                 gssha_project_file_name,
                 lsm_input_folder_path,
                 lsm_search_card="*.nc",
                 lsm_lat_var='latitude',
                 lsm_lon_var='longitude',
                 lsm_time_var='time',
                 lsm_lat_dim='latitude',
                 lsm_lon_dim='longitude',
                 lsm_time_dim='time',
                 output_timezone=None,
                 download_start_datetime=None,
                 download_end_datetime=None,
                 era_download_data='era5',
                 ):
        """
        Initializer function for the HRRRtoGSSHA class
        """
        self.download_start_datetime = download_start_datetime
        self.download_end_datetime = download_end_datetime
        if era_download_data.lower() not in ('era5', 'interim'):
            raise ValueError("Invalid option for era_download_data. "
                             "Only 'era5' or 'interim' are supported")
        self.era_download_data = era_download_data.lower()

        super(ERAtoGSSHA, self).__init__(gssha_project_folder,
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

    def _download(self):
        """download ERA5 data for GSSHA domain"""
        # reproject GSSHA grid and get bounds
        min_x, max_x, min_y, max_y = self.gssha_grid.bounds(as_geographic=True)
        if self.era_download_data == 'era5':
            log.info("Downloading ERA5 data ...")
            download_era5_for_gssha(self.lsm_input_folder_path,
                                    self.download_start_datetime,
                                    self.download_end_datetime,
                                    leftlon=min_x-0.5,
                                    rightlon=max_x+0.5,
                                    toplat=max_y+0.5,
                                    bottomlat=min_y-0.5)
        else:
            log.info("Downloading ERA Interim data ...")
            download_interim_for_gssha(self.lsm_input_folder_path,
                                       self.download_start_datetime,
                                       self.download_end_datetime,
                                       leftlon=min_x-1,
                                       rightlon=max_x+1,
                                       toplat=max_y+1,
                                       bottomlat=min_y-1)

    @property
    def xd(self):
        """get xarray dataset file handle to LSM files"""
        if self._xd is None:
            # download files if the user requests
            if None not in (self.download_start_datetime, self.download_end_datetime):
                self._download()

            self._xd = super(ERAtoGSSHA, self).xd
            self._xd.lsm.lon_to_180 = True
        return self._xd

    def _load_converted_gssha_data_from_lsm(self, gssha_var, lsm_var, load_type, time_step=None):
        """
        This function loads data from LSM and converts to GSSHA format
        """
        super(ERAtoGSSHA, self).\
            _load_converted_gssha_data_from_lsm(gssha_var, lsm_var, load_type, time_step)
        self.data.lsm.lon_to_180 = True
