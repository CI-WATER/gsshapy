from affine import Affine
import math
import numpy as np
from osgeo import osr, gdalconst
import pandas as pd
from pyproj import Proj, transform
import wrf
import xarray as xr

from ..lib.grid_tools import (geotransform_from_latlon, gdal_reproject,
                              resample_grid, utm_proj_from_latlon,
                              ArrayGrid, GDALGrid)

@xr.register_dataset_accessor('lsm')
class LSMGridReader(object):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj
        self._projection = None
        self._epsg = None
        self._geotransform = None
        self._affine = None
        self._center = None

        # set variable information
        self.y_var = 'lat'
        self.x_var = 'lon'
        self.time_var = 'time'
        # set dimension information
        self.y_dim = 'y'
        self.x_dim = 'x'
        self.time_dim = 'time'


    def to_datetime(self):
        """Converts time to datetime."""
        time_values = self._obj[self.time_var].values
        if 'datetime' not in str(time_values.dtype):
            try:
                self._obj[self.time_var].values = pd.to_datetime(time_values)
            except ValueError:
                # ONE POTENTIAL WRF FORMAT
                self._obj[self.time_var].values = pd.to_datetime(time_values,
                                                                 format="%Y-%m-%d_%H:%M:%S")
    @property
    def datetime(self):
        """Get datetime object for time index"""
        self.to_datetime()
        return pd.to_datetime(self._obj[self.time_var].values)

    def _load_wrf_projection(self):
        """Get the osgeo.osr projection for WRF Grid.

        - 'MAP_PROJ': The map projection type as an integer.
        - 'TRUELAT1': True latitude 1.
        - 'TRUELAT2': True latitude 2.
        - 'MOAD_CEN_LAT': Mother of all domains center latitude.
        - 'STAND_LON': Standard longitude.
        - 'POLE_LAT': Pole latitude.
        - 'POLE_LON': Pole longitude.
        """
        # load in params from WRF Global Attributes
        possible_proj_params = ('MAP_PROJ', 'TRUELAT1', 'TRUELAT2',
                                'MOAD_CEN_LAT', 'STAND_LON', 'POLE_LAT',
                                'POLE_LON')
        proj_params = dict()
        for proj_param in possible_proj_params:
            if proj_param in self._obj.attrs:
                proj_params[proj_param] = self._obj.attrs[proj_param]

        # determine projection from WRF Grid
        proj = wrf.projection.getproj(**proj_params)

        # export to Proj4 and add as osr projection
        self._projection = osr.SpatialReference()
        self._projection.ImportFromProj4(str(proj.proj4()))

    @property
    def projection(self):
        """Get the osgeo.osr projection for the dataset."""
        if self._projection is None:
            # read projection information from global attributes
            map_proj4 = self._obj.attrs.get('proj4')
            map_proj = self._obj.attrs.get('MAP_PROJ')
            if map_proj4 is not None:
                self._projection = osr.SpatialReference()
                self._projection.ImportFromProj4(map_proj4)
            elif 'MAP_PROJ' in self._obj.attrs:
                self._load_wrf_projection()
            else:
                # default to EPSG 4326
                self._projection = osr.SpatialReference()
                self._projection.ImportFromEPSG(4326)
        return self._projection

    @property
    def epsg(self):
        """EPSG code"""
        if self._epsg is None:
            self._epsg = self.projection.GetAuthorityCode(None)
        return self._epsg

    @property
    def dx(self):
        return self.geotransform[1]

    @property
    def dy(self):
        return -self.geotransform[-1]

    @property
    def geotransform(self):
        """Get the osgeo geotransform for grid"""
        if self._geotransform is None:
            if self._obj.attrs.get('geotransform') is not None:
                self._geotransform = [float(g) for g in self._obj.attrs.get('geotransform')]

            elif str(self.epsg) != '4326':
                proj_y, proj_x = self.coords()
                self._geotransform = geotransform_from_latlon(proj_y,
                                                              proj_x)
            else:
                self._geotransform = geotransform_from_latlon(*self.latlon)

        return self._geotransform

    @property
    def affine(self):
        """Gets the affine for the transformation"""
        if self._affine is None:
            self._affine = Affine.from_gdal(*self.geotransform)
        return self._affine

    def pixel2coord(self, col, row):
        """Returns global coordinates to pixel center using base-0 raster index
           http://gis.stackexchange.com/questions/53617/how-to-find-lat-lon-values-for-every-pixel-in-a-geotiff-file
        """
        return self.affine * (col+0.5, row+0.5)

    @property
    def x_size(self):
        return self._obj.dims[self.x_dim]

    @property
    def y_size(self):
        return self._obj.dims[self.y_dim]

    @property
    def latlon(self):
        """Returns lat,lon"""
        if 'MAP_PROJ' in self._obj.attrs:
            lat, lon = wrf.latlon_coords(self._obj, as_np=True)
            # WRF Grid is upside down
            lat = lat[0, ::-1]
            lon = lon[0, ::-1]
        else:
            lon = self._obj[self.x_var].values
            lat = self._obj[self.y_var].values

        if lat.ndim == 3:
            lat = lat[0]
        if lon.ndim == 3:
            lon = lon[0]

        return lat, lon

    def coords(self, as_2d=False):
        """Returns x, y coordinate lists"""
        try:
            y_coords, x_coords = self.latlon
            proj_x, proj_y = transform(Proj(init='epsg:4326'),
                                       Proj(self.projection.ExportToProj4()),
                                       x_coords,
                                       y_coords,
                                       )
            return proj_y, proj_x
        except KeyError:
            pass

        x_size = self.x_size
        y_size = self.y_size
        x_2d_coords = np.zeros((y_size, x_size))
        y_2d_coords = np.zeros((y_size, x_size))

        for x in range(x_size):
            for y in range(y_size):
                x_2d_coords[y, x], y_2d_coords[y, x] = self.pixel2coord(x,y)

        if not as_2d:
            return y_coords.mean(axis=1), x_2d_coords.mean(axis=0)

        return y_2d_coords, x_2d_coords

    @property
    def center(self):
        """Return the geographic center point of this dataset."""
        if self._center is None:
            # we can use a cache on our accessor objects, because accessors
            # themselves are cached on instances that access them.
            lat, lon = self.latlon
            self._center = (float(lon.mean()), float(lat.mean()))
        return self._center

    def _export_dataset(self, variable, new_data, grid):
        """Export subset of dataset."""
        lats, lons = grid.lat_lon(two_dimensional=True)
        return xr.Dataset({variable: (['time', 'y', 'x'],
                                      new_data,
                                      self._obj[variable].attrs),
                           },
                           coords={'lat': (['y', 'x'],
                                            lats,
                                            self._obj[variable].coords[self.y_var].attrs
                                            ),
                                    'lon': (['y', 'x'],
                                            lons,
                                            self._obj[variable].coords[self.x_var].attrs
                                            ),
                                    'time': (['time'],
                                             self._obj[self.time_var].values,
                                             self._obj[self.time_var].attrs,
                                             ),
                            },
                            attrs={'proj4': grid.proj4,
                                   'geotransform': grid.geotransform,
                            }
                        )

    def resample(self, variable, match_grid):
        """Resample data to grid."""
        new_data = []
        for band in range(self._obj.dims[self.time_dim]):
            data = self._obj[variable][band].values
            arr_grid = ArrayGrid(in_array=data,
                                 wkt_projection=self.projection.ExportToWkt(),
                                 geotransform=self.geotransform,
                                 )
            resampled_data_grid = resample_grid(original_grid=arr_grid,
                                                match_grid=match_grid,
                                                as_gdal_grid=True)
            new_data.append(resampled_data_grid.np_array())

        self.to_datetime()
        return self._export_dataset(variable, np.array(new_data),
                                    resampled_data_grid)


    def get_subset(self, variable,
                   x_index_start=0,
                   x_index_end=-1,
                   y_index_start=0,
                   y_index_end=-1,
                   calc_4d_method=None,
                   calc_4d_dim=None):
        """Get Subset of variable"""
        if 'MAP_PROJ' in self._obj.attrs:
            # WRF Y DIM IS BACKWARDS
            original_y_index_start = y_index_start
            y_index_start = self.y_size - y_index_end - 1
            y_index_end = self.y_size - original_y_index_start - 1

        if len(self._obj[variable].dims) == 4:
            if calc_4d_method is None or calc_4d_dim is None:
                raise ValueError("The variable {var} has 4 dimension. "
                                 "Need 'calc_4d_method' and 'calc_4d_dim' "
                                 "to proceed ...".format(var=data_var))
            data = self._obj[variable][:,:,
                                       y_index_start:y_index_end,
                                       x_index_start:x_index_end,
                                       ]
            data = getattr(data, calc_4d_method)(dim=calc_4d_dim)
        else:
            data = self._obj[variable][:,
                                       y_index_start:y_index_end,
                                       x_index_start:x_index_end,
                                      ]

        if 'MAP_PROJ' in self._obj.attrs:
            # WRF Y DIM IS BACKWARDS
            data = data[:,::-1]

        data[self.time_var] = self._obj[self.time_var]

        return data

    def to_utm(self, variable):
        """Convert Grid to UTM Coordinates"""
        # get utm projection
        center_lon, center_lat = self.center
        utm_proj = utm_proj_from_latlon(center_lat, center_lon, as_osr=True)
        new_data = []
        for band in range(self._obj.dims[self.time_dim]):
            arr_grid = ArrayGrid(in_array=self._obj[variable][band].values,
                                 wkt_projection=self.projection.ExportToWkt(),
                                 geotransform=self.geotransform,
                                 )
            ggrid = gdal_reproject(arr_grid.dataset,
                                   src_srs=self.projection,
                                   dst_srs=utm_proj,
                                   resampling=gdalconst.GRA_Average,
                                   as_gdal_grid=True)
            new_data.append(ggrid.np_array())

        self.to_datetime()
        return self._export_dataset(variable, np.array(new_data),
                                    ggrid)

    def to_tif(self, variable, time_index, out_path):
        """Dump to TIFF"""
        arr_grid = ArrayGrid(in_array=self._obj[variable][time_index].values,
                             wkt_projection=self.projection.ExportToWkt(),
                             geotransform=self.geotransform,
                             )
        arr_grid.to_tif(out_path)

if __name__ == "__main__":
    # path to files
    path_to_files = '/home/rdchlads/scripts/gsshapy/tests/grid_standard/wrf_raw_data/gssha_d03_nc/*.nc'
    with xr.open_mfdataset(path_to_files, concat_dim='Time') as xd:
        #xd.lsm.y_var = "XLAT"
        #xd.lsm.x_var = "XLONG"
        xd.lsm.time_var = "Times"
        xd.lsm.y_dim = "south_north"
        xd.lsm.x_dim = "west_east"
        xd.lsm.time_dim = "Time"
        xd.lsm.to_tif("U10", 10)
