# -*- coding: utf-8 -*-
##
##  gssha_framework.py
##  GSSHApy
##
##  Created by Alan D Snow, 2016.
##  BSD 3-Clause

from datetime import datetime
from pyproj import Proj, transform
import os
from RAPIDpy import RAPIDDataset
from subprocess import Popen, PIPE

from gridtogssha import LSMtoGSSHA
from gsshapy.lib import db_tools as dbt
from gsshapy.orm import ProjectCard, ProjectFile

class GSSHAFramework(object):
    def __init__(self, gssha_executable, gssha_directory, project_filename):
        """
        Initializer
        """
        self.gssha_executable = gssha_executable
        self.gssha_directory = gssha_directory
        self.project_filename = project_filename
        self.project_name = os.path.splitext(project_filename)[0]
        
        # Create Test DB
        sqlalchemy_url, sql_engine = dbt.init_sqlite_memory()
        
        # Create DB Sessions
        self.db_session = dbt.create_session(sqlalchemy_url, sql_engine)
    
        # Instantiate GSSHAPY object for reading to database
        self.project_manager = ProjectFile()
        
        # Call read method
        self.project_manager.read(directory=self.gssha_directory,
                                  filename=self.project_filename,
                                  session=self.db_session)
        
    def _update_card(self, card_name, new_value, add_quotes=False):
        """
        Adds/updates card for gssha project file
        """
        card_name = card_name.upper()
        gssha_card = self.project_manager.getCard(card_name)
        
        if add_quotes:
            new_value = "\"{0}\"".format(new_value)
            
        if gssha_card is None:
            #add new card
            new_card = ProjectCard(name=card_name, value=new_value)
            self.project_manager.projectCards.append(new_card)
        else:
            gssha_card.value = new_value
    
    def _delete_card(self, card_name):
        """
        Removes card from gssha project file
        """
        card_name = card_name.upper()
        gssha_card = self.project_manager.getCard(card_name)
        if gssha_card is not None:
            self.db_session.delete(gssha_card)
            self.db_session.commit()

    def run(self, path_to_rapid_qout, 
                  connection_list,
                  lsm_folder,
                  lsm_data_var_map_array,
                  lsm_precip_data_var,
                  lsm_precip_type,
                  lsm_lat_var,
                  lsm_lon_var,
                  lsm_file_date_naming_convention,
                  lsm_time_var='time',                
                  lsm_search_card="*.nc",
                  precip_interpolation_type="THIESSEN",
                  output_netcdf=False
                  ):
        
        """
        Updates card & runs for RAPID to GSSHA & LSM to GSSHA
        
        Args:
            path_to_rapid_qout(str): Path to the RAPID Qout file.
            connection_list(list): List connecting GSSHA rivers to RAPID river network.
            lsm_folder(str): Path to folder with land surface model data. See: *lsm_input_folder_path* variable at :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA`.
            lsm_data_var_map_array(str): Array with connections for LSM output and GSSHA input. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.`
            lsm_precip_data_var(list or str): String of name for precipitation variable name or list of precip variable names.  See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
            lsm_precip_type(str): Type of precipitation. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA.lsm_precip_to_gssha_precip_gage`.
            lsm_lat_var(str): Name of the latitude variable in the LSM netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
            lsm_lon_var(str): Name of the longitude variable in the LSM netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
            lsm_file_date_naming_convention(str): Array with connections for LSM output and GSSHA input. See: :func:`~gridtogssha.LSMtoGSSHA`.
            lsm_time_var(str): Name of the time variable in the LSM netCDF files. See: :func:`~gridtogssha.LSMtoGSSHA`.
            lsm_search_card(str): Glob search pattern for LSM files. See: :func:`~gridtogssha.grid_to_gssha.GRIDtoGSSHA`.
            precip_interpolation_type(str): Type of interpolation for LSM precipitation. Can be "INV_DISTANCE" or "THIESSEN". Default is "THIESSEN".
            output_netcdf(bool): If you want the HMET data output as a NetCDF4 file for input to GSSHA. Default is False.
            
        Example::
            
                gssha_executable = 'C:/Program Files/WMS 10.1 64-bit/gssha/gssha.exe'
                gssha_directory = "C:/Users/{username}/Documents/GSSHA"
                project_filename = "gssha_project.prj"
                
                #RAPID INPUTS
                path_to_rapid_qout = 'C:/Users/{username}/Documents/GSSHA/Qout_rapid_watershed.nc'
                #list to connect the RAPID rivers to GSSHA rivers
                connection_list = [
                                   {
                                     'link_id': 599,
                                     'node_id': 1,
                                     'baseflow': 0.0,
                                     'rapid_rivid': 80968,
                                   },
                                 ]
                
                #WRF INPUTS
                lsm_folder = '"C:/Users/{username}/Documents/GSSHA/wrf-sample-data-v1.0'
                lsm_lat_var = 'XLAT'
                lsm_lon_var = 'XLONG'
                search_card = '*.nc'
                precip_data_var = ['RAINC', 'RAINNC']
                precip_type = 'ACCUM'
                lsm_file_date_naming_convention='gssha_d02_%Y_%m_%d_%H_%M_%S.nc'
                
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
                                    project_filename)
                
                gr.run(path_to_rapid_qout, 
                       connection_list,
                       lsm_folder,
                       data_var_map_array,
                       precip_data_var,
                       precip_type,
                       lsm_lat_var,
                       lsm_lon_var,
                       lsm_file_date_naming_convention,
                       )
        """
        self._update_card("PROJECT_PATH", self.gssha_directory)
        
        #----------------------------------------------------------------------
        #RAPID to GSSHA
        #----------------------------------------------------------------------
        ihg_filename = os.path.join('{0}.ihg'.format(self.project_name))
        
        #write out IHG file
        start_datetime = None
        end_datetime = None
        with RAPIDDataset(path_to_rapid_qout) as qout_nc:
            time_array = qout_nc.get_time_array(return_datetime=True)
            start_datetime = time_array[0]
            end_datetime = time_array[-1]
            qout_nc.write_flows_to_gssha_time_series_ihg(ihg_filename,
                                                         connection_list,
                                                         mode="max"
                                                         )
    
        # update cards
        self._update_card("START_DATE", start_datetime.strftime("%Y %m %d"))
        self._update_card("START_TIME", start_datetime.strftime("%H %M"))
        self._update_card("END_TIME", end_datetime.strftime("%Y %m %d %H %M"))
        self._update_card("CHAN_POINT_INPUT", ihg_filename, True)


        #----------------------------------------------------------------------
        #LSM to GSSHA
        #----------------------------------------------------------------------
        l2g = LSMtoGSSHA(gssha_project_folder=self.gssha_directory,
                         gssha_grid_file_name='{0}.ele'.format(self.project_name),
                         lsm_input_folder_path=lsm_folder,
                         lsm_search_card=search_card, 
                         lsm_lat_var=lsm_lat_var,
                         lsm_lon_var=lsm_lon_var,
                         lsm_time_var='time',
                         lsm_file_date_naming_convention=lsm_file_date_naming_convention,
                         )
        
        out_gage_file = os.path.join('{0}.gag'.format(self.project_name))
        l2g.lsm_precip_to_gssha_precip_gage(out_gage_file,
                                            lsm_data_var=lsm_precip_data_var,
                                            precip_type=lsm_precip_type)
        

        if output_netcdf:
            netcdf_file_path = os.path.join('{0}_hmet.nc'.format(self.project_name))
            l2g.lsm_data_to_subset_netcdf(netcdf_file_path, lsm_data_var_map_array)
            self._update_card("HMET_NETCDF", netcdf_file_path, True)
            self._delete_card("HMET_ASCII")
        else:
            l2g.lsm_data_to_arc_ascii(lsm_data_var_map_array)
            self._update_card("HMET_ASCII", os.path.join('hmet_ascii_data', 'hmet_file_list.txt'), True)
            self._delete_card("HMET_NETCDF")
    
        # update cards
        self._update_card('LONG_TERM', '')
        self._update_card('PRECIP_FILE', out_gage_file, True)
        
        if precip_interpolation_type.upper() == "INV_DISTANCE":
            self._update_card('RAIN_INV_DISTANCE ', '')
            self._delete_card("RAIN_THIESSEN")
        else:
            self._update_card('RAIN_THIESSEN ', '')
            self._delete_card("RAIN_INV_DISTANCE")
        
        #assume UTC time zone
        self._update_card('GMT', str(0))
        #update centroid
        center_lon, center_lat = transform(l2g.gssha_proj4,
                                           Proj(init='epsg:4326'),
                                           [(l2g.east_bound+l2g.west_bound)/2.0],
                                           [(l2g.north_bound+l2g.south_bound)/2.0], 
                                           )
        
        self._update_card('LATITUDE', str(center_lat[0]))
        self._update_card('LONGITUDE', str(center_lon[0]))

        #WRITE OUT UPDATED GSSHA PROJECT FILE
        self.project_manager.write(session=self.db_session, 
                                   directory=self.gssha_directory, 
                                   name=self.project_name)
        
        #RUN SIMULATION
        print("RUNNING GSSHA SIMULATION ...")
        run_gssha_command = [self.gssha_executable, 
                             os.path.join(self.gssha_directory, self.project_filename)]

        process = Popen(run_gssha_command, 
                        stdout=PIPE, stderr=PIPE, shell=False)
        out, err = process.communicate()
        if err:
            raise Exception(err)
        else:
            for line in out.split(b'\n'):
                print(line)
        
        
        
if __name__ == "__main__":
    gssha_executable = 'C:/Program Files/WMS 10.1 64-bit/gssha/gssha.exe'
    gssha_directory = "C:/Users/RDCHLADS/Documents/GSSHA/AF_GSSHA/NK_Hawaii/GSSHA"
    project_filename = "nk_arb2.prj"
    
    #RAPID
    path_to_rapid_qout = 'C:/Users/RDCHLADS/Documents/GSSHA/AF_GSSHA/Qout_korean_peninsula_48k_52.nc'
    #list to connect the RAPID rivers to GSSHA rivers
    connection_list = [
                       {
                         'link_id': 599,
                         'node_id': 1,
                         'baseflow': 0.0,
                         'rapid_rivid': 80968,
                       },
                     ]
    
    #LSM
    lsm_folder = 'F:/GSSHA/wrf-sample-data-v1.0'
    lsm_lat_var = 'XLAT'
    lsm_lon_var = 'XLONG'
    search_card = '*.nc'
    precip_data_var = ['RAINC', 'RAINNC']
    precip_type = 'ACCUM'
    lsm_file_date_naming_convention='gssha_d02_%Y_%m_%d_%H_%M_%S.nc'
    
    ##CONVERT FROM RAW WRF DATA
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
    
    gr = GSSHAFramework(gssha_executable,
                        gssha_directory, 
                        project_filename)
    
    gr.run(path_to_rapid_qout, 
           connection_list,
           lsm_folder,
           data_var_map_array,
           precip_data_var,
           precip_type,
           lsm_lat_var,
           lsm_lon_var,
           lsm_file_date_naming_convention,
           )