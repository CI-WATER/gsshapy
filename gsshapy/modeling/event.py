# -*- coding: utf-8 -*-
#
#  event.py
#  GSSHApy
#
#  Created by Alan D Snow, 2017.
#  BSD 3-Clause

from datetime import datetime, timedelta
import logging
from numpy import mean
import os
from osgeo import gdal, osr
from pyproj import Proj, transform
from pytz import timezone, utc
from RAPIDpy import RAPIDDataset
from timezonefinder import TimezoneFinder

from ..grid import GRIDtoGSSHA

log = logging.getLogger(__name__)

class Event(object):
    '''
    Object for GSSHA event managment and creation

    An event can consist of various combinations of:
    - Initial Conditions
    - Boundary Conditions
    - Precipitation Events

    Parameters:
        project_manager(ProjectFile): GSSHApy ProjecFile object.
        db_session(Database session): Database session object.
        simulation_start(Optional[datetime]): Date of simulation start.
        simulation_end(Optional[datetime]): Date of simulation end.
        simulation_duration(Optional[timedelta]): Datetime timedelta object with duration of GSSHA simulation.
        load_simulation_datetime(Optional[bool]): If True, this will load in datetime information from the project file. Default is False.
    '''
    PRECIP_INTERP_TYPES = ('THIESSEN', 'INV_DISTANCE')
    ET_CALC_MODES = ("PENMAN", "DEARDORFF")
    EVENT_MODE_CARDS = ('PRECIP_UNIF', 'RAIN_INTENSITY', 'RAIN_DURATION')
    # http://www.gsshawiki.com/Long-term_Simulations:Global_parameters
    LONG_TERM_MODE_CARDS = ('LONG_TERM', 'SEASONAL_RS', 'GMT',
                            'LONGITUDE', 'LATITUDE',
                            'EVENT_MIN_Q', 'SOIL_MOIST_DEPTH',
                            'HMET_ASCII', 'HMET_NETCDF', 'HMET_WES',
                            'HMET_SAMSON', 'HMET_SURFAWAYS', 'HMET_OROG_GAGES',
                            ) + ET_CALC_MODES
    def __init__(self,
                 project_manager,
                 db_session,
                 gssha_directory,
                 simulation_start=None,
                 simulation_end=None,
                 simulation_duration=None,
                 load_simulation_datetime=False,
                 ):

        self.project_manager = project_manager
        self.db_session = db_session
        self.gssha_directory = gssha_directory

        # load time
        end_time = self.project_manager.getCard("END_TIME")
        self.simulation_end = simulation_end
        if end_time and load_simulation_datetime:
            self.simulation_end = datetime.strptime(end_time.value.strip(), "%Y %m %d %H %M")


        duration = self.project_manager.getCard("TOT_TIME")
        self.simulation_duration = simulation_duration
        if duration and load_simulation_datetime:
            self.simulation_duration = timedelta(seconds=float(duration.value.strip())*60.0)

        start_time = self.project_manager.getCard("START_TIME")
        start_date = self.project_manager.getCard("START_DATE")
        if start_time and start_date and load_simulation_datetime:
            stard_date_time_str = start_date.value.strip() + " " + start_time.value.strip()
            self._update_simulation_start(datetime.strptime(stard_date_time_str, "%Y %m %d %H %M"))
        else:
            self._update_simulation_start(simulation_start)

        self._update_centroid_timezone()

    def _update_card(self, card_name, new_value, add_quotes=False):
        """
        Adds/updates card for gssha project file
        """
        self.project_manager.setCard(card_name, new_value, add_quotes)

    def _update_gmt(self):
        """
        Based on timezone and start date, the GMT card is updated
        (ONLY FOR LONG TERM SIMULATIONS)
        """
        return

    def _update_simulation_start(self, simulation_start):
        """
        Update GSSHA simulation start time
        """
        self.simulation_start = simulation_start
        if self.simulation_duration is not None and self.simulation_start is not None:
            self.simulation_end = self.simulation_start + self.simulation_duration
        self._update_simulation_start_cards()

    def _update_simulation_start_cards(self):
        '''
        Update GSSHA cards for simulation start
        '''
        if self.simulation_start is not None:
            self._update_card("START_DATE", self.simulation_start.strftime("%Y %m %d"))
            self._update_card("START_TIME", self.simulation_start.strftime("%H %M"))

    def _update_centroid_timezone(self):
        """
        This function updates the centroid and timezone
        based of off GSSHA elevation grid
        """
        # GET CENTROID FROM GSSHA GRID
        gssha_grid = self.project_manager.getGrid()

        min_x, max_x, min_y, max_y = gssha_grid.bounds()
        x_ext, y_ext = transform(gssha_grid.proj,
                                 Proj(init='epsg:4326'),
                                 [min_x, max_x, min_x, max_x],
                                 [min_y, max_y, max_y, min_y],
                                 )

        self.center_lat = mean(y_ext)
        self.center_lon = mean(x_ext)

        # update time zone
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=self.center_lon, lat=self.center_lat)

        self.tz = timezone(tz_name)

    def set_simulation_duration(self, simulation_duration):
        '''
        set the simulation_duration
        see: http://www.gsshawiki.com/Project_File:Required_Inputs
        ONLY NEEDED FOR EVENT MODE
        '''
        self.simulation_duration = simulation_duration

    def add_precip_file(self, precip_file_path, interpolation_type=None):
        '''
        Adds a precip file to project with interpolation_type
        '''
        # precip file read in
        self._update_card('PRECIP_FILE', precip_file_path, True)

        if interpolation_type is None:
            # check if precip type exists already in card
            if not self.project_manager.getCard('RAIN_INV_DISTANCE') \
                    and not self.project_manager.getCard('RAIN_THIESSEN'):
                # if no type exists, then make it theissen
                self._update_card('RAIN_THIESSEN', '')
        else:
            if interpolation_type.upper() not in self.PRECIP_INTERP_TYPES:
                raise IndexError("Invalid interpolation_type {0}".format(interpolation_type))
            interpolation_type = interpolation_type.upper()

            if interpolation_type == "INV_DISTANCE":
                self._update_card('RAIN_INV_DISTANCE', '')
                self.project_manager.deleteCard('RAIN_THIESSEN', self.db_session)
            else:
                self._update_card('RAIN_THIESSEN', '')
                self.project_manager.deleteCard('RAIN_INV_DISTANCE', self.db_session)

    def prepare_rapid_streamflow(self, path_to_rapid_qout, connection_list_file):
        """
        Prepares RAPID streamflow for GSSHA simulation
        """
        ihg_filename = '{0}.ihg'.format(self.project_manager.name)

        # write out IHG file
        time_index_range = []
        with RAPIDDataset(path_to_rapid_qout, out_tzinfo=self.tz) as qout_nc:

            time_index_range = qout_nc.get_time_index_range(date_search_start=self.simulation_start,
                                                            date_search_end=self.simulation_end)

            if len(time_index_range) > 0:
                time_array = qout_nc.get_time_array(return_datetime=True,
                                                    time_index_array=time_index_range)

                # GSSHA STARTS INGESTING STREAMFLOW AT SECOND TIME STEP
                if self.simulation_start is not None:
                    if self.simulation_start == time_array[0]:
                        log.warn("First timestep of streamflow skipped "
                                 "in order for GSSHA to capture the streamflow.")
                        time_index_range = time_index_range[1:]
                        time_array = time_array[1:]

            if len(time_index_range) > 0:
                start_datetime = time_array[0]

                if self.simulation_start is None:
                   self._update_simulation_start(start_datetime)

                if self.simulation_end is None:
                    self.simulation_end = time_array[-1]

                qout_nc.write_flows_to_gssha_time_series_ihg(ihg_filename,
                                                             connection_list_file,
                                                             date_search_start=start_datetime,
                                                             date_search_end=self.simulation_end,
                                                             )
            else:
                log.warn("No streamflow values found in time range ...")

        if len(time_index_range) > 0:
            # update cards
            self._update_simulation_start_cards()

            self._update_card("END_TIME", self.simulation_end.strftime("%Y %m %d %H %M"))
            self._update_card("CHAN_POINT_INPUT", ihg_filename, True)

            # update duration
            self.set_simulation_duration(self.simulation_end-self.simulation_start)

            # UPDATE GMT CARD
            self._update_gmt()
        else:
            # cleanup
            os.remove(ihg_filename)
            self.project_manager.deleteCard('CHAN_POINT_INPUT', self.db_session)


class EventMode(Event):
    '''
    Object for ensuring required cards are active for EventMode
    '''
    def __init__(self,
                 project_manager,
                 db_session,
                 gssha_directory,
                 simulation_start,
                 simulation_end=None,
                 simulation_duration=None,
                 load_simulation_datetime=False,
                 ):

        if simulation_duration is None and None not in \
                (simulation_start, simulation_end):
            simulation_duration = simulation_end - simulation_start

        super(EventMode, self).__init__(project_manager, db_session,
                                        gssha_directory, simulation_start,
                                        simulation_end, simulation_duration,
                                        load_simulation_datetime)

        # Clean up any long term mode cards
        for long_term_mode_card in self.LONG_TERM_MODE_CARDS:
            self.project_manager.deleteCard(long_term_mode_card, self.db_session)

        if simulation_duration is not None:
            # see: http://www.gsshawiki.com/Project_File:Required_Inputs
            self.set_simulation_duration(simulation_duration)

    def set_simulation_duration(self, simulation_duration):
        '''
        set the simulation_duration
        see: http://www.gsshawiki.com/Project_File:Required_Inputs
        '''
        self.project_manager.setCard('TOT_TIME', str(simulation_duration.total_seconds()/60.0))
        super(EventMode, self).set_simulation_duration(simulation_duration)
        self.simulation_duration = simulation_duration

    def add_uniform_precip_event(self, intensity, duration):
        '''
        Add a uniform precip event
        '''
        self.project_manager.setCard('PRECIP_UNIF', '')
        self.project_manager.setCard('RAIN_INTENSITY', str(intensity))
        self.project_manager.setCard('RAIN_DURATION', str(duration.total_seconds()/60.0))


class LongTermMode(Event):
    '''
    Object for ensuring required cards are active for LongTermMode

    Parameters:
        project_manager(ProjectFile): GSSHApy ProjecFile object.
        project_manager(ProjectFile): GSSHApy ProjecFile object.
        db_session(Database session): Database session object.
        simulation_start(Optional[datetime]): Date of simulation start.
        simulation_end(Optional[datetime]): Date of simulation end.
        load_simulation_datetime(Optional[bool]): If True, this will load in datetime information from the project file. Default is False.
        event_min_q(Optional[double]): Threshold discharge for continuing runoff events in m3/s. Default is 60.0.
        et_calc_mode(Optional[str]): Type of evapo-transpitation calculation for GSSHA. Can be "PENMAN" or "DEARDORFF". Default is "PENMAN".
        soil_moisture_depth(Optional[double]): Depth of the active soil moisture layer from which ET occurs (m). Default is 0.0.
    '''

    def __init__(self,
                 project_manager,
                 db_session,
                 gssha_directory,
                 simulation_start=None,
                 simulation_end=None,
                 simulation_duration=None,
                 load_simulation_datetime=False,
                 event_min_q=None,
                 et_calc_mode=None,
                 soil_moisture_depth=None,
                ):

        super(LongTermMode, self).__init__(project_manager, db_session,
                                           gssha_directory, simulation_start,
                                           simulation_end, simulation_duration,
                                           load_simulation_datetime)

        # Clean up any event mode cards
        for evt_mode_card in self.EVENT_MODE_CARDS:
            self.project_manager.deleteCard(evt_mode_card, self.db_session)
        # UPDATE GSSHA LONG TERM CARDS
        # make sure long term added as it is required for reading in HMET
        self._update_card('LONG_TERM', '')
        self._update_card('SEASONAL_RS', '')
        self._update_card('LATITUDE', str(self.center_lat))
        self._update_card('LONGITUDE', str(self.center_lon))

        # EVENT_MIN_Q
        if event_min_q is None:
            # check if card exists already in card
            if not self.project_manager.getCard('EVENT_MIN_Q'):
                # if no type exists, then make it 0.0
                self._update_card('EVENT_MIN_Q', '0.0')
        else:
            self._update_card('EVENT_MIN_Q', str(event_min_q))

        # SOIL_MOIST_DEPTH
        if soil_moisture_depth is None:
            # check if card exists already in card
            if not self.project_manager.getCard('SOIL_MOIST_DEPTH'):
                # if no type exists, then make it 0.0
                self._update_card('SOIL_MOIST_DEPTH', '0.0')
        else:
            self._update_card('SOIL_MOIST_DEPTH', str(soil_moisture_depth))

        # ET CALC
        if et_calc_mode is not None:
            if et_calc_mode.upper() not in self.ET_CALC_MODES:
                raise IndexError("Invalid et_calc_mode {}".format(et_calc_mode))
            et_calc_mode = et_calc_mode.upper()

        if et_calc_mode is None:
            # check if ET calc mode exists already in card
            if not self.project_manager.getCard('ET_CALC_PENMAN') \
                    and not self.project_manager.getCard('ET_CALC_DEARDORFF'):
                # if no type exists, then make it penman
                self._update_card('ET_CALC_PENMAN', '')

        elif et_calc_mode == "PENMAN":
            self._update_card('ET_CALC_PENMAN', '')
            self.project_manager.deleteCard('ET_CALC_DEARDORFF', self.db_session)
        else:
            self._update_card('ET_CALC_DEARDORFF', '')
            self.project_manager.deleteCard('ET_CALC_PENMAN', self.db_session)

    def _update_gmt(self):
        """
        Based on timezone and start date, the GMT card is updated
        """
        if self.simulation_start is not None:
            # NOTE: Because of daylight savings time,
            # offset result depends on time of the year
            offset_string = self.simulation_start.replace(tzinfo=self.tz).strftime('%z')
            if not offset_string:
                offset_string = '0' # assume UTC
            else:
                sign = offset_string[0]
                hr_offset = int(offset_string[1:3]) + int(offset_string[-2:])/60.0
                offset_string = "{0}{1:.1f}".format(sign, hr_offset)

            self._update_card('GMT', offset_string)

    def prepare_lsm_data(self,
                         lsm_folder,
                         lsm_data_var_map_array,
                         lsm_precip_data_var,
                         lsm_precip_type,
                         lsm_lat_var,
                         lsm_lon_var,
                         lsm_time_var,
                         lsm_lat_dim,
                         lsm_lon_dim,
                         lsm_time_dim,
                         lsm_search_card,
                         hmet_ascii_output_folder=None,
                         netcdf_file_path=None,
                         ):
        """
        Prepares LSM output for GSSHA simulation

        Parameters:
            lsm_folder(str): Path to folder with land surface model data. See: *lsm_input_folder_path* variable at :func:`~gsshapy.grid.GRIDtoGSSHA`.
            lsm_data_var_map_array(str): Array with connections for LSM output and GSSHA input. See: :func:`~gsshapy.grid.GRIDtoGSSHA.`
            lsm_precip_data_var(list or str): String of name for precipitation variable name or list of precip variable names.  See: :func:`~gsshapy.grid.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
            lsm_precip_type(str): Type of precipitation. See: :func:`~gsshapy.grid.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
            lsm_lat_var(str): Name of the latitude variable in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
            lsm_lon_var(str): Name of the longitude variable in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
            lsm_time_var(str): Name of the time variable in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
            lsm_lat_dim(str): Name of the latitude variable in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
            lsm_lon_dim(str): Name of the longitude variable in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
            lsm_time_dim(str): Name of the time variable in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
            lsm_search_card(str): Glob search pattern for LSM files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
            hmet_ascii_output_folder(Optional[str]): Path to diretory to output HMET ASCII files. Mutually exclusice with netcdf_file_path. Default is None.
            netcdf_file_path(Optional[str]): If you want the HMET data output as a NetCDF4 file for input to GSSHA. Mutually exclusice with hmet_ascii_output_folder. Default is None.
        """
        gssha_msk_card = self.project_manager.getCard("WATERSHED_MASK")
        if gssha_msk_card is None:
            raise Exception("ERROR: WATERSHED_MASK card not found ...")

        l2g = GRIDtoGSSHA(gssha_project_folder=self.gssha_directory,
                          gssha_project_file_name="{0}.prj".format(self.project_manager.name),
                          lsm_input_folder_path=lsm_folder,
                          lsm_search_card=lsm_search_card,
                          lsm_lat_var=lsm_lat_var,
                          lsm_lon_var=lsm_lon_var,
                          lsm_time_var=lsm_time_var,
                          lsm_lat_dim=lsm_lat_dim,
                          lsm_lon_dim=lsm_lon_dim,
                          lsm_time_dim=lsm_time_dim,
                          output_timezone=self.tz,
                         )

        # SIMULATION TIME CARDS
        if self.simulation_start is None:
            ts = l2g.xd.lsm.datetime[0]
            ts = ts.replace(tzinfo=utc) \
                   .astimezone(tz=self.tz).replace(tzinfo=None)
            self._update_simulation_start(ts)

        self._update_simulation_start_cards()

        # GSSHA simulation does not work after HMET data is finished
        te = l2g.xd.lsm.datetime[-1]
        wrf_simulation_end = te.replace(tzinfo=utc) \
                               .astimezone(tz=self.tz).replace(tzinfo=None)

        if self.simulation_end is None:
            self.simulation_end = wrf_simulation_end
        elif self.simulation_end > wrf_simulation_end:
            self.simulation_end = wrf_simulation_end
        self._update_card("END_TIME", self.simulation_end.strftime("%Y %m %d %H %M"))

        # PRECIPITATION CARDS
        out_gage_file = '{0}.gag'.format(self.project_manager.name)
        l2g.lsm_precip_to_gssha_precip_gage(out_gage_file,
                                            lsm_data_var=lsm_precip_data_var,
                                            precip_type=lsm_precip_type)

        # precip file read in
        self.add_precip_file(out_gage_file)

        # HMET CARDS
        if netcdf_file_path is not None:
            l2g.lsm_data_to_subset_netcdf(netcdf_file_path, lsm_data_var_map_array)
            self._update_card("HMET_NETCDF", netcdf_file_path, True)
            self.project_manager.deleteCard('HMET_ASCII', self.db_session)
        else:
            if "{0}" in hmet_ascii_output_folder and "{1}" in hmet_ascii_output_folder:
                hmet_ascii_output_folder = hmet_ascii_output_folder.format(self.simulation_start.strftime("%Y%m%d%H%M"),
                                                                           self.simulation_end.strftime("%Y%m%d%H%M"))
            l2g.lsm_data_to_arc_ascii(lsm_data_var_map_array, main_output_folder=os.path.join(self.gssha_directory,
                                                                                                   hmet_ascii_output_folder))
            self._update_card("HMET_ASCII", os.path.join(hmet_ascii_output_folder, 'hmet_file_list.txt'), True)
            self.project_manager.deleteCard('HMET_NETCDF', self.db_session)

        # make sure xarray dataset closed
        l2g.xd.close()

        # UPDATE GMT CARD
        self._update_gmt()
