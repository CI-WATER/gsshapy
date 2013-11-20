'''
********************************************************************************
* Name: RasterConverter
* Author: Nathan Swain
* Created On: November 19, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''
import math
import xml.etree.ElementTree as ET

class RasterConverter(object):
    '''
    An instance of RasterConverter can be used to extract PostGIS
    rasters from a database and convert them into different formats
    for visualization. Create a new instance of RasterConverter for
    each raster.
    '''
    _session = None
    
    # Definitions
    LINE_COLOR = 'FF000000'
    LINE_WIDTH = 1
    MAX_HEX_DECIMAL = 255
    
    def __init__(self, session=None):
        '''
        Constructor
        '''
        self._session = session

    def getAsKmlGrid(self, tableName, rasterId=1, rasterIdFieldName='id', rasterType='discrete', ramp='rainbow', alpha=1.0, name='default'):
        '''
        Creates a KML file with each cell in the raster represented by a polygon. The
        result is a vector grid representation of the raster
        '''
        # Validation
        if not (rasterType == 'continuous' or rasterType == 'discrete'):
            print 'RASTER CONVERTER WARNING: ' + rasterType + ' is not a valid raster type. Only "continuous" and "discrete" are allowed.'
            raise
            
        if not (alpha >= 0 and alpha <= 1.0):
            print "RASTER CONVERSION ERROR: alpha must be between 0.0 and 1.0."
            raise
        
        # Get polygons for each cell in kml format
        statement = '''
                    SELECT x, y, val, ST_AsKML(geom) AS geomkml
                    FROM (
                    SELECT (ST_PixelAsPolygons(raster)).*
                    FROM %s WHERE %s=%s
                    ) AS foo
                    ORDER BY val;
                    ''' % (tableName, rasterIdFieldName, rasterId)
        
        result = self._session.execute(statement)
        
        groups = dict()
        
        # Post process the query
        for i, j, value, geomkml in result:                
            cell = {'i': i, 'j': j, 'kml':geomkml}
            
            if (str(value) in groups):
                groups[str(value)].append(cell)
            else:
                if (value != 0):
                    groups[str(value)] = [cell]
        
        # Create KML Document            
        kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
        document = ET.SubElement(kml, 'Document')
        name = ET.SubElement(document, 'name')
        name.text = name
        
        # Retrieve the color ramp
        colorRamp = self.colorRamp(ramp)
        
        # Stats for discreet calcluations
        numValues = len(groups)
        valueCount = 0
        
        # Stats for continous calculations
        if (rasterType=='continuous'):
            minIndex = 0.0
            maxIndex = float(len(colorRamp)-1)
            maxValue = float(max(groups, key=float))
            minValue = float(min(groups, key=float))
            
            # Map color ramp indices to values using equation of a line
            # Resulting equation will be:
            # rampIndex = slope * value + intercept
            slope = (maxIndex - minIndex) / (maxValue - minValue)
            intercept = maxIndex - (slope * maxValue)
            
        for value, contents in groups.iteritems():
            if (float(value) > 0):
                # Create new placemark for each unique value
                placemark = ET.SubElement(document, 'Placemark')
                
                # Create style tag and setup styles
                style = ET.SubElement(placemark, 'Style')
                
                # Set polygon line style
                lineStyle = ET.SubElement(style, 'LineStyle')
                
                # Set polygon line color and width
                lineColor = ET.SubElement(lineStyle, 'color')
                lineColor.text = self.LINE_COLOR
                lineWidth = ET.SubElement(lineStyle, 'width')
                lineWidth.text = str(self.LINE_WIDTH)
                
                # Set polygon fill color
                polyStyle = ET.SubElement(style, 'PolyStyle')
                polyColor = ET.SubElement(polyStyle, 'color')
                
                # Interpolate raster to Color Ramp index and increment counter
                if (rasterType == 'continuous'):
                    '''
                    Continuous raster case
                    '''
                    rampIndex = math.trunc(slope * float(value) + intercept)
                    
                elif (rasterType == 'discrete'):
                    '''
                    Discrete raster case
                    '''
                    indexInterval = float(len(colorRamp)) / numValues
                    rampIndex = math.trunc(valueCount*indexInterval)
                    valueCount += 1
                
                # Convert alpha from 0.0-1.0 decimal to 00-FF string
                integerAlpha = int(alpha * self.MAX_HEX_DECIMAL)
                
                # Get RGB color from color ramp and convert to KML hex ABGR string with alpha
                integerRGB = colorRamp[rampIndex]
                hexABGR = '%02X%02X%02X%02X' % (integerAlpha, integerRGB[2], integerRGB[1], integerRGB[0])
                
                # Set the polygon fill alpha and color
                polyColor.text = hexABGR
                
                # Wrap geometry in MultiGeometry tags
                multiGeometry = ET.SubElement(placemark, 'MultiGeometry')
                for cell in contents:
                    polygon = ET.fromstring(cell['kml'])
                    polyName = ET.SubElement(polygon, 'ij')
                    polyName.text = '%s,%s' % (cell['i'], cell['j'])
                    multiGeometry.append(polygon)
                    
                # Create the data tag
                extendedData = ET.SubElement(placemark, 'ExtendedData')
                
                # Add value to data
                valueData = ET.SubElement(extendedData, 'Data', name='value')
                valueValue = ET.SubElement(valueData, 'value')
                valueValue.text = value
                    
        
        return ET.tostring(kml)
                
    def colorRamp(self, ramp='rainbow'):
        '''
        Returns the color ramp as a list of RGB tuples
        '''
        rainbow = [(255, 0, 255), (231, 0, 255), (208, 0, 255), (185, 0, 255), (162, 0, 255), (139, 0, 255), (115, 0, 255), (92, 0, 255), (69, 0, 255), (46, 0, 255), (23, 0, 255),        # magenta to blue
                   (0, 0, 255), (0, 23, 255), (0, 46, 255), (0, 69, 255), (0, 92, 255), (0, 115, 255), (0, 139, 255), (0, 162, 255), (0, 185, 255), (0, 208, 255), (0, 231, 255),          # blue to cyan
                   (0, 255, 255), (0, 255, 231), (0, 255, 208), (0, 255, 185), (0, 255, 162), (0, 255, 139), (0, 255, 115), (0, 255, 92), (0, 255, 69), (0, 255, 46), (0, 255, 23),        # cyan to green
                   (0, 255, 0), (23, 255, 0), (46, 255, 0), (69, 255, 0), (92, 255, 0), (115, 255, 0), (139, 255, 0), (162, 255, 0), (185, 255, 0), (208, 255, 0), (231, 255, 0),          # green to yellow
                   (255, 255, 0), (255, 243, 0), (255, 231, 0), (255, 220, 0), (255, 208, 0), (255, 197, 0), (255, 185, 0), (255, 174, 0), (255, 162, 0), (255, 151, 0), (255, 139, 0),    # yellow to orange
                   (255, 128, 0), (255, 116, 0), (255, 104, 0), (255, 93, 0), (255, 81, 0), (255, 69, 0), (255, 58, 0), (255, 46, 0), (255, 34, 0), (255, 23, 0), (255, 11, 0),            # orange to red
                   (255, 0, 0)]                                                                                                                                                            # red
        
        terrain = [(0, 100, 0), (19, 107, 0), (38, 114, 0), (57, 121, 0), (76, 129, 0), (95, 136, 0), (114, 143, 0), (133, 150, 0), (152, 158, 0), (171, 165, 0), (190, 172, 0),                   # dark green to golden rod yellow
                   (210, 180, 0), (210, 167, 5), (210, 155, 10), (210, 142, 15), (210, 130, 20), (210, 117, 25),                                                                                   # golden rod yellow to orange brown
                   (210, 105, 30), (188, 94, 25), (166, 83, 21), (145, 72, 17), (123, 61, 13), (101, 50, 9),                                                                                       # orange brown to dark brown
                   (80, 40, 5), (95, 59, 27), (111, 79, 50), (127, 98, 73), (143, 118, 95), (159, 137, 118),(175, 157, 141), (191, 176, 164), (207, 196, 186), (223, 215, 209), (239, 235, 232),   # dark brown to white
                   (255, 255, 255)]                                                                                                                                                                # white
        
        aqua = [(150, 255, 255), (136, 240, 250), (122, 226, 245), (109, 212, 240), (95, 198, 235), (81, 184, 230), (68, 170, 225), (54, 156, 220), (40, 142, 215), (27, 128, 210), (13, 114, 205), # aqua to blue
                (0, 100, 200), (0, 94, 195), (0, 89, 191), (0, 83, 187), (0, 78, 182), (0, 72, 178), (0, 67, 174), (0, 61, 170), (0, 56, 165), (0, 50, 161), (0, 45, 157), (0, 40, 153),            # blue to navy blue
                (0, 36, 143), (0, 32, 134), (0, 29, 125), (0, 25, 115), (0, 21, 106), (0, 18, 97), (0, 14, 88), (0, 10, 78), (0, 7, 69), (0, 3, 60), (0, 0, 51)]                                    # navy blue to dark navy blue
        
           
        if (ramp == 'rainbow'):
            return rainbow
        elif (ramp == 'terrain'):
            return terrain
        elif (ramp == 'aqua'):
            return aqua

                                                                                                         
        
   
   
