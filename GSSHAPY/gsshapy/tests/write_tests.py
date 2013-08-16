'''
********************************************************************************
* Name: Write Tests
* Author: Nathan Swain
* Created On: May 16, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

import unittest, itertools, os, uuid

from gsshapy.orm.file_io import *
from gsshapy.orm import ProjectFile
from gsshapy.lib import db_tools as dbt

class TestWriteMethods(unittest.TestCase):
    def setUp(self):
        # Find db directory path
        here = os.path.abspath(os.path.dirname(__file__))
        
        dbName = '%s.db' % uuid.uuid4()
        self.db_path = os.path.join(here, 'db', 'standard.db')
        
        # Create Test DB 
        sqlalchemy_url = dbt.init_sqlite_db(self.db_path)
        
        # Define workspace
        self.readDirectory = os.path.join(here, 'standard')
        self.writeDirectory = os.path.join(here, 'out')
        self.original = 'standard'
        self.name = 'standard'
        
        # Create DB Sessions
        readSession = dbt.create_session(sqlalchemy_url)
        self.writeSession = dbt.create_session(sqlalchemy_url)
        
        # Instantiate GSSHAPY ProjectFile object
        prjR = ProjectFile(directory=self.readDirectory,
                           filename='standard.prj',
                           session=readSession)
        
        # Invoke read project method
        prjR.readProject()
        
    
    def test_project_file_write(self):
        '''
        Test ProjectFile write method
        '''
        # Query and invoke write method
        self._query_n_write(ProjectFile)
        
        # Test
        self._compare_files(self.original, self.name, 'prj')

    def test_channel_input_write(self):
        '''
        Test ChannelInputFile write method
        '''
        # Query and invoke write method
        self._query_n_write(ChannelInputFile)
        
        # Test
        self._compare_files(self.original, self.name, 'cif')
        

    def test_map_table_file_write(self):
        '''
        Test MapTableFile write method
        '''
        # Query and invoke write method
        self._query_n_write(MapTableFile)
        
        # Test
        self._compare_files(self.original, self.name, 'cmt')
        
    def test_precip_file_write(self):
        '''
        Test PrecipFile write method
        '''
        # Query and invoke write method
        self._query_n_write(PrecipFile)
        
        # Test
        self._compare_files(self.original, self.name, 'gag')
        
        
    def test_grid_pipe_file_write(self):
        '''
        Test GridPipeFile write method
        '''
        # Query and invoke write method
        self._query_n_write(GridPipeFile)
        
        # Test
        self._compare_files(self.original, self.name, 'gpi')
        
        
    def test_grid_stream_file_write(self):
        '''
        Test GridStreamFile write method
        '''
        # Query and invoke write method
        self._query_n_write(GridStreamFile)
        
        # Test
        self._compare_files(self.original, self.name, 'gst')
        
        
    def test_hmet_file_write(self):
        '''
        Test HmetFile write method
        '''
        # Query and invoke write method
        self._query_n_write_filename(HmetFile, 'hmet_wes.hmt')
        
        # Test
        self._compare_files('hmet_wes', 'hmet_wes', 'hmt')
        
        
    def test_output_location_file_write(self):
        '''
        Test OutputLocationFile write method
        '''
        # Query and invoke write method
        self._query_n_write_multiple(OutputLocationFile, 'ihl')
        
        # Test
        self._compare_files(self.original, self.name, 'ihl')
        
        
        
    def test_link_node_dataset_file_write(self):
        '''
        Test LinkNodeDatasetFile write method
        '''
        # Query and invoke write method
        self._query_n_write_multiple(LinkNodeDatasetFile, 'cdp')
        
        # Test
        self._compare_files(self.original, self.name, 'cdp')
        
        
    def test_raster_map_file_write(self):
        '''
        Test RasterMapFile write method
        '''
        # Query and invoke write method
        self._query_n_write_multiple(RasterMapFile, 'msk')
        
        # Test
        self._compare_files(self.original, self.name, 'msk')
        
        
        
    def test_projection_file_write(self):
        '''
        Test ProjectionFile write method
        '''
        # Query and invoke write method
        self._query_n_write(ProjectionFile)
        
        # Test
        self._compare_files('standard_prj', 'standard_prj', 'pro')
        
        
    def test_replace_param_file_write(self):
        '''
        Test ReplaceParamFile write method
        '''
        # Query and invoke write method
        self._query_n_write_filename(ReplaceParamFile, 'replace_param.txt')
        
        # Test
        self._compare_files('replace_param', 'replace_param', 'txt')
        
        
        
    def test_replace_val_file_write(self):
        '''
        Test ReplaceValFile write method
        '''
        # Query and invoke write method
        self._query_n_write_filename(ReplaceValFile, 'replace_val.txt')
        
        # Test
        self._compare_files('replace_val', 'replace_val', 'txt')
        
        
    def test_nwsrfs_file_write(self):
        '''
        Test NwsrfsFile write method
        '''
        # Query and invoke write method
        self._query_n_write_filename(NwsrfsFile, 'nwsrfs_elev.txt')
        
        # Test
        self._compare_files('nwsrfs_elev', 'nwsrfs_elev', 'txt')
        
        
    def test_ortho_gage_file_write(self):
        '''
        Test OrthographicGageFile write method
        '''
        # Query and invoke write method
        self._query_n_write_filename(OrthographicGageFile, 'ortho_gages.txt')
        
        # Test
        self._compare_files('ortho_gages', 'ortho_gages', 'txt')
        
        
    def test_storm_pipe_network_file_write(self):
        '''
        Test StormPipeNetworkFile write method
        '''
        # Query and invoke write method
        self._query_n_write(StormPipeNetworkFile)
        
        # Test
        self._compare_files(self.original, self.name, 'spn')
        
        
        
    def test_time_series_file_write(self):
        '''
        Test TimeSeriesFile write method
        '''
        # Query and invoke write method
        self._query_n_write_multiple(TimeSeriesFile, 'ohl')
        
        # Test
        self._compare_files(self.original, self.name, 'ohl')

    def test_index_map_write(self):
        '''
        Test IndexMap write method
        '''
        # Retrieve file from database
        idx = self.writeSession.query(IndexMap).\
                   filter(IndexMap.filename == 'Soil.idx').\
                   one()
        
        # Invoke write method
        idx.write(session=self.writeSession,
                  directory=self.writeDirectory,
                  name='soil_new_name')
        
        # Test
        self._compare_files('Soil', 'soil_new_name', 'idx')
        
        
    def test_project_file_write_all(self):
        '''
        Test ProjectFile write all method
        '''
        # Retrieve ProjectFile from database
        projectFile = self.writeSession.query(ProjectFile).one()
        
        # Invoke write all method
        projectFile.writeProject(session=self.writeSession,
                                 directory=self.writeDirectory,
                                 name='standard')
        
        # Compare all files
        self._compare_directories(self.readDirectory, self.writeDirectory)
        

    def test_project_file_write_input(self):
        '''
        Test ProjecFile write input method
        '''
        # Retrieve ProjectFile from database
        projectFile = self.writeSession.query(ProjectFile).one()
        
        # Invoke write input method
        projectFile.writeInput(session=self.writeSession,
                               directory=self.writeDirectory,
                               name='standard')
        
        # Compare all files
        self._compare_directories(self.readDirectory, self.writeDirectory)
        
    def test_project_file_write_output(self):
        '''
        Test ProjectFile write output method
        '''
        # Retrieve ProjectFile from database
        projectFile = self.writeSession.query(ProjectFile).one()
        
        # Invoke write output method
        projectFile.writeOutput(session=self.writeSession,
                                directory=self.writeDirectory,
                                name='standard')
        
        # Compare all files
        self._compare_directories(self.readDirectory, self.writeDirectory)
    
    def _query_n_write(self, fileIO):
        '''
        Query database and write file method
        '''
        # Retrieve file from database
        instance = self.writeSession.query(fileIO).one()
        
        # Invoke write method
        instance.write(session=self.writeSession,
                       directory=self.writeDirectory,
                       name=self.name)
    
    def _query_n_write_filename(self, fileIO, filename):
        '''
        Query database and write file method
        '''
        # Retrieve file from database
        instance = self.writeSession.query(fileIO).one()
        
        # Invoke write method
        instance.write(session=self.writeSession,
                       directory=self.writeDirectory,
                       name=filename)
        
    def _query_n_write_multiple(self, fileIO, ext):
        '''
        Query database and write file method
        '''
        # Retrieve file from database
        instance = self.writeSession.query(fileIO).\
                        filter(fileIO.fileExtension == ext).\
                        one()
        
        # Invoke write method
        instance.write(session=self.writeSession,
                       directory=self.writeDirectory,
                       name=self.name)
        
    def _compare_files(self, original, new, ext):
        '''
        Compare the contents of two files
        '''
        filenameO = '%s.%s' % (original, ext)
        filePathO = os.path.join(self.readDirectory, filenameO)
        filenameN = '%s.%s' % (new, ext)
        filePathN = os.path.join(self.writeDirectory, filenameN)
        
        with open(filePathO) as fileO:
            contentsO = fileO.read()
            linesO = contentsO.strip().split()
            
        with open(filePathN) as fileN:
            contentsN = fileN.read()
            linesN = contentsN.strip().split()
            
        self.assertEqual(linesO, linesN)
        
    def _compare_directories(self, dir1, dir2):
        '''
        Compare the contents of the files of two directories
        '''
        fileList2 = os.listdir(dir2)
        
        for afile in fileList2:
            name = afile.split('.')[0]
            ext = afile.split('.')[1]
            
            # Compare files with same name
            self._compare_files(name, name, ext)
            
    def _list_compare(self, listone, listtwo):
        for one, two in itertools.izip(listone, listtwo):
            self.assertEqual(one, two)
        
    def tearDown(self):
        # Remove temp database
        dbt.del_sqlite_db(self.db_path)
        
        # Clear out directory
        fileList = os.listdir(self.writeDirectory)
        
        for afile in fileList:
            path = os.path.join(self.writeDirectory, afile)
            os.remove(path)
            
suite = unittest.TestLoader().loadTestsFromTestCase(TestWriteMethods)
    

if __name__ == '__main__':
    unittest.main()
