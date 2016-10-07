# -*- coding: utf-8 -*-
##
##  gssha_framework.py
##  GSSHApy
##
##  Created by Alan D Snow, 2016.
##  BSD 3-Clause

from datetime import datetime
from gridtogssha import LSMtoGSSHA
from gsshapy.lib import db_tools as dbt
from gsshapy.orm import ProjectCard, ProjectFile
import os
from RAPIDpy import RAPIDDataset
from subprocess import Popen, PIPE

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
                  output_netcdf=False
                  ):
        
        """
        Updates card & runs for RAPID to GSSHA & LSM to GSSHA
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
        self._update_card("CHAN_POINT_INPUT", ihg_filename)


        #----------------------------------------------------------------------
        #LSM to GSSHA
        #----------------------------------------------------------------------
        
        ###### ----------
        ### MAIN FUNNCTIONS
        ###### ----------
    
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
            self._update_card("HMET_NETCDF", netcdf_file_path)
            self._delete_card("HMET_ASCII")
        else:
            l2g.lsm_data_to_arc_ascii(lsm_data_var_map_array)
            self._update_card("HMET_ASCII", os.path.join('hmet_ascii_data', 'hmet_file_list.txt'))
            self._delete_card("HMET_NETCDF")
    
        # update cards
        self._update_card('LONG_TERM', '')
        self._update_card('PRECIP_FILE', out_gage_file)
        #TODO: UPDATE CARDS
        #self._update_card('GMT', '')
        #self._update_card('LATITUDE', '')
        #self._update_card('LONGITUDE', '')

        #WRITE OUT NEW FILES
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