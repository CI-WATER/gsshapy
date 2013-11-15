'''
********************************************************************************
* Name: GeoAlchemy Spatial Functions for PostGIS
* Author: Nathan Swain
* Created On: November 14, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

from geoalchemy2 import Geometry, Raster
from geoalchemy2.functions import GenericFunction

class ST_DumpAsPolygons(GenericFunction):
    '''
    GeoAlchemy Function for PostGIS Raster Function: ST_DumpAsPolygons
    See PostGIS documentation for usage: http://postgis.net/docs/RT_ST_DumpAsPolygons.html
    '''
    name = 'ST_DumpAsPolygons'
    type = Raster
    
class ST_PixelAsPolygons(GenericFunction):
    '''
    GeoAlchemy Function for PostGIS Raster Function: ST_PixelAsPolygons
    See PostGIS documentation for usage: http://postgis.net/docs/RT_ST_PixelAsPolygons.html
    '''
    name = 'ST_PixelAsPolygons'
    type = Raster