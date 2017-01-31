from osgeo import gdal, gdalconst, osr
from os import path
from pyproj import Proj

class GDALGrid(object):
    '''
    Loads grid into gdal dataset with projection
    '''
    def __init__(self, grid_file):
        self.dataset = gdal.Open(grid_file, gdalconst.GA_ReadOnly)
        self.projection = osr.SpatialReference()
        self.projection.ImportFromWkt(self.dataset.GetProjection())

    def getGeoTransform(self):
        '''
        returns GeoTransform
        '''
        return self.dataset.GetGeoTransform()

    def getWkt(self):
        '''
        returns WKT projection string
        '''
        return self.projection.ExportToWkt()

    def getProj(self):
        '''
        returns pyproj object
        '''
        return Proj(self.projection.ExportToProj4())

    def getBounds(self):
        '''
        Returns bounding coordinated for raster
        Based on http://gis.stackexchange.com/questions/57834/how-to-get-raster-corner-coordinates-using-python-gdal-bindings
        '''
        min_x, xres, xskew, max_y, yskew, yres = self.getGeoTransform()
        max_x = min_x + self.dataset.RasterXSize * xres + self.dataset.RasterYSize * xskew
        min_y = max_y + self.dataset.RasterYSize * yres + self.dataset.RasterXSize * yskew

        return (min_x, max_x, min_y, max_y)

    def getLatLon(self, two_dimensional=False):
        '''
        Returns latitude and longitude lists
        '''
        min_x, xres, xskew, max_y, yskew, yres = self.getGeoTransform()
        lon1 = min_x + xres/2.0
        lon2 = min_x + (self.dataset.RasterXSize-0.5) * xres + (self.dataset.RasterYSize-0.5) * xskew
        lat2 = max_y + yres/2.0
        lat1 = max_y + (self.dataset.RasterYSize-0.5) * yres + (self.dataset.RasterXSize-0.5) * yskew

        lats = np.linspace(lat1, lat2, self.dataset.RasterYSize)
        lons = np.linspace(lon1, lon2, self.dataset.RasterXSize)

        if two_dimensional:
            return np.meshgrid(lats, lons)

        return lats, lons

class GSSHAGrid(GDALGrid):
    '''
    Loads GSSHA grid into gdal dataset with projection
    '''
    def __init__(self, gssha_ele_grid, gssha_prj_file):
        self.dataset = gdal.Open(gssha_ele_grid, gdalconst.GA_ReadOnly)
        self.projection = osr.SpatialReference()
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
                 x_skew=0,
                 y_max=0,
                 y_skew=0,
                 geotransform=None,
                 name="tmp_ras",
                 gdal_dtype=gdalconst.GDT_Float32):

        num_bands = 1
        if in_array.ndim == 3:
            num_bands = in_array.shape[2]

        self.dataset = gdal.GetDriverByName('MEM').Create(name,
                                                          in_array.shape[0],
                                                          in_array.shape[1],
                                                          num_bands,
                                                          gdal_dtype,
                                                          )

        if geotransform is None:
            self.dataset.SetGeoTransform((x_min, in_array.shape[0], x_skew,
                                          y_max, in_array.shape[1], y_skew))
        else:
            self.dataset.SetGeoTransform(geotransform)

        self.dataset.dataset.SetProjection(wkt_projection)
        self.dataset.dataset.GetRasterBand(1).WriteArray(array)
        self.projection = osr.SpatialReference()
        self.projection.ImportFromWkt(wkt_projection)

def load_raster(grid):
    '''
    grid (str|gdal.Dataset|GDALGrid): str is path to dataset or can pass in GDALGrid or gdal.Dataset.
    '''
    if isinstance(grid, gdal.Dataset):
        src = grid
        src_proj = src.GetProjection()
    elif isinstance(grid, GDALGrid):
        src = grid.dataset
        src_proj = grid.getWkt()
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

    original_grid (str|gdal.Dataset|GDALGrid): If str, reads in path, otherwise assumes gdal.Dataset.
    match_grid (str|gdal.Dataset|GDALGrid): If str, reads in path, otherwise assumes gdal.Dataset.
    to_file (str|bool): If False, returns in memory grid. If str, writes to file.
    output_datatype (gdalconst): A valid datatype from gdalconst (ex. gdalconst.GDT_Float32).
    resample_method (gdalconst): A valid resample method from gdalconst. Default is gdalconst.GRA_Average.
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
        dst_path = "tmp_ras"
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

    # extract subset and resample grid
    gdal.ReprojectImage(src, dst,
                        src_proj,
                        match_proj,
                        resample_method)

    if not to_file:
        print(dst.GetRasterBand(1).ReadAsArray())
        return dst
    if to_file:
        del dst
        return None
    elif as_gdal_grid:


# TODO: http://geoexamples.blogspot.com/2013/09/reading-wrf-netcdf-files-with-gdal.html

# base_folder = 'C:/Users/RDCHLADS/Documents/scripts/gsshapy/tests/grid_standard'
base_folder = '/home/rdchlads/scripts/gsshapy/tests/grid_standard'
data_grid = path.join(base_folder, 'hrrr_hmet_data','2016091407_Pres.asc')
gssha_grid = path.join(base_folder, 'gssha_project', 'grid_standard.ele')
gssha_prj_file = path.join(base_folder, 'gssha_project', 'grid_standard_prj.pro')
out_grid = path.join(base_folder, 'test_resample.tif')
match_ds = GSSHAGrid(gssha_grid, gssha_prj_file)
resample_grid(data_grid, match_ds)

'''
# https://mapbox.github.io/rasterio/topics/resampling.html
# https://mapbox.s3.amazonaws.com/playground/perrygeo/rasterio-docs/cookbook.html

from gdal import osr
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.crs import CRS

with open(gssha_prj_file) as pro_file:
    gssha_prj_str = pro_file.read()
    gssha_srs=osr.SpatialReference()
    gssha_srs.ImportFromWkt(gssha_prj_str)
    dst_crs = CRS.from_string(gssha_srs.ExportToProj4())

with rasterio.Env(CHECK_WITH_INVERT_PROJ=True):
    with rasterio.open(data_grid) as src, \
            rasterio.open(gssha_grid) as grd:
        profile = grd.profile

        # update the relevant parts of the profile
        profile.update({
            'crs': dst_crs,
            'driver': "GTiff",
        })

        # Reproject and write each band
        with rasterio.open(out_grid, 'w', **profile) as dst:
            for i in range(1, src.count + 1):
                src_array = src.read(i)
                dst_array = np.empty((grd.height, grd.width), dtype=src_array.dtype)
                reproject(
                    # Source parameters
                    source=src_array,
                    src_crs=dst_crs,
                    src_transform=src.transform,
                    # Destination paramaters
                    destination=dst_array,
                    dst_transform=grd.transform,
                    dst_crs=dst_crs,
                    # Configuration
                    resampling=Resampling.average,
                    num_threads=1,
                    )
                print(dst_array)

                dst.write(dst_array, i)
'''
