from affine import Affine
from csv import writer as csv_writer
from mapkit import lookupSpatialReferenceID
import numpy as np
from osgeo import gdal, gdalconst, ogr, osr
from os import path, getcwd
from pyproj import Proj, transform
import utm


def utm_proj_from_latlon(latitude, longitude, as_wkt=False, as_osr=False):
    '''
    Returns UTM projection information from a latitude, longitude corrdinate pair
    '''
    # get utm coordinates
    utm_centroid_info = utm.from_latlon(latitude, longitude)
    easting, northing, zone_number, zone_letter = utm_centroid_info

    # METHOD USING SetUTM. Not sure if better/worse
    sp_ref = osr.SpatialReference()

    try:
        south_string = ''
        if zone_letter < 'N':
            south_string = ', +south'
        proj4_utm_string = ('+proj=utm +zone={zone_number}{zone_letter}'
                            '{south_string} +ellps=WGS84 +datum=WGS84 '
                            '+units=m +no_defs').format(zone_number=abs(zone_number),
                                                        zone_letter=zone_letter,
                                                        south_string=south_string)
        sp_ref.ImportFromProj4(proj4_utm_string)
    except:
        north_zone = True
        if zone_letter < 'N':
            north_zone = False
        sp_ref.SetUTM(abs(zone_number), north_zone)

    sp_ref.AutoIdentifyEPSG()

    if as_osr:
        return sp_ref
    elif as_wkt:
        return sp_ref.ExportToWkt()
    return sp_ref.ExportToProj4()

def project_to_geographic(x_coord, y_coord, osr_projetion):
    '''
    Project point to geographic
    '''
    # Make sure projected into global projection
    sp_ref = osr.SpatialReference()
    sp_ref.ImportFromEPSG(4326)
    tx = osr.CoordinateTransformation(osr_projetion, sp_ref)
    return tx.TransformPoint(x_coord, y_coord)


class GDALGrid(object):
    '''
    Loads grid into gdal dataset with projection
    '''
    def __init__(self, grid_file, **kwargs):
        if isinstance(grid_file, gdal.Dataset):
            self.dataset = grid_file
        else:
            self.dataset = gdal.Open(grid_file, gdalconst.GA_ReadOnly)

        self._init_projection(**kwargs)
        # identify EPSG code where applicable
        self.projection.AutoIdentifyEPSG()
        self.affine = Affine.from_gdal(*self.dataset.GetGeoTransform())

    def _init_projection(self, **kwargs):
        """initialize projection
        """
        self.projection = osr.SpatialReference()
        self.projection.ImportFromWkt(self.dataset.GetProjection())

    @property
    def geotransform(self):
        return self.dataset.GetGeoTransform()

    @property
    def x_size(self):
        """size of x dimensions
        """
        return self.dataset.RasterXSize

    @property
    def y_size(self):
        """size of y dimensions
        """
        return self.dataset.RasterYSize

    @property
    def wkt(self):
        """WKT projection string
        """
        return self.projection.ExportToWkt()

    @property
    def proj4(self):
        """proj4 string
        """
        return self.projection.ExportToProj4()

    @property
    def proj(self):
        """pyproj.Proj object
        """
        return Proj(self.proj4)

    @property
    def epsg(self):
        """EPSG code
        """
        epsg =  self.projection.GetAuthorityCode(None)
        if epsg:
            return epsg
        # attempt online lookup
        return lookupSpatialReferenceID(self.wkt)

    def bounds(self, as_geographic=False, as_utm=False):
        """Returns bounding coordinates for raster
        """
        x_min, y_min = self.affine * (0, self.dataset.RasterYSize)
        x_max, y_max = self.affine * (self.dataset.RasterXSize, 0)
        if as_geographic or as_utm:
            lon_min, lat_max, ulz = project_to_geographic(x_min, y_max,
                                                          self.projection)
            lon_max, lat_min, brz = project_to_geographic(x_max, y_min,
                                                          self.projection)
            if as_geographic:
                return(lon_min, lon_max, lat_min, lat_max)

            # convert to UTM
            utm_osr = utm_proj_from_latlon((lat_min+lat_max)/2.0,
                                           (lon_min+lon_max)/2.0,
                                           as_osr=True)
            tx = osr.CoordinateTransformation(self.projection, utm_osr)
            x_min, y_max, ulz = tx.TransformPoint(x_min, y_max)
            x_max, y_min, brz = tx.TransformPoint(x_max, y_min)

        return (x_min, x_max, y_min, y_max)

    def pixel2coord(self, col, row):
        """Returns global coordinates to pixel center using base-0 raster index
           http://gis.stackexchange.com/questions/53617/how-to-find-lat-lon-values-for-every-pixel-in-a-geotiff-file
        """
        return self.affine * (col+0.5, row+0.5)

    def coord2pixel(self, x_coord, y_coord):
        """Returns base-0 raster index using global coordinates to pixel center
        """
        col, row = ~self.affine * (x_coord, y_coord)
        if col > self.x_size or col < 0:
            raise IndexError("Longitude {0} is out of bounds ...".format(x_coord))
        if row > self.y_size or row < 0:
            raise IndexError("Latitude {0} is out of bounds ...".format(y_coord))

        return (int(col), int(row))

    def pixel2lonlat(self, col, row):
        """Returns latitude and longitude to pixel center using base-0 raster index
        """
        x_coord, y_coord = self.pixel2coord(col, row)
        longitude, latitude, z_coord = project_to_geographic(x_coord, y_coord,
                                                             self.projection)
        return (longitude, latitude)

    def lonlat2pixel(self, longitude, latitude):
        """Returns base-0 raster index using longitude and latitude of pixel center
        """
        sp_ref = osr.SpatialReference()
        sp_ref.ImportFromEPSG(4326) # geographic
        tx = osr.CoordinateTransformation(sp_ref, self.projection)
        x_coord, y_coord, z_coord = tx.TransformPoint(longitude, latitude)
        return self.coord2pixel(x_coord, y_coord)

    def lat_lon(self, two_dimensional=False):
        """Returns latitude and longitude lists
        """
        lats_2d = np.zeros((self.y_size, self.x_size))
        lons_2d = np.zeros((self.y_size, self.x_size))
        for x in range(self.x_size):
            for y in range(self.y_size):
                lons_2d[y,x], lats_2d[y,x] = self.pixel2coord(x,y)

        proj_lons, proj_lats = transform(self.proj,
                                         Proj(init='epsg:4326'),
                                         lons_2d,
                                         lats_2d,
                                         )
        if not two_dimensional:
            return proj_lats.mean(axis=1), proj_lons.mean(axis=0)

        return proj_lats, proj_lons

    def np_array(self, band=1):
        """Returns the raster band as a numpy array
        """
        if band == 'all':
            grid_data = self.dataset.ReadAsArray()
        else:
            raster_band = self.dataset.GetRasterBand(band)
            grid_data = raster_band.ReadAsArray()
            nodata_value = raster_band.GetNoDataValue()
            if nodata_value is not None:
                return np.ma.array(data=grid_data,
                                   mask=(grid_data==nodata_value))
        return np.array(grid_data)

    def write_prj(self, out_projection_file, esri_format=False):
        """Writes ESRI projection file
        """
        if esri_format:
            self.projection.MorphToESRI()
        with open(out_projection_file, 'w') as prj_file:
            prj_file.write(self.wkt)
            prj_file.close()

    def to_tif(self, file_path, out_epsg=None):
        """Write out as geotiff
        """
        if out_epsg:
            return gdal_reproject(self.dataset, file_path,
                                  src_srs=self.projection,
                                  epsg=out_epsg)
        else:
            drv = gdal.GetDriverByName('GTiff')
            return drv.CreateCopy(file_path, self.dataset)

    def _to_ascii(self, header_string, file_path, band, print_nodata=True):
        """Writes data to ascii file
        """
        if print_nodata:
            nodata_value = self.dataset.GetRasterBand(band).GetNoDataValue()
            if nodata_value is not None:
                header_string += "NODATA_value {0}\n".format(nodata_value)

        with open(file_path, 'w') as out_ascii_grid:
            out_ascii_grid.write(header_string)
            grid_writer = csv_writer(out_ascii_grid,
                                     delimiter=" ")
            grid_writer.writerows(self.np_array(band))

    def to_grass_ascii(self, file_path, band=1, print_nodata=True):
        """Writes data to GRASS ASCII file format.

            Parameters:
                file_path(str): Path to output ascii file.
                band(Optional[int]): Band number (1-based).
        """
        # PART 1: HEADER
        # get data extremes
        west_bound, east_bound, south_bound, north_bound = self.bounds()
        header_string = u"north: {0:.9f}\n".format(north_bound)
        header_string += "south: {0:.9f}\n".format(south_bound)
        header_string += "east: {0:.9f}\n".format(east_bound)
        header_string += "west: {0:.9f}\n".format(west_bound)
        header_string += "rows: {0}\n".format(self.y_size)
        header_string += "cols: {0}\n".format(self.x_size)

        # PART 2: WRITE DATA
        self._to_ascii(header_string, file_path, band, print_nodata)

    def to_arc_ascii(self, file_path, band=1, print_nodata=True):
        """Writes data to Arc ASCII file format.

            Parameters:
                file_path(str): Path to output ascii file.
                band(Optional[int]): Band number (1-based).
        """
        # PART 1: HEADER
        # get data extremes
        west_bound, east_bound, south_bound, north_bound = self.bounds()
        cellsize = (self.geotransform[1] - self.geotransform[-1])/2.0
        header_string = u"ncols {0}\n".format(self.x_size)
        header_string += "nrows {0}\n".format(self.y_size)
        header_string += "xllcorner {0}\n".format(west_bound)
        header_string += "yllcorner {0}\n".format(south_bound)
        header_string += "cellsize {0}\n".format(cellsize)

        #PART 2: WRITE DATA
        self._to_ascii(header_string, file_path, band, print_nodata)

class GSSHAGrid(GDALGrid):
    """Loads GSSHA grid into gdal dataset with projection
    """
    def __init__(self, gssha_ele_grid, gssha_prj_file):
        dataset = gdal.Open(gssha_ele_grid, gdalconst.GA_ReadOnly)
        super(GSSHAGrid, self).__init__(dataset, gssha_prj_file=gssha_prj_file)

    def _init_projection(self, **kwargs):
        """initialize projection
        """
        self.projection = osr.SpatialReference()
        gssha_prj_file = kwargs.get('gssha_prj_file')
        with open(gssha_prj_file) as pro_file:
            self.projection.ImportFromWkt(pro_file.read())

class ArrayGrid(GDALGrid):
    '''
    Loads numpy array gdal dataset with projection
    '''
    def __init__(self,
                 in_array,
                 wkt_projection,
                 x_min=0,
                 x_pixel_size=0,
                 x_skew=0,
                 y_max=0,
                 y_pixel_size=0,
                 y_skew=0,
                 geotransform=None,
                 name="tmp_ras",
                 gdal_dtype=gdalconst.GDT_Float32):

        num_bands = 1
        if in_array.ndim == 3:
            num_bands, y_size, x_size = in_array.shape
        else:
            y_size, x_size = in_array.shape

        dataset = gdal.GetDriverByName('MEM').Create(name,
                                                     x_size,
                                                     y_size,
                                                     num_bands,
                                                     gdal_dtype,
                                                     )

        if geotransform is None:
            dataset.SetGeoTransform((x_min, x_pixel_size, x_skew,
                                     y_max, y_skew, -y_pixel_size))
        else:
            dataset.SetGeoTransform(geotransform)

        dataset.SetProjection(wkt_projection)
        if in_array.ndim == 3:
            for band in range(1, num_bands+1):
                dataset.GetRasterBand(band).WriteArray(in_array[band-1])
        else:
            dataset.GetRasterBand(1).WriteArray(in_array)

        super(ArrayGrid, self).__init__(dataset)

def geotransform_from_latlon(lats, lons, proj=None):
    '''
    get geotransform from arrays of latitude and longitude
    WORKING PROGRESS

    Parameters:
        lats(numpy array): Array of latitudes.
        lons(numpy array): Array of longitudes.
        proj(pyproj.Proj): Output projection.

    '''
    if lats.ndim < 2:
        lons_2d, lats_2d = np.meshgrid(lons, lats)
    else:
        lons_2d = lons
        lats_2d = lats

    if proj:
        # get projected transform
        lons_2d, lats_2d = transform(Proj(init='epsg:4326'),
                                     proj,
                                     lons_2d,
                                     lats_2d,
                                     )

    # get cell size
    x_cell_size = np.nanmean(np.absolute(np.diff(lons_2d, axis=1)))
    y_cell_size = np.nanmean(np.absolute(np.diff(lats_2d, axis=0)))
    # get top left corner
    min_x_tl = lons_2d[0,0] - x_cell_size/2.0
    max_y_tl = lats_2d[0,0] + y_cell_size/2.0
    return (min_x_tl, x_cell_size, 0, max_y_tl, 0, -y_cell_size)

def load_raster(grid):
    '''
    Parameters:
        grid(str|gdal.Dataset|GDALGrid): str is path to dataset or can pass in GDALGrid or gdal.Dataset.
    '''
    if isinstance(grid, gdal.Dataset):
        src = grid
        src_proj = src.GetProjection()
    elif isinstance(grid, GDALGrid):
        src = grid.dataset
        src_proj = grid.wkt
    else:
        src = gdal.Open(grid, gdalconst.GA_ReadOnly)
        src_proj = src.GetProjection()

    return src, src_proj

def resample_grid(original_grid,
                  match_grid,
                  to_file=False,
                  output_datatype=None,
                  resample_method=gdalconst.GRA_Average,
                  as_gdal_grid=False):
    '''
    This function resamples a grid and outputs the result to a file

    Parameters:
        original_grid(str|gdal.Dataset|GDALGrid): If str, reads in path, otherwise assumes gdal.Dataset.
        match_grid(str|gdal.Dataset|GDALGrid): If str, reads in path, otherwise assumes gdal.Dataset.
        to_file(Optional[str|bool]): If False, returns in memory grid. If str, writes to file.
        output_datatype(Optional[gdalconst]): A valid datatype from gdalconst (ex. gdalconst.GDT_Float32).
        resample_method(Optional[gdalconst]): A valid resample method from gdalconst. Default is gdalconst.GRA_Average.
        as_gdal_grid(Optional[bool]): If True, it will return as a GDALGrid object. Default is False.

    '''
    # http://stackoverflow.com/questions/10454316/how-to-project-and-resample-a-grid-to-match-another-grid-with-gdal-python

    # Source of the data
    src, src_proj = load_raster(original_grid)
    src_geotrans = src.GetGeoTransform()

    # ensure output datatype is set
    if output_datatype is None:
        output_datatype = src.GetRasterBand(1).DataType

    # Grid to use to extract subset and match
    match_ds, match_proj = load_raster(match_grid)
    match_geotrans = match_ds.GetGeoTransform()

    if not to_file:
        # in memory raster
        dst_driver = gdal.GetDriverByName('MEM')
        dst_path = ""
    else:
        # geotiff
        dst_driver = gdal.GetDriverByName('GTiff')
        dst_path = to_file

    dst = dst_driver.Create(dst_path,
                            match_ds.RasterXSize,
                            match_ds.RasterYSize,
                            src.RasterCount,
                            output_datatype)

    dst.SetGeoTransform(match_geotrans)
    dst.SetProjection(match_proj)

    for band_i in range(1, dst.RasterCount+1):
        nodata_value = src.GetRasterBand(band_i).GetNoDataValue()
        if not nodata_value:
            nodata_value = -9999
        dst.GetRasterBand(band_i).SetNoDataValue(nodata_value)

    # extract subset and resample grid
    gdal.ReprojectImage(src, dst,
                        src_proj,
                        match_proj,
                        resample_method)

    if not to_file:
        if as_gdal_grid:
            return GDALGrid(dst)
        else:
            return dst
    else:
        del dst
        return None


def reproject_layer(in_path, out_path, outSpatialRef):
    """
    From: https://pcjericks.github.io/py-gdalogr-cookbook/projection.html
    """
    driver = ogr.GetDriverByName('ESRI Shapefile')

    # get the input layer
    inDataSet = driver.Open(in_path)
    inLayer = inDataSet.GetLayer()

    # input SpatialReference
    inSpatialRef = inLayer.GetSpatialRef()

    # create the CoordinateTransformation
    coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)

    # create the output layer
    outputShapefile = out_path
    if path.exists(outputShapefile):
        driver.DeleteDataSource(outputShapefile)
    outDataSet = driver.CreateDataSource(outputShapefile)
    outLayer = outDataSet.CreateLayer("", geom_type=ogr.wkbMultiPolygon)

    # add fields
    inLayerDefn = inLayer.GetLayerDefn()
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)

    # get the output layer's feature definition
    outLayerDefn = outLayer.GetLayerDefn()

    # loop through the input features
    inFeature = inLayer.GetNextFeature()
    while inFeature:
        # get the input geometry
        geom = inFeature.GetGeometryRef()
        # reproject the geometry
        geom.Transform(coordTrans)
        # create a new feature
        outFeature = ogr.Feature(outLayerDefn)
        # set the geometry and attribute
        outFeature.SetGeometry(geom)
        for i in range(0, outLayerDefn.GetFieldCount()):
            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))
        # add the feature to the shapefile
        outLayer.CreateFeature(outFeature)
        # dereference the features and get the next input feature
        outFeature = None
        inFeature = inLayer.GetNextFeature()

    # Save and close the shapefiles
    inDataSet = None
    outDataSet = None

    # write projection
    shapefile_basename = path.splitext(out_path)[0]
    projection_file_name = "{shapefile_basename}.prj" \
                          .format(shapefile_basename=shapefile_basename)
    with open(projection_file_name, 'w') as prj_file:
        prj_file.write(outSpatialRef.ExportToWkt())
        prj_file.close()

def gdal_reproject(src,
                   dst=None,
                   epsg=None,
                   src_srs=None,
                   dst_srs=None,
                   error_threshold=0.125,
                   resampling=gdal.GRA_NearestNeighbour,
                   as_gdal_grid=False):
    """
    FROM: https://github.com/OpenDataAnalytics/gaia/blob/master/gaia/geo/gdal_functions.py
    To be removed when gaia is conda package.

    Reproject a raster image
    :param src: The source image
    :param dst: The filepath/name of the output image
    :param epsg: The EPSG code to reproject to
    :param error_threshold: Default is 0.125 (same as gdalwarp commandline)
    :param resampling: Default method is Nearest Neighbor
    """
    # Open source dataset
    src_ds, src_proj = load_raster(src)

    # Define target SRS
    if dst_srs is None:
        dst_srs = osr.SpatialReference()
        dst_srs.ImportFromEPSG(int(epsg))

    dst_wkt = dst_srs.ExportToWkt()

    # Resampling might be passed as a string
    if not isinstance(resampling, int):
        resampling = getattr(gdal, resampling)

    src_wkt = None
    if src_srs is not None:
        src_wkt = src_srs.ExportToWkt()

    # Call AutoCreateWarpedVRT() to fetch default values
    # for target raster dimensions and geotransform
    reprojected_ds = gdal.AutoCreateWarpedVRT(src_ds,
                                              src_wkt,
                                              dst_wkt,
                                              resampling,
                                              error_threshold)

    # Create the final warped raster
    if dst:
        gdal.GetDriverByName('GTiff').CreateCopy(dst, reprojected_ds)
    if as_gdal_grid:
        return GDALGrid(reprojected_ds)
    return reprojected_ds


def rasterize_shapefile(shapefile_path,
                        out_raster_path=None,
                        shapefile_attribute=None,
                        x_cell_size=None,
                        y_cell_size=None,
                        x_num_cells=None,
                        y_num_cells=None,
                        match_grid=None,
                        raster_wkt_proj=None,
                        convert_to_utm=False,
                        raster_dtype=gdal.GDT_Int32,
                        raster_nodata=-9999,
                        as_gdal_grid=False):
    """
    Convert shapefile to raster from specified attribute

    Parameters:
        shapefile_path(str): Path to shapefile.
        out_raster_path(Optional[str]): Path to raster to be generated.
        shapefile_attribute(Optional[str]): Attribute to be rasterized.
        x_cell_size(Optional[float]): Longitude cell size in output projection.
        y_cell_size(Optional[float]): latitude cell size in output projection.
        x_num_cells(Optional[int]): Number of cells in latitude.
        y_num_cells(Optional[int]): Number of cells in longitude.
        match_grid(Optional[str|gdal.Dataset|GDALGrid]): Grid to match for output.
        raster_wkt_proj(Optional[str]): WKT projections string for output grid.
        convert_to_utm(Optional[bool]): Convert grid to UTM automatically.
        raster_dtype(Optional[gdal GDT]): Output grid datatype. Default is gdal.GDT_Int32.
        raster_nodata(Optional[float,int]): No data value for output raster. Default is -9999,
        as_gdal_grid((Optional[bool]): Return as GDAL grid. Default is False.

    Example Default::

        from gridtogssha.grid_tools import rasterize_shapefile

        shapefile_path = 'shapefile.shp'
        new_grid = 'new_grid.tif'
        rasterize_shapefile(shapefile_path,
                            new_grid,
                            x_num_cells=50,
                            y_num_cells=50,
                            raster_nodata=0,
                            )

    Example GDALGrid to ASCII with UTM::

        from gridtogssha.grid_tools import rasterize_shapefile

        shapefile_path = 'shapefile.shp'
        new_grid = 'new_grid.asc'
        gr = rasterize_shapefile(shapefile_path,
                                 x_num_cells=50,
                                 y_num_cells=50,
                                 raster_nodata=0,
                                 convert_to_utm=True,
                                 as_gdal_grid=True,
                                 )
        gr.to_grass_ascii(new_grid, print_nodata=False)

    """
    if as_gdal_grid:
        raster_driver = gdal.GetDriverByName('MEM')
        out_raster_path = ''
    elif out_raster_path is not None:
        raster_driver = gdal.GetDriverByName('GTiff')
    else:
        raise ValueError("Either out_raster_path or as_gdal_grid need to be set ...")

    # open the data source
    shapefile = ogr.Open(shapefile_path)
    source_layer = shapefile.GetLayer(0)

    x_min, x_max, y_min, y_max = source_layer.GetExtent()
    shapefile_spatial_ref = source_layer.GetSpatialRef()
    reprojected_layer = None
    # determine UTM projection from centroid of shapefile
    if convert_to_utm:
        # Make sure projected into global projection
        lon_min, lat_max, ulz = project_to_geographic(x_min, y_max,
                                                      shapefile_spatial_ref)
        lon_max, lat_min, brz = project_to_geographic(x_max, y_min,
                                                      shapefile_spatial_ref)

        # get UTM projection for watershed
        raster_wkt_proj = utm_proj_from_latlon((lat_min+lat_max)/2.0,
                                               (lon_min+lon_max)/2.0,
                                               as_wkt=True)
    # reproject shapefile to new projection
    if raster_wkt_proj is not None:
        shapefile_basename = path.splitext(shapefile_path)[0]
        reprojected_layer = "{shapefile_basename}_projected.shp" \
                             .format(shapefile_basename=shapefile_basename)
        outSpatialRef = osr.SpatialReference()
        outSpatialRef.ImportFromWkt(raster_wkt_proj)
        reproject_layer(shapefile_path, reprojected_layer, outSpatialRef)
        reprojected_shapefile = ogr.Open(reprojected_layer)
        source_layer = reprojected_shapefile.GetLayer(0)

        x_min, x_max, y_min, y_max = source_layer.GetExtent()
        shapefile_spatial_ref = source_layer.GetSpatialRef()

    if match_grid is not None:
        # grid to match
        match_ds, match_proj = load_raster(match_grid)
        match_geotrans = match_ds.GetGeoTransform()
        x_num_cells = match_ds.RasterXSize
        y_num_cells = match_ds.RasterYSize

    elif x_cell_size is not None and y_cell_size is not None:
        # caluclate nuber of cells in extent
        x_num_cells = int((x_max - x_min) / x_cell_size)
        y_num_cells = int((y_max - y_min) / y_cell_size)
        match_geotrans = (x_min, x_cell_size, 0, y_max, 0, -y_cell_size)
        match_proj = shapefile_spatial_ref.ExportToWkt()

    elif x_num_cells is not None and y_num_cells is not None:
        x_cell_size = (x_max - x_min) / float(x_num_cells)
        y_cell_size = (y_max - y_min) / float(y_num_cells)
        match_geotrans = (x_min, x_cell_size, 0, y_max, 0, -y_cell_size)
        match_proj = shapefile_spatial_ref.ExportToWkt()

    else:
        raise ValueError("Invalid parameters for output grid entered ...")

    # geotiff
    target_ds = raster_driver.Create(out_raster_path,
                                     x_num_cells,
                                     y_num_cells,
                                     1,
                                     raster_dtype)

    target_ds.SetGeoTransform(match_geotrans)
    target_ds.SetProjection(match_proj)
    band = target_ds.GetRasterBand(1)
    band.SetNoDataValue(raster_nodata)

    # rasterize
    if shapefile_attribute is not None:
        err = gdal.RasterizeLayer(target_ds, [1], source_layer,
                                  options=["ATTRIBUTE={0}".format(attribute)])
    else:
        err = gdal.RasterizeLayer(target_ds, [1], source_layer,
                                  burn_values=[1])

    if err != 0:
        raise Exception("Error rasterizing layer: %s" % err)


    if raster_wkt_proj is not None and raster_wkt_proj != match_proj:
        # from http://gis.stackexchange.com/questions/139906/replicating-result-of-gdalwarp-using-gdal-python-bindings
        error_threshold = 0.125 # error threshold --> use same value as in gdalwarp
        resampling = gdal.GRA_NearestNeighbour

        # Call AutoCreateWarpedVRT() to fetch default values for target raster dimensions and geotransform
        target_ds = gdal.AutoCreateWarpedVRT(target_ds,
                                             None, # src_wkt : left to default value --> will use the one from source
                                             raster_wkt_proj,
                                             resampling,
                                             error_threshold)
        if not as_gdal_grid:
            # Create the final warped raster
            target_ds = gdal.GetDriverByName('GTiff').CreateCopy(out_raster_path, target_ds)

    # clean up
    if reprojected_layer is not None:
        driver = ogr.GetDriverByName("ESRI Shapefile")
        if path.exists(reprojected_layer):
             driver.DeleteDataSource(reprojected_layer)

    if as_gdal_grid:
        return GDALGrid(target_ds)
