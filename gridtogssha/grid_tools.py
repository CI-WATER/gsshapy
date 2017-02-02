from affine import Affine
import numpy as np
from osgeo import gdal, gdalconst, osr
from os import path
from pyproj import Proj, transform


class GDALGrid(object):
    '''
    Loads grid into gdal dataset with projection
    '''
    def __init__(self, grid_file):
        if isinstance(grid_file, gdal.Dataset):
            self.dataset = grid_file
        else:
            self.dataset = gdal.Open(grid_file, gdalconst.GA_ReadOnly)

        self.projection = osr.SpatialReference()
        self.projection.ImportFromWkt(self.dataset.GetProjection())
        self.affine = Affine.from_gdal(*self.dataset.GetGeoTransform())

    def geotransform(self):
        return self.dataset.GetGeoTransform()

    def x_size(self):
        return self.dataset.RasterXSize

    def y_size(self):
        return self.dataset.RasterYSize

    def wkt(self):
        '''
        returns WKT projection string
        '''
        return self.projection.ExportToWkt()

    def proj(self):
        '''
        returns pyproj object
        '''
        return Proj(self.projection.ExportToProj4())

    def bounds(self):
        '''
        Returns bounding coordinates for raster
        '''
        x_min, y_min = self.affine * (0, self.dataset.RasterYSize)
        x_max, y_max = self.affine * (self.dataset.RasterXSize, 0)
        return (x_min, x_max, y_min, y_max)

    def pixel2coord(self, col, row):
        """Returns global coordinates to pixel center using base-0 raster index
           http://gis.stackexchange.com/questions/53617/how-to-find-lat-lon-values-for-every-pixel-in-a-geotiff-file
        """
        return self.affine * (col+0.5, row+0.5)


    def lat_lon(self, two_dimensional=False):
        '''
        Returns latitude and longitude lists
        '''
        lats_2d = np.zeros((self.y_size(), self.x_size()))
        lons_2d = np.zeros((self.y_size(), self.x_size()))
        for x in range(self.x_size()):
            for y in range(self.y_size()):
                lons_2d[y,x], lats_2d[y,x] = self.pixel2coord(x,y)

        proj_lons, proj_lats = transform(self.proj(),
                                         Proj(init='epsg:4326'),
                                         lons_2d,
                                         lats_2d,
                                         )
        if not two_dimensional:
            return proj_lats.mean(axis=1), proj_lons.mean(axis=0)

        return proj_lats, proj_lons

    def np_array(self, band=1):
        '''
        Returns the raster band as a numpy array
        '''
        if band == 'all' and self.dataset.RasterCount > 1:
            grid_data = []
            for band in range(1, self.dataset.RasterCount+1):
                grid_data.append(self.dataset.GetRasterBand(band).ReadAsArray())
        else:
            grid_data = self.dataset.GetRasterBand(band).ReadAsArray()

        return np.array(grid_data)


class GSSHAGrid(GDALGrid):
    '''
    Loads GSSHA grid into gdal dataset with projection
    '''
    def __init__(self, gssha_ele_grid, gssha_prj_file):
        dataset = gdal.Open(gssha_ele_grid, gdalconst.GA_ReadOnly)
        super(GSSHAGrid, self).__init__(dataset)
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
    x_cell_size = np.max(np.absolute(np.diff(lons_2d, axis=1)))
    y_cell_size = -np.max(np.absolute(np.diff(lats_2d, axis=0)))
    # get top left corner
    min_x_tl = lons_2d[0,0] - x_cell_size/2.0
    max_y_tl = lats_2d[0,0] + y_cell_size/2.0
    # get bottom rignt corner
    max_x_br = lons_2d[-1,-1] + x_cell_size/2.0
    min_y_br = lats_2d[-1,-1] - y_cell_size/2.0
    # calculate size
    x_size = lons_2d.shape[1]
    y_size = lons_2d.shape[0]
    # calculate skew
    # x_skew = (max_x_br - min_x_tl - x_size * x_cell_size)/y_size
    # y_skew = (min_y_br - max_y_tl - y_size * y_cell_size)/x_size
    # geotransform = (min_x_tl, x_cell_size, x_skew, max_y_tl, y_skew, y_cell_size)
    return (min_x_tl, x_cell_size, 0, max_y_tl, 0, y_cell_size)

def load_raster(grid):
    '''
    grid (str|gdal.Dataset|GDALGrid): str is path to dataset or can pass in GDALGrid or gdal.Dataset.
    '''
    if isinstance(grid, gdal.Dataset):
        src = grid
        src_proj = src.GetProjection()
    elif isinstance(grid, GDALGrid):
        src = grid.dataset
        src_proj = grid.wkt()
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
    as_gdal_grid(bool): If True, it will return as a GDALGrid object. Default is False.
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
        if as_gdal_grid:
            return GDALGrid(dst)
        else:
            # print(dst.GetRasterBand(1).ReadAsArray())
            return dst
    else:
        del dst
        return None


if __name__ == "__main__":
    # TODO: http://geoexamples.blogspot.com/2013/09/reading-wrf-netcdf-files-with-gdal.html

    # base_folder = 'C:/Users/RDCHLADS/Documents/scripts/gsshapy/tests/grid_standard'
    base_folder = '/home/rdchlads/scripts/gsshapy/tests/grid_standard'
    data_grid = path.join(base_folder, 'wrf_hmet_data','2016082322_Temp.asc')
    gssha_grid = path.join(base_folder, 'gssha_project', 'grid_standard.ele')
    gssha_prj_file = path.join(base_folder, 'gssha_project', 'grid_standard_prj.pro')
    out_grid = path.join(base_folder, 'test_resample.tif')
    match_ds = GSSHAGrid(gssha_grid, gssha_prj_file)
    # resample_grid(data_grid, match_ds, to_file=out_grid)
    # lat, lon = match_ds.lat_lon(two_dimensional=True)
    # print(match_ds.geotransform())
    # print(geotransform_from_latlon(lat, lon, proj=match_ds.proj()))

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
