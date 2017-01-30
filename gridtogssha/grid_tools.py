from osgeo import gdal, gdalconst
from os import path

def gdal_memory_grid_from_nparray(in_array,
                                  x_min,
                                  x_size,
                                  y_max,
                                  y_size,
                                  wkt_projection,
                                  name="tmp_ras",
                                  gdal_dtype=gdalconst.GDT_Float32):
    '''
    Creates a gdal in memory raster from nparray
    '''
    dataset = gdal.GetDriverByName('MEM').Create(name,
                                                 in_array.shape[0],
                                                 in_array.shape[1],
                                                 1,
                                                 gdal_dtype,
                                                 )

    dataset.SetGeoTransform((x_min, x_size, 0, y_max, 0, -y_size))
    dataset.SetProjection(wkt_projection)
    dataset.GetRasterBand(1).WriteArray(array)
    return dataset

def gdal_from_gssha(gssha_ele_grid, gssha_prj_file):
    '''
    Creates a gdal in memory raster from gssha grid
    '''
    gssha_grid = gdal.Open(gssha_ele_grid, gdalconst.GA_ReadOnly)
    with open(gssha_prj_file) as pro_file:
        gssha_grid.SetProjection(pro_file.read())
    return gssha_grid

def resample_grid(original_grid, match_grid, to_file=False, output_datatype=None):
    '''
    This function resamples a grid and outputs the result to a file

    original_grid (str|gdal.Dataset): If str, reads in path, otherwise assumes gdal.Dataset.
    match_grid (str|gdal.Dataset): If str, reads in path, otherwise assumes gdal.Dataset.
    to_file (str|bool): If False, returns in memory grid. If str, writes to file.
    output_datatype (gdalconst): A valid datatype from gdalconst (ex. gdalconst.GDT_Float32).
    '''
    # http://stackoverflow.com/questions/10454316/how-to-project-and-resample-a-grid-to-match-another-grid-with-gdal-python

    # Source of the data
    if not isinstance(original_grid, gdal.Dataset):
        src = gdal.Open(original_grid, gdalconst.GA_ReadOnly)
    else:
        src = original_grid

    src_proj = src.GetProjection()
    src_geotrans = src.GetGeoTransform()

    # ensure output datatype is set
    if output_datatype is None:
        output_datatype = src.GetRasterBand(1).DataType

    # Grid to use to extract subset and match
    if not isinstance(match_grid, gdal.Dataset):
        match_ds = gdal.Open(match_grid, gdalconst.GA_ReadOnly)
    else:
        match_ds = match_grid

    match_geotrans = match_ds.GetGeoTransform()
    match_proj = match_ds.GetProjection()

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
                        gdalconst.GRA_Average)
    # if not isinstance(dst, gdal.Dataset):
    print(dst.GetRasterBand(1).ReadAsArray())

    if not to_file:
        return dst
    else:
        del dst
        return None

# TODO: http://geoexamples.blogspot.com/2013/09/reading-wrf-netcdf-files-with-gdal.html

# base_folder = 'C:/Users/RDCHLADS/Documents/scripts/gsshapy/tests/grid_standard'
base_folder = '/home/rdchlads/scripts/gsshapy/tests/grid_standard'
data_grid = path.join(base_folder, 'hrrr_hmet_data','2016091407_Pres.asc')
gssha_grid = path.join(base_folder, 'gssha_project', 'grid_standard.ele')
gssha_prj_file = path.join(base_folder, 'gssha_project', 'grid_standard_prj.pro')
out_grid = path.join(base_folder, 'test_resample.tif')
match_ds = gdal_from_gssha(gssha_grid, gssha_prj_file)
resample_grid(data_grid, match_ds)

"""
# https://mapbox.github.io/rasterio/topics/resampling.html
# https://mapbox.s3.amazonaws.com/playground/perrygeo/rasterio-docs/cookbook.html

from gdal import osr
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.crs import CRS

with open(gssha_projection_file) as pro_file:
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

        print(profile)
        # Reproject and write each band
        with rasterio.open(out_grid, 'w', **profile) as dst:
            print(dst)
            for i in range(1, src.count + 1):
                print(i)
                src_array = src.read(i)
                dst_array = np.empty((grd.height, grd.width), dtype=src_array.dtype)
                print(src_array.dtype)
                reproject(
                    # Source parameters
                    source=src_array,
                    # src_crs=src.crs,
                    src_crs=dst_crs,
                    src_transform=src.transform,
                    # Destination paramaters
                    destination=dst_array,
                    dst_transform=grd.transform,
                    dst_crs=dst_crs,
                    # Configuration
                    resampling=Resampling.bilinear,
                    num_threads=1,
                    )
                print(dst_array)

                dst.write(dst_array, i)


"""
