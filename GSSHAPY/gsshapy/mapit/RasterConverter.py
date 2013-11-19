'''
********************************************************************************
* Name: RasterConverter
* Author: Nathan Swain
* Created On: November 19, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''
import random, math
import xml.etree.ElementTree as ET
import xml.dom.minidom

class RasterConverter(object):
    '''
    An instance of RasterConverter can be used to extract PostGIS
    rasters from a database and convert them into different formats
    for visualization. Create a new instance of RasterConverter for
    each raster.
    '''
    _session = None
    _tableName = ''
    _rasterId = 1
    _outFilePath = ''
    _name = ''
    
    # Definitions
    LINE_COLOR = 'FF000000'
    LINE_WIDTH = 1
    
    def __init__(self, session=None, tableName='', rasterId=1, outFilePath='', name=''):
        '''
        Constructor
        '''
        self._session = session
        self._tableName = tableName
        self._rasterId = rasterId
        self._outFilePath = outFilePath
        self._name = name

    def getAsKML(self):
    # Get polygons for each cell in kml format
            statement = '''
                        SELECT x, y, val, ST_AsKML(geom) AS geomkml
                        FROM (
                        SELECT (ST_PixelAsPolygons(raster)).*
                        FROM %s WHERE id=%s
                        ) AS foo
                        ORDER BY val;
                        ''' % (self._tableName, self._rasterId)
            
            result = self._session.execute(statement)
            
            groups = dict()
            
            # Post process the query
            for i, j, value, geomkml in result:                
                cell = {'i': i, 'j': j, 'kml':geomkml}
                
                if (str(value) in groups):
                    groups[str(value)].append(cell)
                else:
                    groups[str(value)] = [cell]
            
            # Create KML Document            
            kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
            document = ET.SubElement(kml, 'Document')
            name = ET.SubElement(document, 'name')
            name.text = self._name
            
            # Number of values
            numValues = len(groups)
            valueCount = 0
                
            for value, contents in groups.iteritems():
                if (float(value) > 0):
                    # Create new placemark for each unique value
                    placemark = ET.SubElement(document, 'Placemark', id=value)
                    placemarkName = ET.SubElement(placemark, 'name')
                    placemarkName.text = value
                    
                    # Link placemark with its style
                    styleURL = ET.SubElement(placemark, 'styleURL')
                    styleURL.text = '#style' + value
                    
                    # Wrap geometry in MultiGeometry tags
                    multiGeometry = ET.SubElement(placemark, 'MultiGeometry')
                    
                    # Create style tag
                    style = ET.SubElement(placemark, 'Style', id=('style' + value))
                    
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
                    
                    # Interpolate to Color Ramp index
                    colorRamp = self._colorRamp()
                    
                    if (len(colorRamp) >= numValues):
                        indexInterval = len(colorRamp) / numValues
                    
                    polyFillColor = 'FF' + colorRamp[valueCount*indexInterval]
                    polyColor.text = polyFillColor
                    
                    valueCount += 1
                    
                    for cell in contents:
                        polygon = ET.fromstring(cell['kml'])
                        multiGeometry.append(polygon)
                        
            this = xml.dom.minidom.parseString(ET.tostring(kml)) 
    #         print this.toprettyxml()   
                
            with open(self._outFilePath, 'w') as f:
                f.write(this.toprettyxml())
                
    def _colorRamp(self, rampName='rainbow', rampFormat='hex'):
        '''
        Returns the color ramp as a list of hex strings or rgb tuplets
        '''
        rainbow = {'rgb': [('255', '0', '255'), ('231', '0', '255'), ('208', '0', '255'), ('185', '0', '255'), ('162', '0', '255'), ('139', '0', '255'), ('115', '0', '255'), ('92', '0', '255'), ('69', '0', '255'), ('46', '0', '255'), ('23', '0', '255'),        # magenta to blue
                           ('0', '0', '255'), ('0', '23', '255'), ('0', '46', '255'), ('0', '69', '255'), ('0', '92', '255'), ('0', '115', '255'), ('0', '139', '255'), ('0', '162', '255'), ('0', '185', '255'), ('0', '208', '255'), ('0', '231', '255'),          # blue to cyan
                           ('0', '255', '255'), ('0', '255', '231'), ('0', '255', '208'), ('0', '255', '185'), ('0', '255', '162'), ('0', '255', '139'), ('0', '255', '115'), ('0', '255', '92'), ('0', '255', '69'), ('0', '255', '46'), ('0', '255', '23'),        # cyan to green
                           ('0', '255', '0'), ('23', '255', '0'), ('46', '255', '0'), ('69', '255', '0'), ('92', '255', '0'), ('115', '255', '0'), ('139', '255', '0'), ('162', '255', '0'), ('185', '255', '0'), ('208', '255', '0'), ('231', '255', '0'),          # green to yellow
                           ('255', '255', '0'), ('255', '243', '0'), ('255', '231', '0'), ('255', '220', '0'), ('255', '208', '0'), ('255', '197', '0'), ('255', '185', '0'), ('255', '174', '0'), ('255', '162', '0'), ('255', '151', '0'), ('255', '139', '0'),    # yellow to orange
                           ('255', '128', '0'), ('255', '116', '0'), ('255', '104', '0'), ('255', '93', '0'), ('255', '81', '0'), ('255', '69', '0'), ('255', '58', '0'), ('255', '46', '0'), ('255', '34', '0'), ('255', '23', '0'), ('255', '11', '0'),            # orange to red
                           ('255', '0', '0')],
                   'hex': ['FF00FF', 'E700FF', 'D000FF', 'B900FF', 'A200FF', '8B00FF', '7300FF', '5C00FF', '4500FF', '2E00FF', '1700FF', # magenta to blue
                           '0000FF', '0017FF', '002EFF', '0045FF', '005CFF', '0073FF', '008BFF', '00A2FF' ,'00B9FF', '00D0FF', '00E7FF', # blue to cyan
                           '00FFFF', '00FFE7', '00FFD0', '00FFB9', '00FFA2', '00FF8B', '00FF73', '00FF5C', '00FF45', '00FF2E', '00FF17', # cyan to green
                           '00FF00', '17FF00', '2EFF00', '45FF00', '5CFF00', '73FF00', '8BFF00', 'A2FF00', 'B9FF00', 'D0FF00', 'E7FF00', # green to yellow
                           'FFFF00', 'FFF300', 'FFE700', 'FFDC00', 'FFD000', 'FFC500', 'FFB900', 'FFAE00', 'FFA200', 'FF9700', 'FF8B00', # yellow to orange
                           'FF8000', 'FF7400', 'FF6800', 'FF5D00', 'FF5100', 'FF4500', 'FF3A00', 'FF2E00', 'FF2200', 'FF1700', 'FF0B00', # orange to red
                           'FF0000']
                   }
        
        if not (rampFormat == 'hex' or rampFormat == 'rgb'):
            # Return nothing if rampFormat is not correct
            print 'COLOR RAMP WARNING: ' + rampFormat + ' is not a valid rampFormat for a color ramp'
            return None
            
        if (rampName == 'rainbow'):
            return rainbow[rampFormat]
                                                                                                         
        
   
   
