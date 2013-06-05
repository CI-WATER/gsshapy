'''
********************************************************************************
* Name: Bootstrap Data for ORM Tests
* Author: Nathan Swain
* Created On: May 16, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

from gsshapy.orm import *
from datetime import date

def orm_test_data(DBSession):
    # Define Model Instance
    # Define the model instance
    
    mdl = ModelInstance("Park City Basic", "Park City, UT", date(2013,6,5))
    
    # Define a default scenario for this model
    scn1 = Scenario(name='DEFAULT', description='This is the default scenario for testing purposes.', created=date(2013,6,5), base=True)
    scn1.model = mdl
    
    # Load the project file
    projectFile = [('WATERSHED_MASK', '"parkcity.msk"','PATH'), 
                   ('LandSoil', '"parkcity.lsf"','PATH'),
                   ('PROJECTION_FILE', '"parkcity_prj.pro"','PATH'),
                   ('NON_ORTHO_CHANNELS', 'TRUE','BOOLEAN'),
                   ('FLINE', '"parkcity.map"','PATH'),
                   ('METRIC', 'TRUE','BOOLEAN'),
                   ('GRIDSIZE', '90.000000','FLOAT'),
                   ('ROWS', '72', 'INTEGER'),
                   ('COLS', '67', 'INTEGER'),
                   ('TOT_TIME', '1440', 'INTEGER'),
                   ('TIMESTEP', '10', 'INTEGER'),
                   ('OUTROW', '11', 'INTEGER'),
                   ('OUTCOL', '38', 'INTEGER'),
                   ('OUTSLOPE', '0.001000','FLOAT'),
                   ('MAP_FREQ', '30', 'INTEGER'),
                   ('HYD_FREQ', '30', 'INTEGER'),
                   ('MAP_TYPE', '1', 'INTEGER'),
                   ('ELEVATION', '"parkcity.ele"','PATH'),
                   ('DEPTH', '"parkcity.dep"','PATH'),
                   ('DIFFUSIVE_WAVE', 'TRUE','BOOLEAN'),
                   ('CHANNEL_INPUT', '"parkcity.cif"','PATH'),
                   ('STREAM_CELL', '"parkcity.gst"','PATH'),
                   ('OVERTYPE', 'ADE','STRING'),
                   ('INF_REDIST', '','BOOLEAN'),
                   ('INDEXGRID_GUID', '"luse.idx"','PATH'),
                   ('INDEXGRID_GUID', '"soil.idx"','PATH'),
                   ('INDEXGRID_GUID', '"combo.idx"','PATH'),
                   ('MAPPING_TABLE', '"parkcity.cmt"','PATH'),
                   ('ST_MAPPING_TABLE', '"parkcity.smt"','PATH'),
                   ('SUMMARY', '"parkcity.sum"','PATH'),
                   ('OUTLET_HYDRO', '"parkcity.otl"','PATH'),
                   ('QUIET', 'TRUE','BOOLEAN'),
                   ('PRECIP_FILE', '"parkcity.gag"','PATH'),
                   ('RAIN_INV_DISTANCE', 'TRUE','BOOLEAN'),
                   ('IN_HYD_LOCATION', '"parkcity.ihl"','PATH'),
                   ('OUT_HYD_LOCATION', '"parkcity.ohl"','PATH')]
    
    for p in projectFile:
        crd = ProjectCard(name=p[0], valueType=p[2])
        prj = ProjectOption(value=p[1])
        prj.card = crd
        prj.model = mdl
        prj.scenarios.append(scn1)
    
        
        
    # Load Index Maps
    """
    luse = IndexMap('LandUse', '"luse.idx"','')
    luse.model = mdl
    soil = IndexMap('Soil', '"soil.idx"','')
    soil.model = mdl
    combo = IndexMap('Combination', '"combo.idx"','')
    combo.model = mdl
    
    # Load Mapping Tables
    
    roughTbl = MapTable('ROUGHNESS', 7, -1, -1, -1) # Roughness
    roughTbl.model = mdl
    roughTbl.indexMap = luse
    
    roughIdxs = [(11, 'Land Use #11',''),
                 (16, 'Land Use #16',''),
                 (17, 'Land Use #17',''),
                 (32, 'Land Use #32',''),
                 (33, 'Land Use #33',''),
                 (41, 'Land Use #41',''),
                 (42, 'Land Use #42','')]
    
    roughValues = [(0, 'ROUGH', 0.011000),
                   (1, 'ROUGH', 0.011000),
                   (2, 'ROUGH', 0.011000),
                   (3, 'ROUGH', 0.050000),
                   (4, 'ROUGH', 0.040000),
                   (5, 'ROUGH', 0.100000),
                   (6, 'ROUGH', 0.150000)]
    
    # Load Indexes
    idx = []
    for i in roughIdxs:
        mtIDX = MTIndex(i[0], i[1], i[2])
        mtIDX.indexMap = luse
        idx.append(mtIDX)
        
    # Load Variables
    for v in roughValues:
        val = MTValue(v[1], v[2])
        val.mapTable = roughTbl
        val.index = idx[v[0]]
        
        
        
    
    infilTbl = MapTable('GREEN_AMPT_INFILTRATION', 19, -1, -1, -1) # Infiltration
    infilTbl.model = mdl
    infilTbl.indexMap = combo
    
    infilIdxs = [(1, 'Clay loam', 'Land ID #32'),
                 (2, 'Loam', 'Land ID #32'),
                 (3, 'Loam', 'Land ID #11'),
                 (4, 'Clay loam', 'Land ID #16'),
                 (5, 'Loam', 'Land ID #16'),
                 (6, 'Clay loam', 'Land ID #11'),
                 (7, 'Clay loam', 'Land ID #42'),
                 (8, 'Clay loam', 'Land ID #17'),
                 (9, 'Loam', 'Land ID #17'),
                 (10, 'Loam', 'Land ID #42'),
                 (11, 'Sandy clay loam', 'Land ID #16'),
                 (12, 'Sandy clay loam', 'Land ID #42'),
                 (13, 'Sandy clay loam', 'Land ID #17'),
                 (14, 'Sandy clay loam', 'Land ID #32'),
                 (15, 'Loam', 'Land ID #41'),
                 (16, 'Sandy clay loam', 'Land ID #41'),
                 (17, 'Sandy clay loam', 'Land ID #33'),
                 (18, 'Clay loam', 'Land ID #33'),
                 (19, 'Loam', 'Land ID #33')]
    
    infilValues = [(1, 'HYDR_COND', 'Clay loam', 'Land ID #32', 1.000000),
                   (2, 'HYDR_COND', 'Loam', 'Land ID #32', 1.000000),
                   (3, 'HYDR_COND', 'Loam', 'Land ID #11', 1.000000),
                   (4, 'HYDR_COND', 'Clay loam', 'Land ID #16', 1.000000),
                   (5, 'HYDR_COND', 'Loam', 'Land ID #16', 1.000000),
                   (6, 'HYDR_COND', 'Clay loam', 'Land ID #11', 1.000000),
                   (7, 'HYDR_COND', 'Clay loam', 'Land ID #42', 1.000000),
                   (8, 'HYDR_COND', 'Clay loam', 'Land ID #17', 1.000000),
                   (9, 'HYDR_COND', 'Loam', 'Land ID #17', 1.000000),
                   (10, 'HYDR_COND', 'Loam', 'Land ID #42', 1.000000),
                   (11, 'HYDR_COND', 'Sandy clay loam', 'Land ID #16', 1.000000),
                   (12, 'HYDR_COND', 'Sandy clay loam', 'Land ID #42', 1.000000),
                   (13, 'HYDR_COND', 'Sandy clay loam', 'Land ID #17', 1.000000),
                   (14, 'HYDR_COND', 'Sandy clay loam', 'Land ID #32', 1.000000),
                   (15, 'HYDR_COND', 'Loam', 'Land ID #41', 1.000000),
                   (16, 'HYDR_COND', 'Sandy clay loam', 'Land ID #41', 1.000000),
                   (17, 'HYDR_COND', 'Sandy clay loam', 'Land ID #33', 1.000000),
                   (18, 'HYDR_COND', 'Clay loam', 'Land ID #33', 1.000000),
                   (19, 'HYDR_COND', 'Loam', 'Land ID #33', 1.000000),
                   (1, 'CAPIL_HEAD', 'Clay loam', 'Land ID #32', 4.950000),
                   (2, 'CAPIL_HEAD', 'Loam', 'Land ID #32', 4.950000),
                   (3, 'CAPIL_HEAD', 'Loam', 'Land ID #11', 4.950000),
                   (4, 'CAPIL_HEAD', 'Clay loam', 'Land ID #16', 4.950000),
                   (5, 'CAPIL_HEAD', 'Loam', 'Land ID #16', 4.950000),
                   (6, 'CAPIL_HEAD', 'Clay loam', 'Land ID #11',4.950000),
                   (7, 'CAPIL_HEAD', 'Clay loam', 'Land ID #42', 4.950000),
                   (8, 'CAPIL_HEAD', 'Clay loam', 'Land ID #17', 4.950000),
                   (9, 'CAPIL_HEAD', 'Loam', 'Land ID #17', 4.950000),
                   (10, 'CAPIL_HEAD', 'Loam', 'Land ID #42', 4.950000),
                   (11, 'CAPIL_HEAD', 'Sandy clay loam', 'Land ID #16', 4.950000),
                   (12, 'CAPIL_HEAD', 'Sandy clay loam', 'Land ID #42', 4.950000),
                   (13, 'CAPIL_HEAD', 'Sandy clay loam', 'Land ID #17', 4.950000),
                   (14, 'CAPIL_HEAD', 'Sandy clay loam', 'Land ID #32', 21.850000),
                   (15, 'CAPIL_HEAD',  'Loam', 'Land ID #41', 4.950000),
                   (16, 'CAPIL_HEAD', 'Sandy clay loam', 'Land ID #41', 4.950000),
                   (17, 'CAPIL_HEAD', 'Sandy clay loam', 'Land ID #33', 4.950000),
                   (18, 'CAPIL_HEAD', 'Clay loam', 'Land ID #33', 4.950000),
                   (19, 'CAPIL_HEAD', 'Loam', 'Land ID #33', 4.950000),    
                   (1, 'POROSITY', 'Clay loam', 'Land ID #32', 0.437000),
                   (2, 'POROSITY', 'Loam', 'Land ID #32', 0.437000),
                   (3, 'POROSITY', 'Loam', 'Land ID #11', 0.437000),
                   (4, 'POROSITY', 'Clay loam', 'Land ID #16', 0.437000),
                   (5, 'POROSITY', 'Loam', 'Land ID #16', 0.437000),
                   (6, 'POROSITY', 'Clay loam', 'Land ID #11', 0.437000),
                   (7, 'POROSITY', 'Clay loam', 'Land ID #42', 0.437000),
                   (8, 'POROSITY', 'Clay loam', 'Land ID #17', 0.437000),
                   (9, 'POROSITY', 'Loam', 'Land ID #17', 0.4370000),
                   (10, 'POROSITY', 'Loam', 'Land ID #42', 0.437000),
                   (11, 'POROSITY', 'Sandy clay loam', 'Land ID #16', 0.437000),
                   (12, 'POROSITY', 'Sandy clay loam', 'Land ID #42', 0.437000),
                   (13, 'POROSITY', 'Sandy clay loam', 'Land ID #17', 0.437000),
                   (14, 'POROSITY', 'Sandy clay loam', 'Land ID #32', 0.398000),
                   (15, 'POROSITY', 'Loam', 'Land ID #41', 0.437000),
                   (16, 'POROSITY', 'Sandy clay loam', 'Land ID #41', 0.437000),
                   (17, 'POROSITY', 'Sandy clay loam', 'Land ID #33', 0.437000),
                   (18, 'POROSITY', 'Clay loam', 'Land ID #33', 0.437000),
                   (19, 'POROSITY', 'Loam', 'Land ID #33', 0.437000),    
                   (1, 'PORE_INDEX', 'Clay loam', 'Land ID #32', 0.694000),
                   (2, 'PORE_INDEX', 'Loam', 'Land ID #32', 0.694000),
                   (3, 'PORE_INDEX', 'Loam', 'Land ID #11', 0.694000),
                   (4, 'PORE_INDEX', 'Clay loam', 'Land ID #16', 0.694000),
                   (5, 'PORE_INDEX', 'Loam', 'Land ID #16', 0.694000),
                   (6, 'PORE_INDEX', 'Clay loam', 'Land ID #11', 0.694000),
                   (7, 'PORE_INDEX', 'Clay loam', 'Land ID #42', 0.694000),
                   (8, 'PORE_INDEX', 'Clay loam', 'Land ID #17', 0.694000),
                   (9, 'PORE_INDEX', 'Loam', 'Land ID #17', 0.694000),
                   (10, 'PORE_INDEX', 'Loam', 'Land ID #42', 0.694000),
                   (11, 'PORE_INDEX', 'Sandy clay loam', 'Land ID #16', 0.694000),
                   (12, 'PORE_INDEX', 'Sandy clay loam', 'Land ID #42', 0.694000),
                   (13, 'PORE_INDEX', 'Sandy clay loam', 'Land ID #17', 0.694000),
                   (14, 'PORE_INDEX', 'Sandy clay loam', 'Land ID #32', 0.319000),
                   (15, 'PORE_INDEX', 'Loam', 'Land ID #41', 0.694000),
                   (16, 'PORE_INDEX', 'Sandy clay loam', 'Land ID #41', 0.694000),
                   (17, 'PORE_INDEX', 'Sandy clay loam', 'Land ID #33', 0.694000),
                   (18, 'PORE_INDEX', 'Clay loam', 'Land ID #33', 0.694000),
                   (19, 'PORE_INDEX', 'Loam', 'Land ID #33', 0.694000),    
                   (1,'RESID_SAT', 'Clay loam', 'Land ID #32', 0.020000),
                   (2,'RESID_SAT', 'Loam', 'Land ID #32', 0.020000),
                   (3,'RESID_SAT', 'Loam', 'Land ID #11', 0.020000),
                   (4,'RESID_SAT', 'Clay loam', 'Land ID #16', 0.020000),
                   (5,'RESID_SAT', 'Loam', 'Land ID #16', 0.020000),
                   (6,'RESID_SAT', 'Clay loam', 'Land ID #11', 0.020000),
                   (7,'RESID_SAT', 'Clay loam', 'Land ID #42', 0.020000),
                   (8,'RESID_SAT', 'Clay loam', 'Land ID #17', 0.020000),
                   (9,'RESID_SAT', 'Loam', 'Land ID #17', 0.020000),
                   (10,'RESID_SAT', 'Loam', 'Land ID #42', 0.020000),
                   (11,'RESID_SAT', 'Sandy clay loam', 'Land ID #16', 0.020000),
                   (12,'RESID_SAT', 'Sandy clay loam', 'Land ID #42', 0.020000),
                   (13,'RESID_SAT', 'Sandy clay loam', 'Land ID #17', 0.020000),
                   (14,'RESID_SAT', 'Sandy clay loam', 'Land ID #32', 0.068000),
                   (15,'RESID_SAT', 'Loam', 'Land ID #41', 0.020000),
                   (16,'RESID_SAT', 'Sandy clay loam', 'Land ID #41', 0.020000),
                   (17,'RESID_SAT', 'Sandy clay loam', 'Land ID #33', 0.020000),
                   (18,'RESID_SAT', 'Clay loam', 'Land ID #33', 0.020000),
                   (19,'RESID_SAT', 'Loam', 'Land ID #33', 0.020000),    
                   (1, 'FIELD_CAPACITY', 'Clay loam', 'Land ID #32', 0.091000),
                   (2, 'FIELD_CAPACITY', 'Loam', 'Land ID #32', 0.091000),
                   (3, 'FIELD_CAPACITY', 'Loam', 'Land ID #11', 0.091000),
                   (4, 'FIELD_CAPACITY', 'Clay loam', 'Land ID #16', 0.091000),
                   (5, 'FIELD_CAPACITY', 'Loam', 'Land ID #16', 0.091000),
                   (6, 'FIELD_CAPACITY', 'Clay loam', 'Land ID #11', 0.091000),
                   (7, 'FIELD_CAPACITY', 'Clay loam', 'Land ID #42', 0.091000),
                   (8, 'FIELD_CAPACITY', 'Clay loam', 'Land ID #17', 0.091000),
                   (9, 'FIELD_CAPACITY', 'Loam', 'Land ID #17', 0.091000),
                   (10, 'FIELD_CAPACITY', 'Loam', 'Land ID #42', 0.091000),
                   (11, 'FIELD_CAPACITY', 'Sandy clay loam', 'Land ID #16', 0.091000),
                   (12, 'FIELD_CAPACITY', 'Sandy clay loam', 'Land ID #42', 0.091000),
                   (13, 'FIELD_CAPACITY', 'Sandy clay loam', 'Land ID #17', 0.091000),
                   (14, 'FIELD_CAPACITY', 'Sandy clay loam', 'Land ID #32',0.225000),
                   (15, 'FIELD_CAPACITY', 'Loam', 'Land ID #41', 0.091000),
                   (16, 'FIELD_CAPACITY', 'Sandy clay loam', 'Land ID #41', 0.091000),
                   (17, 'FIELD_CAPACITY', 'Sandy clay loam', 'Land ID #33', 0.091000),
                   (18, 'FIELD_CAPACITY', 'Clay loam', 'Land ID #33', 0.091000),
                   (19, 'FIELD_CAPACITY', 'Loam', 'Land ID #33', 0.091000),    
                   (1,'WILTING_PT', 'Clay loam', 'Land ID #32', 0.100000),
                   (2,'WILTING_PT', 'Loam', 'Land ID #32', 0.100000),
                   (3,'WILTING_PT', 'Loam', 'Land ID #11', 0.100000),
                   (4,'WILTING_PT', 'Clay loam', 'Land ID #16', 0.100000),
                   (5,'WILTING_PT', 'Loam', 'Land ID #16', 0.100000),
                   (6,'WILTING_PT', 'Clay loam', 'Land ID #11', 0.100000),
                   (7,'WILTING_PT', 'Clay loam', 'Land ID #42', 0.100000),
                   (8,'WILTING_PT', 'Clay loam', 'Land ID #17', 0.100000),
                   (9,'WILTING_PT', 'Loam', 'Land ID #17', 0.100000),
                   (10,'WILTING_PT', 'Loam', 'Land ID #42', 0.100000),
                   (11,'WILTING_PT', 'Sandy clay loam', 'Land ID #16', 0.100000),
                   (12,'WILTING_PT', 'Sandy clay loam', 'Land ID #42', 0.100000),
                   (13,'WILTING_PT', 'Sandy clay loam', 'Land ID #17', 0.100000),
                   (14,'WILTING_PT', 'Sandy clay loam', 'Land ID #32', 0.100000),
                   (15,'WILTING_PT', 'Loam', 'Land ID #41', 0.100000),
                   (16,'WILTING_PT', 'Sandy clay loam', 'Land ID #41', 0.100000),
                   (17,'WILTING_PT', 'Sandy clay loam', 'Land ID #33', 0.100000),
                   (18,'WILTING_PT', 'Clay loam', 'Land ID #33', 0.100000),
                   (19,'WILTING_PT', 'Loam', 'Land ID #33', 0.100000)]

    # Load Indexes
    idx = []
    for i in infilIdxs:
        mtIDX = MTIndex(i[0], i[1], i[2])
        mtIDX.indexMap = combo
        idx.append(mtIDX)
        
    # Load Variables
    for v in infilValues:
        val = MTValue(v[1], v[4])
        val.mapTable = infilTbl
        val.index = idx[v[0]-1]

    gaMoisTbl = MapTable('GREEN_AMPT_INITIAL_SOIL_MOISTURE', 3, -1, -1, -1) # Initial moisture
    gaMoisTbl.model = mdl
    gaMoisTbl.indexMap = soil
    
    gaMoisIdxs = [(1,'Clay loam', ''),
                  (2, 'Loam', ''),
                  (3, 'Sandy clay loam', '')]
    
    gaMoisValues = [(1, 'SOIL_MOISTURE', 0.200000),
                    (2, 'SOIL_MOISTURE', 0.150000),
                    (3, 'SOIL_MOISTURE', 0.200000)]
    
    # Load Indexes
    idx = []
    for i in gaMoisIdxs:
        mtIDX = MTIndex(i[0], i[1], i[2])
        mtIDX.indexMap = soil
        idx.append(mtIDX)
        
    # Load Variables
    for v in gaMoisValues:
        val = MTValue(v[1], v[2])
        val.mapTable = infilTbl
        val.index = idx[v[0]-1]
        
    # Load Outlet Hydrograph as a Time Series
    otl = TimeSeries('Outlet Hydrograph','otl', 48)
    otl.model = mdl
    
    # Load Values
    otlValues = [(0.00000000,     0.000000), 
                   (30.00000000,     0.000000), 
                   (60.00000000,     0.000000), 
                   (90.00000000,     0.000000), 
                  (120.00000000,     0.000000), 
                  (150.00000000,     0.000000), 
                  (180.00000000,     0.000000), 
                  (210.00000000,     0.000000), 
                  (240.00000000,     0.000000), 
                  (270.00000000,     0.000000), 
                  (300.00000000,     0.000000), 
                  (330.00000000,     0.000000), 
                  (360.00000000,     0.000000), 
                  (390.00000000,     0.000000), 
                  (420.00000000,     0.000000), 
                  (450.00000000,     0.000000), 
                  (480.00000000,     0.000000), 
                  (510.00000000,     0.000000), 
                  (540.00000000,     0.000000), 
                  (570.00000000,     0.000000), 
                  (600.00000000,     0.000000), 
                  (630.00000000,     0.000000), 
                  (660.00000000,     0.000000), 
                  (690.00000000,     0.000000), 
                  (720.00000000,    95.636322), 
                  (750.00000000,    37.418172), 
                  (780.00000000,    13.734266), 
                  (810.00000000,     4.684455), 
                  (840.00000000,     1.687831), 
                  (870.00000000,     0.675520), 
                  (900.00000000,     0.309639), 
                  (930.00000000,     0.150475), 
                  (960.00000000,     0.075994), 
                  (990.00000000,     0.041083), 
                 (1020.00000000,     0.023873), 
                 (1050.00000000,     0.014667), 
                 (1080.00000000,     0.009549), 
                 (1110.00000000,     0.006565), 
                 (1140.00000000,     0.004725), 
                 (1170.00000000,     0.003530), 
                 (1200.00000000,     0.002718), 
                 (1230.00000000,     0.002145), 
                 (1260.00000000,     0.001728), 
                 (1290.00000000,     0.001417), 
                 (1320.00000000,     0.001179), 
                 (1350.00000000,     0.000993), 
                 (1380.00000000,     0.000846), 
                 (1410.00000000,     0.000728)]
    
    for v in otlValues:
        val = TimeSeriesValue(v[0],v[1])
        val.timeseries = otl
        
    """
    """
    Test for multiple scenario functionality
    """
    
    # Add model definition to the session
    DBSession.add(mdl) 
    
    # Define the new scenario for this model
    scn2 = Scenario(name='Test Scenario', description='This is a test scenario', created=date(2013,6,5), base=False)
    scn2.model = mdl
     
    # Get all the project options from the default scenario
    prjOptions = DBSession.query(ProjectCard, ProjectOption).\
                 join(ProjectOption.card).\
                 filter(ProjectOption.scenarios.contains(scn1)).\
                 all()

    # Append new scenario ID to all the existing project options
    # less the cards to be removed
    for crd, opt in prjOptions:
        if crd.name != 'QUIET' and opt.value != '"combo.idx"':
            opt.scenarios.append(scn2)
        
    # Add new cards to the second scenario
    newProjectCards =[('NEW_CARD_1', 'NEWVAL1','BOOLEAN'),
                      ('NEW_CARD_2', 'NEWVAL2','PATH'),
                      ('NEW_CARD_3', 'NEWVAL3','INTEGER'),
                      ('NEW_CARD_4', 'NEWVAL4', 'FLOAT')]
    
    for p in newProjectCards:
        crd = ProjectCard(name=p[0], valueType=p[2])
        prj = ProjectOption(value=p[1])
        prj.card = crd
        prj.model = mdl
        prj.scenarios.append(scn2)
            
      
    
    # DB Commit
    DBSession.add(mdl)    

    
    