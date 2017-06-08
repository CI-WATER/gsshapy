# -*- coding: utf-8 -*-
#
#  framework.py
#  GSSHApy
#
#  Created by Alan D Snow, 2016.
#  BSD 3-Clause

from distutils.spawn import find_executable
from glob import glob
import logging
import os
from shutil import copy, move
import subprocess

log = logging.getLogger(__name__)

try:
    from spt_dataset_manager import ECMWFRAPIDDatasetManager
except ImportError:
    log.warn("spt_dataset_manager is not installed. The SPT functionality will not work.")
    pass

from ..lib import db_tools as dbt
from .event import EventMode, LongTermMode
from ..util.context import tmp_chdir


def replace_file(from_file, to_file):
    """
    Replaces to_file with from_file
    """
    try:
        os.remove(to_file)
    except OSError:
        pass
    copy(from_file, to_file)


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
        gssha_simulation_start(Optional[datetime]): Datetime object with date of start of GSSHA simulation.
        gssha_simulation_end(Optional[datetime]): Datetime object with date of end of GSSHA simulation.
        gssha_simulation_duration(Optional[timedelta]): Datetime timedelta object with duration of GSSHA simulation.
        load_simulation_datetime(Optional[bool]): If True, this will load in datetime information from the project file. Default is False.
        spt_watershed_name(Optional[str]): Streamflow Prediction Tool watershed name.
        spt_subbasin_name(Optional[str]): Streamflow Prediction Tool subbasin name.
        spt_forecast_date_string(Optional[str]): Streamflow Prediction Tool forecast date string.
        ckan_engine_url(Optional[str]): CKAN engine API url.
        ckan_api_key(Optional[str]): CKAN api key.
        ckan_owner_organization(Optional[str]): CKAN owner organization.
        path_to_rapid_qout(Optional[str]): Path to the RAPID Qout file. Use this if you do NOT want to download the forecast and you want to use RAPID streamflows.
        connection_list_file(Optional[str]): CSV file with list connecting GSSHA rivers to RAPID river network. See: http://rapidpy.readthedocs.io/en/latest/rapid_to_gssha.html
        lsm_folder(Optional[str]): Path to folder with land surface model data. See: *lsm_input_folder_path* variable at :func:`~gsshapy.grid.GRIDtoGSSHA`.
        lsm_data_var_map_array(Optional[str]): Array with connections for LSM output and GSSHA input. See: :func:`~gsshapy.grid.GRIDtoGSSHA.`
        lsm_precip_data_var(Optional[list or str]): String of name for precipitation variable name or list of precip variable names.  See: :func:`~gsshapy.grid.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
        lsm_precip_type(Optional[str]): Type of precipitation. See: :func:`~gsshapy.grid.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
        lsm_lat_var(Optional[str]): Name of the latitude variable in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
        lsm_lon_var(Optional[str]): Name of the longitude variable in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
        lsm_time_var(Optional[str]): Name of the time variable in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
        lsm_lat_dim(Optional[str]): Name of the latitude dimension in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
        lsm_lon_dim(Optional[str]): Name of the longitude dimension in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
        lsm_time_dim(Optional[str]): Name of the time dimension in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
        lsm_search_card(Optional[str]): Glob search pattern for LSM files. See: :func:`~gsshapy.grid.grid_to_gssha.GRIDtoGSSHA`.
        precip_interpolation_type(Optional[str]): Type of interpolation for LSM precipitation. Can be "INV_DISTANCE" or "THIESSEN". Default is "THIESSEN".
        event_min_q(Optional[double]): Threshold discharge for continuing runoff events in m3/s. Default is 60.0.
        et_calc_mode(Optional[str]): Type of evapo-transpitation calculation for GSSHA. Can be "PENMAN" or "DEARDORFF". Default is "PENMAN".
        soil_moisture_depth(Optional[double]): Depth of the active soil moisture layer from which ET occurs (m). Default is 0.0.
        output_netcdf(Optional[bool]): If you want the HMET data output as a NetCDF4 file for input to GSSHA. Default is False.
        write_hotstart(Optional[bool]): If you want to automatically generate all hotstart files, set to True. Default is False.
        read_hotstart(Optional[bool]): If you want to automatically search for and read in hotstart files, set to True. Default is False.
        hotstart_minimal_mode(Optional[bool]): If you want to turn off all outputs to only generate the hotstart file, set to True. Default is False.
        grid_module(:obj:`str`): The name of the LSM tool needed. Options are 'grid', 'hrrr', or 'era'. Default is 'grid'.

    Example modifying parameters during class initialization:

    .. code:: python

            from gsshapy.modeling import GSSHAFramework

            gssha_executable = 'C:/Program Files/WMS 10.1 64-bit/gssha/gssha.exe'
            gssha_directory = "C:/Users/{username}/Documents/GSSHA"
            project_filename = "gssha_project.prj"

            #WRF INPUTS
            lsm_folder = '"C:/Users/{username}/Documents/GSSHA/wrf-sample-data-v1.0'
            lsm_lat_var = 'XLAT'
            lsm_lon_var = 'XLONG'
            search_card = '*.nc'
            precip_data_var = ['RAINC', 'RAINNC']
            precip_type = 'ACCUM'

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
                                lsm_folder=lsm_folder,
                                lsm_data_var_map_array=data_var_map_array,
                                lsm_precip_data_var=precip_data_var,
                                lsm_precip_type=precip_type,
                                lsm_lat_var=lsm_lat_var,
                                lsm_lon_var=lsm_lon_var,
                                )

            gr.run_forecast()
    """
    GSSHA_REQUIRED_OUTPUT_PATH_CARDS = (
                                        "SUMMARY",
                                        "OUTLET_HYDRO",
                                        "OUTLET_SED_FLUX",
                                        "OUTLET_SED_TSS",
                                        "SUPERLINK_JUNC_FLOW",
                                        "SUPERLINK_NODE_FLOW",
                                        )

    GSSHA_OPTIONAL_OUTPUT_PATH_CARDS = (
                                        "OUT_THETA_LOCATION",
                                        "OUT_HYD_LOCATION",
                                        "OUT_DEP_LOCATION",
                                        "OUT_SED_LOC",
                                        "OUT_TSS_LOC",
                                        "MAX_SED_FLUX",
                                        "CHAN_DEPTH",
                                        "CHAN_STAGE",
                                        "CHAN_DISCHARGE",
                                        "CHAN_VELOCITY",
                                        "LAKE_OUTPUT",
                                        "GW_OUTPUT",
                                        "OUT_GWFLUX_LOCATION",
                                        "GW_RECHARGE_CUM",
                                        "GW_RECHARGE_INC",
                                        "GW_WELL_LEVEL",
                                        "OUT_CON_LOCATION",
                                        "OUT_MASS_LOCATION",
                                        "NET_SED_VOLUME",
                                        "VOL_SED_SUSP",
                                        "OVERLAND_DEPTHS",
                                        "OVERLAND_WSE",
                                        "DISCHARGE",
                                        "DEPTH",
                                        "INF_DEPTH",
                                        "SURF_MOIST",
                                        "RATE_OF_INFIL",
                                        "DIS_RAIN",
                                        "FLOOD_GRID",
                                        "FLOOD_STREAM",
                                        )
    GSSHA_OPTIONAL_OUTPUT_CARDS = (
                                  "IN_THETA_LOCATION",
                                  "IN_HYD_LOCATION",
                                  "IN_SED_LOC",
                                  "OVERLAND_DEPTH_LOCATION",
                                  "OVERLAND_WSE_LOCATION",
                                  "IN_GWFLUX_LOCATION",
                                  "OUT_WELL_LOCATION",
                                  "STRICT_JULIAN_DATE",
                                  "OPTIMIZE",
                                  "OPTIMIZE_SED",
                                  ) + GSSHA_OPTIONAL_OUTPUT_PATH_CARDS

    def __init__(self,
                 gssha_executable,
                 gssha_directory,
                 project_filename,
                 gssha_simulation_start=None,
                 gssha_simulation_end=None,
                 gssha_simulation_duration=None,
                 load_simulation_datetime=False,
                 spt_watershed_name=None,
                 spt_subbasin_name=None,
                 spt_forecast_date_string=None,
                 ckan_engine_url=None,
                 ckan_api_key=None,
                 ckan_owner_organization=None,
                 path_to_rapid_qout=None,
                 connection_list_file=None,
                 lsm_folder=None,
                 lsm_data_var_map_array=None,
                 lsm_precip_data_var=None,
                 lsm_precip_type=None,
                 lsm_lat_var=None,
                 lsm_lon_var=None,
                 lsm_time_var='time',
                 lsm_lat_dim=None,
                 lsm_lon_dim=None,
                 lsm_time_dim='time',
                 lsm_search_card="*.nc",
                 precip_interpolation_type=None,
                 event_min_q=None,
                 et_calc_mode=None,
                 soil_moisture_depth=None,
                 output_netcdf=False,
                 write_hotstart=False,
                 read_hotstart=False,
                 hotstart_minimal_mode=False,
                 grid_module='grid',
                 ):
        """
        Initializer
        """
        self.gssha_executable = gssha_executable
        self.gssha_directory = gssha_directory
        self.project_filename = project_filename
        self.spt_watershed_name = spt_watershed_name
        self.spt_subbasin_name = spt_subbasin_name
        self.spt_forecast_date_string = spt_forecast_date_string
        self.ckan_engine_url = ckan_engine_url
        self.ckan_api_key = ckan_api_key
        self.ckan_owner_organization = ckan_owner_organization
        self.path_to_rapid_qout = path_to_rapid_qout
        self.connection_list_file = connection_list_file
        self.lsm_folder = lsm_folder
        self.lsm_data_var_map_array = lsm_data_var_map_array
        self.lsm_precip_data_var = lsm_precip_data_var
        self.lsm_precip_type = lsm_precip_type
        self.precip_interpolation_type = precip_interpolation_type
        self.output_netcdf = output_netcdf
        self.write_hotstart = write_hotstart
        self.read_hotstart = read_hotstart
        self.hotstart_minimal_mode = hotstart_minimal_mode

        self.simulation_modified_input_cards = ["MAPPING_TABLE"]

        # get project manager and session
        self.project_manager, db_sessionmaker = \
            dbt.get_project_session(os.path.splitext(self.project_filename)[0],
                                    self.gssha_directory)

        self.db_session = db_sessionmaker()
        self.project_manager.read(directory=self.gssha_directory,
                                  filename=self.project_filename,
                                  session=self.db_session)
        # read event manager card if exists
        eventyml_card = self.project_manager.getCard('#GSSHAPY_EVENT_YML')
        if eventyml_card is not None:
            self.project_manager.readInputFile('#GSSHAPY_EVENT_YML',
                                               directory=self.gssha_directory,
                                               session=self.db_session)

        # generate event manager card if does not exist already
        else:
            prj_evt_manager = self.project_manager.INPUT_FILES['#GSSHAPY_EVENT_YML']()
            self.db_session.add(prj_evt_manager)
            prj_evt_manager.projectFile = self.project_manager
            prj_evt_manager.write(directory=self.gssha_directory,
                                  name='gsshapy_event.yml',
                                  session=self.db_session)
            self.project_manager.setCard(name='#GSSHAPY_EVENT_YML',
                                         value='gsshapy_event.yml',
                                         add_quotes=True)
            self.project_manager.write(directory=self.gssha_directory,
                                       name=self.project_filename,
                                       session=self.db_session)
            self.db_session.commit()

        required_grid_args = (grid_module, lsm_folder, lsm_search_card,
                              lsm_lat_var, lsm_lon_var, lsm_time_var,
                              lsm_lat_dim, lsm_lon_dim, lsm_time_dim)

        self.lsm_input_valid = None not in required_grid_args

        if self._prepare_lsm_hmet:
            self.event_manager = LongTermMode(project_manager=self.project_manager,
                                              db_session=self.db_session,
                                              gssha_directory=self.gssha_directory,
                                              simulation_start=gssha_simulation_start,
                                              simulation_end=gssha_simulation_end,
                                              simulation_duration=gssha_simulation_duration,
                                              load_simulation_datetime=load_simulation_datetime,
                                              lsm_folder=lsm_folder,
                                              lsm_search_card=lsm_search_card,
                                              lsm_lat_var=lsm_lat_var,
                                              lsm_lon_var=lsm_lon_var,
                                              lsm_time_var=lsm_time_var,
                                              lsm_lat_dim=lsm_lat_dim,
                                              lsm_lon_dim=lsm_lon_dim,
                                              lsm_time_dim=lsm_time_dim,
                                              grid_module=grid_module,
                                              event_min_q=event_min_q,
                                              et_calc_mode=et_calc_mode,
                                              soil_moisture_depth=soil_moisture_depth)
        else:
            self.event_manager = EventMode(project_manager=self.project_manager,
                                           db_session=self.db_session,
                                           gssha_directory=self.gssha_directory,
                                           simulation_start=gssha_simulation_start,
                                           simulation_end=gssha_simulation_end,
                                           simulation_duration=gssha_simulation_duration,
                                           load_simulation_datetime=load_simulation_datetime,
                                           lsm_folder=lsm_folder,
                                           lsm_search_card=lsm_search_card,
                                           lsm_lat_var=lsm_lat_var,
                                           lsm_lon_var=lsm_lon_var,
                                           lsm_time_var=lsm_time_var,
                                           lsm_lat_dim=lsm_lat_dim,
                                           lsm_lon_dim=lsm_lon_dim,
                                           lsm_time_dim=lsm_time_dim,
                                           grid_module=grid_module)

    @property
    def _prepare_lsm_hmet(self):
        """
        Determines whether to prepare HMET data from LSM
        """
        return self.lsm_input_valid and self.lsm_data_var_map_array

    @property
    def _prepare_lsm_gag(self):
        """
        Determines whether to prepare gage data from LSM
        """
        lsm_required_vars = (self.lsm_precip_data_var,
                             self.lsm_precip_type)

        return self.lsm_input_valid and (None not in lsm_required_vars)

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
        self.project_manager.setCard(card_name, new_value, add_quotes)

    def _delete_card(self, card_name):
        """
        Removes card for gssha project file
        """
        self.project_manager.deleteCard(card_name, self.db_session)

    def _update_card_file_location(self, card_name, new_directory):
        """
        Moves card to new gssha working directory
        """
        with tmp_chdir(self.gssha_directory):
            file_card = self.project_manager.getCard(card_name)
            if file_card:
                if file_card.value:
                    original_location = file_card.value.strip("'").strip('"')
                    new_location = os.path.join(new_directory,
                                                os.path.basename(original_location))
                    file_card.value = '"{0}"'.format(os.path.basename(original_location))
                    try:
                        move(original_location, new_location)
                    except OSError as ex:
                        log.warn(ex)
                        pass

    def download_spt_forecast(self, extract_directory):
        """
        Downloads Streamflow Prediction Tool forecast data
        """
        needed_vars = (self.spt_watershed_name,
                       self.spt_subbasin_name,
                       self.spt_forecast_date_string,
                       self.ckan_engine_url,
                       self.ckan_api_key,
                       self.ckan_owner_organization)

        if None not in needed_vars:

            er_manager = ECMWFRAPIDDatasetManager(self.ckan_engine_url,
                                                  self.ckan_api_key,
                                                  self.ckan_owner_organization)
            # TODO: Modify to only download one of the forecasts in the ensemble
            er_manager.download_prediction_dataset(watershed=self.spt_watershed_name,
                                                   subbasin=self.spt_subbasin_name,
                                                   date_string=self.spt_forecast_date_string,  # '20160711.1200'
                                                   extract_directory=extract_directory)

            return glob(os.path.join(extract_directory, self.spt_forecast_date_string, "Qout*52.nc"))[0]

        elif needed_vars.count(None) == len(needed_vars):
            log.info("Skipping streamflow forecast download ...")
            return None
        else:
            raise ValueError("To download the forecasts, you need to set: \n"
                             "spt_watershed_name, spt_subbasin_name, spt_forecast_date_string \n"
                             "ckan_engine_url, ckan_api_key, and ckan_owner_organization.")

    def prepare_hmet(self):
        """
        Prepare HMET data for simulation
        """
        if self._prepare_lsm_hmet:
            netcdf_file_path = None
            hmet_ascii_output_folder = None
            if self.output_netcdf:
                netcdf_file_path = '{0}_hmet.nc'.format(self.project_manager.name)
                if self.hotstart_minimal_mode:
                    netcdf_file_path = '{0}_hmet_hotstart.nc'.format(self.project_manager.name)
            else:
                hmet_ascii_output_folder = 'hmet_data_{0}to{1}'
                if self.hotstart_minimal_mode:
                    hmet_ascii_output_folder += "_hotstart"

            self.event_manager.prepare_hmet_lsm(self.lsm_data_var_map_array,
                                                hmet_ascii_output_folder,
                                                netcdf_file_path)
            self.simulation_modified_input_cards += ["HMET_NETCDF",
                                                     "HMET_ASCII"]
        else:
            log.info("HMET preparation skipped due to missing parameters ...")

    def prepare_gag(self):
        """
        Prepare gage data for simulation
        """
        if self._prepare_lsm_gag:
            self.event_manager.prepare_gag_lsm(self.lsm_precip_data_var,
                                               self.lsm_precip_type,
                                               self.precip_interpolation_type)
            self.simulation_modified_input_cards.append("PRECIP_FILE")
        else:
            log.info("Gage file preparation skipped due to missing parameters ...")

    def rapid_to_gssha(self):
        """
        Prepare RAPID data for simulation
        """
        # if no streamflow given, download forecast
        if self.path_to_rapid_qout is None and self.connection_list_file:
            rapid_qout_directory = os.path.join(self.gssha_directory, 'rapid_streamflow')
            try:
                os.mkdir(rapid_qout_directory)
            except OSError:
                pass
            self.path_to_rapid_qout = self.download_spt_forecast(rapid_qout_directory)

        # prepare input for GSSHA if user wants
        if self.path_to_rapid_qout is not None and self.connection_list_file:
            self.event_manager.prepare_rapid_streamflow(self.path_to_rapid_qout,
                                                        self.connection_list_file)
            self.simulation_modified_input_cards.append('CHAN_POINT_INPUT')

    def hotstart(self):
        """
        Prepare simulation hotstart info
        """
        if self.write_hotstart:
            hotstart_time_str = self.event_manager.simulation_end.strftime("%Y%m%d_%H%M")
            try:
                os.mkdir('hotstart')
            except OSError:
                pass

            ov_hotstart_path = os.path.join('..', 'hotstart',
                                            '{0}_ov_hotstart_{1}.ovh'.format(self.project_manager.name,
                                                                             hotstart_time_str))
            self._update_card("WRITE_OV_HOTSTART", ov_hotstart_path, True)
            chan_hotstart_path = os.path.join('..', 'hotstart',
                                              '{0}_chan_hotstart_{1}'.format(self.project_manager.name,
                                                                             hotstart_time_str))
            self._update_card("WRITE_CHAN_HOTSTART", chan_hotstart_path, True)
            sm_hotstart_path = os.path.join('..', 'hotstart',
                                           '{0}_sm_hotstart_{1}.smh'.format(self.project_manager.name,
                                                                            hotstart_time_str))
            self._update_card("WRITE_SM_HOTSTART", sm_hotstart_path, True)
        else:
            self._delete_card("WRITE_OV_HOTSTART")
            self._delete_card("WRITE_CHAN_HOTSTART")
            self._delete_card("WRITE_SM_HOTSTART")

        if self.read_hotstart:
            hotstart_time_str = self.event_manager.simulation_start.strftime("%Y%m%d_%H%M")
            # OVERLAND
            expected_ov_hotstart = os.path.join('hotstart',
                                                '{0}_ov_hotstart_{1}.ovh'.format(self.project_manager.name,
                                                                                  hotstart_time_str))
            if os.path.exists(expected_ov_hotstart):
                self._update_card("READ_OV_HOTSTART", os.path.join("..", expected_ov_hotstart), True)
            else:
                self._delete_card("READ_OV_HOTSTART")
                log.warn("READ_OV_HOTSTART not included as "
                         "{0} does not exist ...".format(expected_ov_hotstart))

            # CHANNEL
            expected_chan_hotstart = os.path.join('hotstart',
                                                  '{0}_chan_hotstart_{1}'.format(self.project_manager.name,
                                                                                 hotstart_time_str))
            if os.path.exists("{0}.qht".format(expected_chan_hotstart)) \
                    and os.path.exists("{0}.dht".format(expected_chan_hotstart)):
                self._update_card("READ_CHAN_HOTSTART", os.path.join("..", expected_chan_hotstart), True)
            else:
                self._delete_card("READ_CHAN_HOTSTART")
                log.warn("READ_CHAN_HOTSTART not included as "
                         "{0}.qht and/or {0}.dht does not exist ...".format(expected_chan_hotstart))

            # INFILTRATION
            expected_sm_hotstart = os.path.join('hotstart',
                                                '{0}_sm_hotstart_{1}.smh'.format(self.project_manager.name,
                                                                                 hotstart_time_str))
            if os.path.exists(expected_sm_hotstart):
                self._update_card("READ_SM_HOTSTART", os.path.join("..", expected_sm_hotstart), True)
            else:
                self._delete_card("READ_SM_HOTSTART")
                log.warn("READ_SM_HOTSTART not included as"
                         " {0} does not exist ...".format(expected_sm_hotstart))

    def run(self, subdirectory=None):
        """
        Write out project file and run GSSHA simulation
        """
        with tmp_chdir(self.gssha_directory):
            if self.hotstart_minimal_mode:
                # remove all optional output cards
                for gssha_optional_output_card in self.GSSHA_OPTIONAL_OUTPUT_CARDS:
                    self._delete_card(gssha_optional_output_card)
                # make sure running in SUPER_QUIET mode
                self._update_card('SUPER_QUIET', '')
                if subdirectory is None:
                    # give execute folder name
                    subdirectory = "minimal_hotstart_run_{0}to{1}" \
                                   .format(self.event_manager.simulation_start.strftime("%Y%m%d%H%M"),
                                           self.event_manager.simulation_end.strftime("%Y%m%d%H%M"))
            else:
                # give execute folder name
                subdirectory = "run_{0}to{1}".format(self.event_manager.simulation_start.strftime("%Y%m%d%H%M"),
                                                     self.event_manager.simulation_end.strftime("%Y%m%d%H%M"))

            # ensure unique folder naming conventions and add to exisitng event manager
            prj_evt_manager = self.project_manager.projectFileEventManager
            prj_event = prj_evt_manager.add_event(name=subdirectory,
                                                  subfolder=subdirectory,
                                                  session=self.db_session)
            eventyml_path = self.project_manager.getCard('#GSSHAPY_EVENT_YML') \
                                                .value.strip("'").strip('"')
            prj_evt_manager.write(session=self.db_session,
                                  directory=self.gssha_directory,
                                  name=os.path.basename(eventyml_path))
            # ensure event manager not propagated to child event
            self.project_manager.deleteCard('#GSSHAPY_EVENT_YML',
                                            db_session=self.db_session)
            self.db_session.delete(self.project_manager.projectFileEventManager)
            self.db_session.commit()

            # make working directory
            working_directory = os.path.join(self.gssha_directory, prj_event.subfolder)
            try:
                os.mkdir(working_directory)
            except OSError:
                pass

            # move simulation generated files to working directory
            # PRECIP_FILE, HMET_NETCDF, HMET_ASCII, CHAN_POINT_INPUT
            # TODO: Move HMET_ASCII files
            for sim_card in self.simulation_modified_input_cards:
                if sim_card != 'MAPPING_TABLE':
                    self._update_card_file_location(sim_card, working_directory)

            mapping_table_card = self.project_manager.getCard('MAPPING_TABLE')
            if mapping_table_card:
                # read in mapping table
                map_table_object = self.project_manager.readInputFile('MAPPING_TABLE',
                                                                      self.gssha_directory,
                                                                      self.db_session,
                                                                      readIndexMaps=False)

                # connect index maps to main gssha directory
                for indexMap in map_table_object.indexMaps:
                    indexMap.filename = os.path.join("..", os.path.basename(indexMap.filename))

                # write copy of mapping table to working directory
                map_table_filename = os.path.basename(mapping_table_card.value.strip("'").strip('"'))
                map_table_object.write(session=self.db_session,
                                       directory=working_directory,
                                       name=map_table_filename,
                                       writeIndexMaps=False)

            # connect to other output files in main gssha directory
            for gssha_card in self.project_manager.projectCards:
                if gssha_card.name not in self.GSSHA_REQUIRED_OUTPUT_PATH_CARDS + \
                                            self.GSSHA_OPTIONAL_OUTPUT_PATH_CARDS + \
                                            tuple(self.simulation_modified_input_cards):
                    if gssha_card.value:
                        updated_value = gssha_card.value.strip('"').strip("'")
                        if updated_value:
                            if gssha_card.name == "READ_CHAN_HOTSTART":
                                # there are two required files
                                # the .dht and .qht
                                if os.path.exists(updated_value + '.dht') \
                                        and os.path.exists(updated_value + '.qht'):
                                    updated_path = os.path.join("..", os.path.basename(updated_value))
                                    gssha_card.value = '"{0}"'.format(updated_path)
                            elif os.path.exists(updated_value):
                                updated_path = os.path.join("..", os.path.basename(updated_value))
                                gssha_card.value = '"{0}"'.format(updated_path)
                            elif gssha_card.name == '#INDEXGRID_GUID':
                                path_split = updated_value.split()
                                updated_path = os.path.basename(path_split[0].strip('"').strip("'"))
                                if os.path.exists(updated_path):
                                    new_path = os.path.join("..", os.path.basename(updated_path))
                                    try:
                                        # Get WMS ID for Index Map as part of value
                                        gssha_card.value = '"{0}" "{1}"'.format(new_path, path_split[1])
                                    except:
                                        # Like normal if the ID isn't there
                                        gssha_card.value = '"{0}"'.format(new_path)
                                else:
                                    log.warn("{0} {1} not found in project directory ...".format("#INDEXGRID_GUID", updated_path))

            # make sure project path is ""
            self._update_card("PROJECT_PATH", "", True)

            # WRITE OUT UPDATED GSSHA PROJECT FILE
            self.project_manager.write(session=self.db_session,
                                       directory=working_directory,
                                       name=self.project_manager.name)

            with tmp_chdir(working_directory):
                # RUN SIMULATION
                if self.gssha_executable and find_executable(self.gssha_executable) is not None:
                    log.info("Running GSSHA simulation ...")

                    try:
                        run_gssha_command = [self.gssha_executable,
                                             os.path.join(working_directory, self.project_filename)]
                        # run GSSHA
                        out = subprocess.check_output(run_gssha_command)

                        # write out GSSHA output
                        log_file_path = os.path.join(working_directory, 'simulation.log')
                        with open(log_file_path, mode='w') as logfile:
                            logfile.write(out.decode('utf-8'))
                            # log to other logger if debug mode on
                            if log.isEnabledFor(logging.DEBUG):
                                for line in out.split(b'\n'):
                                    log.debug(line.decode('utf-8'))

                    except subprocess.CalledProcessError as ex:
                        log.error("{0}: {1}".format(ex.returncode, ex.output))

                else:
                    log.warning("GSSHA executable not found. Skipping GSSHA simulation run ...")

            return working_directory

    def run_forecast(self):

        """
        Updates card & runs for RAPID to GSSHA & LSM to GSSHA
        """
        # ----------------------------------------------------------------------
        # LSM to GSSHA
        # ----------------------------------------------------------------------
        self.prepare_hmet()
        self.prepare_gag()

        # ----------------------------------------------------------------------
        # RAPID to GSSHA
        # ----------------------------------------------------------------------
        self.rapid_to_gssha()

        # ----------------------------------------------------------------------
        # HOTSTART
        # ----------------------------------------------------------------------
        self.hotstart()

        # ----------------------------------------------------------------------
        # Run GSSHA
        # ----------------------------------------------------------------------
        return self.run()


class GSSHAWRFFramework(GSSHAFramework):
    """
    This class is for automating the connection between RAPID to GSSHA and WRF to GSSHA.
    There are several different configurations depending upon what you choose.

    There are three options for RAPID to GSSHA:

    1. Download and run using forecast from the Streamflow Prediction Tool (See: https://streamflow-prediction-tool.readthedocs.io)
    2. Run from RAPID Qout file
    3. Don't run using RAPID to GSSHA

    There are two options for WRF to GSSHA:

    1. Run from WRF to GSSHA
    2. Don't run using WRF to GSSHA


    Parameters:
        gssha_executable(str): Path to GSSHA executable.
        gssha_directory(str): Path to directory for GSSHA project.
        project_filename(str): Name of GSSHA project file.
        gssha_simulation_start(Optional[datetime]): Datetime object with date of start of GSSHA simulation.
        gssha_simulation_end(Optional[datetime]): Datetime object with date of end of GSSHA simulation.
        gssha_simulation_duration(Optional[timedelta]): Datetime timedelta object with duration of GSSHA simulation.
        load_simulation_datetime(Optional[bool]): If True, this will load in datetime information from the project file. Default is False.
        spt_watershed_name(Optional[str]): Streamflow Prediction Tool watershed name.
        spt_subbasin_name(Optional[str]): Streamflow Prediction Tool subbasin name.
        spt_forecast_date_string(Optional[str]): Streamflow Prediction Tool forecast date string.
        ckan_engine_url(Optional[str]): CKAN engine API url.
        ckan_api_key(Optional[str]): CKAN api key.
        ckan_owner_organization(Optional[str]): CKAN owner organization.
        path_to_rapid_qout(Optional[str]): Path to the RAPID Qout file. Use this if you do NOT want to download the forecast and you want to use RAPID streamflows.
        connection_list_file(Optional[str]): CSV file with list connecting GSSHA rivers to RAPID river network. See: http://rapidpy.readthedocs.io/en/latest/rapid_to_gssha.html
        lsm_folder(Optional[str]): Path to folder with land surface model data. See: *lsm_input_folder_path* variable at :func:`~gsshapy.grid.GRIDtoGSSHA`.
        lsm_data_var_map_array(Optional[str]): Array with connections for WRF output and GSSHA input. See: :func:`~gsshapy.grid.GRIDtoGSSHA.`
        lsm_precip_data_var(Optional[list or str]): String of name for precipitation variable name or list of precip variable names.  See: :func:`~gsshapy.grid.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
        lsm_precip_type(Optional[str]): Type of precipitation. See: :func:`~gsshapy.grid.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
        lsm_lat_var(Optional[str]): Name of the latitude variable in the WRF netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
        lsm_lon_var(Optional[str]): Name of the longitude variable in the WRF netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
        lsm_time_var(Optional[str]): Name of the time variable in the WRF netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
        lsm_lat_dim(Optional[str]): Name of the latitude dimension in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
        lsm_lon_dim(Optional[str]): Name of the longitude dimension in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
        lsm_time_dim(Optional[str]): Name of the time dimension in the LSM netCDF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
        lsm_search_card(Optional[str]): Glob search pattern for WRF files. See: :func:`~gsshapy.grid.GRIDtoGSSHA`.
        precip_interpolation_type(Optional[str]): Type of interpolation for WRF precipitation. Can be "INV_DISTANCE" or "THIESSEN". Default is "THIESSEN".
        event_min_q(Optional[double]): Threshold discharge for continuing runoff events in m3/s. Default is 60.0.
        et_calc_mode(Optional[str]): Type of evapo-transpitation calculation for GSSHA. Can be "PENMAN" or "DEARDORFF". Default is "PENMAN".
        soil_moisture_depth(Optional[double]): Depth of the active soil moisture layer from which ET occurs (m). Default is 0.0.
        output_netcdf(Optional[bool]): If you want the HMET data output as a NetCDF4 file for input to GSSHA. Default is False.
        write_hotstart(Optional[bool]): If you want to automatically generate all hotstart files, set to True. Default is False.
        read_hotstart(Optional[bool]): If you want to automatically search for and read in hotstart files, set to True. Default is False.
        hotstart_minimal_mode(Optional[bool]): If you want to turn off all outputs to only generate the hotstart file, set to True. Default is False.

    Example running full framework with RAPID and LSM locally stored:

    .. code:: python

        from gsshapy.modeling import GSSHAWRFFramework

        gssha_executable = 'C:/Program Files/WMS 10.1 64-bit/gssha/gssha.exe'
        gssha_directory = "C:/Users/{username}/Documents/GSSHA"
        project_filename = "gssha_project.prj"

        #LSM TO GSSHA
        lsm_folder = '"C:/Users/{username}/Documents/GSSHA/wrf-sample-data-v1.0'

        #RAPID TO GSSHA
        path_to_rapid_qout = "C:/Users/{username}/Documents/GSSHA/Qout.nc"
        connection_list_file = "C:/Users/{username}/Documents/GSSHA/rapid_to_gssha_connect.csv"

        #INITIALIZE CLASS AND RUN
        gr = GSSHAWRFFramework(gssha_executable,
                               gssha_directory,
                               project_filename,
                               lsm_folder=lsm_folder,
                               path_to_rapid_qout=path_to_rapid_qout,
                               connection_list_file=connection_list_file,
                               )

        gr.run_forecast()

    Example connecting SPT to GSSHA:

    .. code:: python

        from gsshapy.modeling import GSSHAWRFFramework

        gssha_executable = 'C:/Program Files/WMS 10.1 64-bit/gssha/gssha.exe'
        gssha_directory = "C:/Users/{username}/Documents/GSSHA"
        project_filename = "gssha_project.prj"

        #LSM TO GSSHA
        lsm_folder = '"C:/Users/{username}/Documents/GSSHA/wrf-sample-data-v1.0'

        #RAPID TO GSSHA
        connection_list_file = "C:/Users/{username}/Documents/GSSHA/rapid_to_gssha_connect.csv"

        #SPT TO GSSHA
        ckan_engine_url='http://ckan/api/3/action'
        ckan_api_key='your-api-key'
        ckan_owner_organization='your_organization'
        spt_watershed_name='watershed_name'
        spt_subbasin_name='subbasin_name'
        spt_forecast_date_string='20160721.1200'

        #INITIALIZE CLASS AND RUN
        gr = GSSHAWRFFramework(gssha_executable,
                               gssha_directory,
                               project_filename,
                               lsm_folder=lsm_folder,
                               connection_list_file=connection_list_file,
                               ckan_engine_url=ckan_engine_url,
                               ckan_api_key=ckan_api_key,
                               ckan_owner_organization=ckan_owner_organization,
                               spt_watershed_name=spt_watershed_name,
                               spt_subbasin_name=spt_subbasin_name,
                               spt_forecast_date_string=spt_forecast_date_string,
                               )

        gr.run_forecast()

    Example with Hotstart:

    .. code:: python

        from datetime import datetime, timedelta
        from gsshapy.modeling import GSSHAWRFFramework

        gssha_executable = 'C:/Program Files/WMS 10.1 64-bit/gssha/gssha.exe'
        gssha_directory = "C:/Users/{username}/Documents/GSSHA"
        project_filename = "gssha_project.prj"
        full_gssha_simulation_duration = timedelta(days=5, seconds=0)
        gssha_hotstart_offset_duration = timedelta(days=1, seconds=0)

        #LSM
        lsm_folder = '"C:/Users/{username}/Documents/GSSHA/wrf-sample-data-v1.0'

        #RAPID
        path_to_rapid_qout = "C:/Users/{username}/Documents/GSSHA/Qout.nc"
        connection_list_file = "C:/Users/{username}/Documents/GSSHA/rapid_to_gssha_connect.csv"

        #--------------------------------------------------------------------------
        # MAIN RUN
        #--------------------------------------------------------------------------
        mr = GSSHAWRFFramework(gssha_executable,
                               gssha_directory,
                               project_filename,
                               lsm_folder=lsm_folder,
                               path_to_rapid_qout=path_to_rapid_qout,
                               connection_list_file=connection_list_file,
                               gssha_simulation_duration=full_gssha_simulation_duration,
                               read_hotstart=True,
                               )

        mr.run_forecast()
        #--------------------------------------------------------------------------
        # GENERATE HOTSTART FOR NEXT RUN
        #--------------------------------------------------------------------------
        hr = GSSHAWRFFramework(gssha_executable,
                               gssha_directory,
                               project_filename,
                               lsm_folder=lsm_folder,
                               path_to_rapid_qout=path_to_rapid_qout,
                               connection_list_file=connection_list_file,
                               gssha_simulation_duration=gssha_hotstart_offset_duration,
                               write_hotstart=True,
                               read_hotstart=True,
                               hotstart_minimal_mode=True,
                               )
        hr.run_forecast()
    """

    def __init__(self,
                 gssha_executable,
                 gssha_directory,
                 project_filename,
                 gssha_simulation_start=None,
                 gssha_simulation_end=None,
                 gssha_simulation_duration=None,
                 load_simulation_datetime=False,
                 spt_watershed_name=None,
                 spt_subbasin_name=None,
                 spt_forecast_date_string=None,
                 ckan_engine_url=None,
                 ckan_api_key=None,
                 ckan_owner_organization=None,
                 path_to_rapid_qout=None,
                 connection_list_file=None,
                 lsm_folder=None,
                 lsm_data_var_map_array=None,
                 lsm_precip_data_var= ['RAINC', 'RAINNC'],
                 lsm_precip_type='ACCUM',
                 lsm_lat_var='XLAT',
                 lsm_lon_var='XLONG',
                 lsm_time_var='Times',
                 lsm_lat_dim='south_north',
                 lsm_lon_dim='west_east',
                 lsm_time_dim='Time',
                 lsm_search_card="*.nc",
                 precip_interpolation_type=None,
                 event_min_q=None,
                 et_calc_mode=None,
                 soil_moisture_depth=None,
                 output_netcdf=False,
                 write_hotstart=False,
                 read_hotstart=False,
                 hotstart_minimal_mode=False,
                 ):
        """
        Initializer
        """
        if lsm_data_var_map_array is None:
            lsm_data_var_map_array = [
                                      ['precipitation_acc', ['RAINC', 'RAINNC']],
                                      ['pressure', 'PSFC'],
                                      ['relative_humidity', ['Q2', 'PSFC', 'T2']],
                                      ['wind_speed', ['U10', 'V10']],
                                      ['direct_radiation', ['SWDOWN', 'DIFFUSE_FRAC']],
                                      ['diffusive_radiation', ['SWDOWN', 'DIFFUSE_FRAC']],
                                      ['temperature', 'T2'],
                                      ['cloud_cover' , 'CLDFRA'],
                                     ]

        super(GSSHAWRFFramework, self).__init__(gssha_executable, gssha_directory, project_filename,
                                                gssha_simulation_start, gssha_simulation_end,
                                                gssha_simulation_duration, load_simulation_datetime,
                                                spt_watershed_name, spt_subbasin_name,
                                                spt_forecast_date_string, ckan_engine_url,
                                                ckan_api_key, ckan_owner_organization, path_to_rapid_qout,
                                                connection_list_file, lsm_folder, lsm_data_var_map_array,
                                                lsm_precip_data_var, lsm_precip_type, lsm_lat_var, lsm_lon_var,
                                                lsm_time_var, lsm_lat_dim, lsm_lon_dim, lsm_time_dim,
                                                lsm_search_card, precip_interpolation_type, event_min_q,
                                                et_calc_mode, soil_moisture_depth, output_netcdf,
                                                write_hotstart, read_hotstart, hotstart_minimal_mode)
