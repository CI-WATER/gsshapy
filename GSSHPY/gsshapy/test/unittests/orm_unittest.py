'''
********************************************************************************
* Name: ORM Tests
* Author: Nathan Swain
* Created On: May 16, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

import unittest, itertools

from gsshapy.orm.file_object_imports import *
from gsshapy.orm import ProjectFile
from gsshapy.lib import db_tools as dbt

class TestReadMethods (unittest.TestCase):
    def setUp(self):
        # Create 
        sqlalchemy_url = dbt.init_sqlite_db('db/standard.db')
        
        # Create DB Sessions
        self.readSession = dbt.create_session(sqlalchemy_url)
        self.querySession = dbt.create_session(sqlalchemy_url)
        
        # Define directory of test files to read
        self.directory = 'standard/'
        
    
    def test_project_read(self):
        '''
        Test ProjectFile read method
        '''
        # Instantiate GSSHAPY object for reading to database
        projectFileR = ProjectFile(path='standard/standard.prj',
                                   session=self.readSession)
        
        # Call read method
        projectFileR.read()
        
        # Query from database
        projectFileQ = self.querySession.query(ProjectFile).one()
        
        # Tests
        self.assertEqual(projectFileR.name, projectFileQ.name)
        self.assertEqual(projectFileR.mapType, projectFileQ.mapType)
        
        # Retrieve Cards
        cardsR = projectFileR.projectCards
        cardsQ = projectFileQ.projectCards
        
        for cardR, cardQ in itertools.izip(cardsR, cardsQ):
            # Compare cards and values
            self.assertEqual(cardR.name, cardQ.name)
            self.assertEqual(cardR.value, cardQ.value)
            
    def test_channel_input_read(self):
        '''
        Test ChannelInputFile read method
        '''
        # Read and Query
        cifR, cifQ = self._read_n_query(fileIO=ChannelInputFile,
                                        directory=self.directory,
                                        filename='standard.cif')
        
        # Tests
        self.assertEqual(cifR, cifQ)
        
        # Check Links
        linksR = cifR.streamLinks
        linksQ = cifQ.streamLinks
        
        for linkR, linkQ in itertools.izip(linksR, linksQ):
            self.assertEqual(linkR, linkQ)
            
            # Check Nodes
            nodesR = linkR.nodes
            nodesQ = linkQ.nodes
            
            self._list_compare(nodesR, nodesQ)
            
            # Check Upstream Links
            upLinksR = linkR.upstreamLinks
            upLinksQ = linkQ.upstreamLinks
            
            self._list_compare(upLinksR, upLinksQ)
            
            # Check Weirs
            weirsR = linkR.weirs
            weirsQ = linkQ.weirs
            
            self._list_compare(weirsR, weirsQ)
            
            # Check Culverts
            culvertsR = linkR.culverts
            culvertsQ = linkQ.culverts
            
            self._list_compare(culvertsR, culvertsQ)
            
            # Check Reservoir
            resR = linkR.reservoir
            resQ = linkQ.reservoir
            
            self.assertEqual(resR, resQ)
            
            # Check Reservoir Points
            if resR != None and resQ != None:
                resPointsR = resR.reservoirPoints
                resPointsQ = resQ.reservoirPoints
                self._list_compare(resPointsR, resPointsQ)
            
            # Check Trapezoidal CS
            trapR = linkR.trapezoidalCS
            trapQ = linkQ.trapezoidalCS
            
            self.assertEqual(trapR, trapQ)
            
            # Check Breakpoint CS
            breakR = linkR.breakpointCS
            breakQ = linkQ.breakpointCS
            
            self.assertEqual(breakR, breakQ)
                
            # Check Break Points
            if breakR != None and breakQ != None:
                bpR = breakR.breakpoints
                bpQ = breakQ.breakpoints
                
                self._list_compare(bpR, bpQ)

    def test_map_table_read(self):
        '''
        Test MapTableFile read method
        '''
        # Read and Query
        cmtR, cmtQ = self._read_n_query(fileIO=MapTableFile,
                                        directory=self.directory,
                                        filename='standard.cmt')
        
        # Tests
        
        # Check Index Maps
        idxMapsR = cmtR.indexMaps
        idxMapsQ = cmtQ.indexMaps
        
        self._list_compare(idxMapsR, idxMapsQ)
        
        # Check Map Tables
        mapTablesR = cmtR.mapTables
        mapTablesQ = cmtQ.mapTables
        
        for mapTableR, mapTableQ in itertools.izip(mapTablesR, mapTablesQ):
            self.assertEqual(mapTableR, mapTableQ)
            
            
            # Check sediments
            sedsR = mapTableR.sediments
            sedsQ = mapTableQ.sediments
            
            if sedsR != None and sedsQ != None:
                self._list_compare(sedsR, sedsQ)
                
            # Check Values
            valsR = mapTableR.values
            valsQ = mapTableQ.values
            
            for valR, valQ in itertools.izip(valsR, valsQ):
                self.assertEqual(valR, valQ)
                
                # Check Contaminant
                contamR = valR.contaminant
                contamQ = valR.contaminant
                
                
                if contamR != None and contamQ != None:
                    self.assertEqual(contamR, contamQ)
                    
                # Check Index
                indexR = valR.index
                indexQ = valQ.index
                
                self.assertEqual(indexR, indexQ)
            
        
        
        
        
    def _read_n_query(self, fileIO, directory, filename):
        '''
        Read to database and Query from database
        '''
        # Instantiate GSSHAPY object for reading to database
        instanceR = fileIO(directory=directory,
                           filename=filename,
                           session=self.readSession)
        
        # Call read method
        instanceR.read()
        
        # Query from database
        instanceQ = self.querySession.query(fileIO).one()
        
        return instanceR, instanceQ
    
    def _list_compare(self, listone, listtwo):
        for one, two in itertools.izip(listone, listtwo):
            self.assertEqual(one, two)
        
        
        
    def tearDown(self):
        dbt.del_sqlite_db('db/standard.db')
        
    

if __name__ == '__main__':
    unittest.main()
