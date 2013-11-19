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
    _name = 'raster'
    _rasterType='discrete'
    
    # Definitions
    LINE_COLOR = 'FF000000'
    LINE_WIDTH = 1
    MAX_HEX_DECIMAL = 255
    
    def __init__(self, session=None, tableName='', rasterId=1, outFilePath='', name='raster', rasterType='discrete'):
        '''
        Constructor
        '''
        self._session = session
        self._tableName = tableName
        self._rasterId = rasterId
        self._outFilePath = outFilePath
        self._name = name
        
        if not (rasterType == 'continuous' or rasterType == 'discrete'):
            print 'RASTER CONVERTER WARNING: ' + rasterType + ' is not a valid raster type. Only "continuous" and "discrete" are allowed.'
            raise
        
        self._rasterType = rasterType

    def getAsKmlGrid(self, ramp='rainbow', alpha=1.0):
        '''
        Creates a KML file with each cell in the raster represented by a polygon. The
        result is a vector grid representation of the raster
        '''
            
        if not (alpha >= 0 and alpha <= 1.0):
            print "RASTER CONVERSION ERROR: alpha must be between 0.0 and 1.0."
            raise
        
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
                if (value != 0):
                    groups[str(value)] = [cell]
        
        # Create KML Document            
        kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
        document = ET.SubElement(kml, 'Document')
        name = ET.SubElement(document, 'name')
        name.text = self._name
        
        # Retrieve the color ramp
        colorRamp = self.colorRamp(ramp, rampFormat='hex')
        
        # Stats for discreet calcluations
        numValues = len(groups)
        valueCount = 0
        
        # Stats for continous calculations
        if (self._rasterType=='continuous'):
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
                
                # Interpolate to Color Ramp index and increment counter
                if (self._rasterType == 'continuous'):
                    '''
                    Continuous raster case
                    '''
                    rampIndex = math.trunc(slope * float(value) + intercept)
                    
                elif (self._rasterType == 'discrete'):
                    '''
                    Discrete raster case
                    '''
                    indexInterval = float(len(colorRamp)) / numValues
                    rampIndex = math.trunc(valueCount*indexInterval)
                    valueCount += 1
                
                # Convert alpha from 0.0-1.0 decimal to 00-FF string
                hexAlpha = hex(int(alpha * self.MAX_HEX_DECIMAL))[2:]
                
                # Get RGB color from color ramp and add alpha component
                polyFillColor = hexAlpha + colorRamp[rampIndex]
                polyColor.text = polyFillColor
                
                # Add geometry to file
                for cell in contents:
                    polygon = ET.fromstring(cell['kml'])
                    multiGeometry.append(polygon)
                    
        this = xml.dom.minidom.parseString(ET.tostring(kml)) 
        #         print this.toprettyxml()   
            
        with open(self._outFilePath, 'w') as f:
            f.write(this.toprettyxml())
                
    def colorRamp(self, ramp='rainbow', rampFormat='hex'):
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
        
        terrain = {'rgb': [('245', '200', '0'), ('235', '189', '1'), ('225', '178', '3'), ('216', '167', '5'), ('206', '156', '6'), ('196', '145', '8'),
                           ('187', '134', '10'), ('177', '123', '12'), ('167', '112', '13'), ('158', '101', '15'), ('148', '90', '17'), ('139', '80', '19'),
                           ('134', '81', '18'), ('130', '83', '17'), ('126', '85', '16'), ('122', '86', '15'), ('117', '88', '14'), ('113', '90', '13'),
                           ('109', '91', '12'), ('105', '93', '11'), ('100', '95', '10'), ('96', '96', '9'), ('92', '98', '9'), ('88', '100', '8'),
                           ('83', '101', '7'), ('79', '103', '6'), ('75', '105', '5'), ('71', '106', '4'), ('66', '108', '3'), ('62', '110', '2'),
                           ('58', '111', '1'), ('54', '113', '0'), ('50', '115', '0'), ('53', '115', '6'), ('57', '116', '12'), ('61', '116', '18'),
                           ('64', '117', '24'), ('68', '118', '30'), ('72', '118', '36'), ('76', '119', '42'), ('79', '119', '48'), ('83', '120', '54'),
                           ('87', '121', '60'), ('90', '121', '67'), ('94', '122', '73'), ('98', '123', '79'), ('102', '123', '85'), ('105', '124', '91'),
                           ('109', '124', '97'), ('113', '125', '103'), ('116', '126', '109'), ('120', '126', '115'), ('124', '127', '121'), ('128', '128', '128'),
                           ('149', '149', '149'), ('170', '170', '170'), ('191', '191', '191'), ('212', '212', '212'), ('233', '233', '233'), ('255', '255', '255')],
                   'hex': ['F5C800', 'EBBD01', 'E1B203', 'D8A705', 'CE9C06', 'C49108', 'BB860A', 'B17B0C', 'A7700D', '9E650F', '945A11',
                           '8B5013', '865112', '825311', '7E5510', '7A560F', '75580E', '715A0D', '6D5B0C', '695D0B', '645F0A', '606009',
                           '5C6209', '586408', '536507', '4F6706', '4B6905', '476A04', '426C03', '3E6E02', '3A6F01', '367100', '327300',
                           '357306', '39740C', '3D7412', '407518', '44761E', '487624', '4C772A', '4F7730', '537836', '57793C', '5A7943',
                           '5E7A49', '627B4F', '667B55', '697C5B', '6D7C61', '717D67', '747E6D', '787E73', '7C7F79', '808080', '959595',
                           'AAAAAA', 'BFBFBF', 'D4D4D4', 'E9E9E9', 'FFFFFF']
                   }
      
        
        if not (rampFormat == 'hex' or rampFormat == 'rgb'):
            # Return nothing if rampFormat is not correct
            print 'COLOR RAMP WARNING: ' + rampFormat + ' is not a valid rampFormat for a color ramp'
            raise
            
        if (ramp == 'rainbow'):
            return rainbow[rampFormat]
        elif (ramp == 'terrain'):
            return terrain[rampFormat]
                                                                                                         
        
   
   
