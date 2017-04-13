from affine import Affine
import math
import numpy as np
from osgeo import osr
import pandas as pd
from pyproj import Proj, transform
import xarray as xr

from grid_tools import (geotransform_from_latlon, gdal_reproject,
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
        self.y_dim = 'lat'
        self.x_dim = 'lon'
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

    def _load_wrf_projection(self):
        """Get the osgeo.osr projection for WRF Grid."""
        map_proj = self._obj.attrs.get('MAP_PROJ')
        standard_parallel_1 = self._obj.attrs.get('TRUELAT1')
        standard_parallel_2 = self._obj.attrs.get('TRUELAT2')
        central_meridian = self._obj.attrs.get('STAND_LON')
        latitude_of_origin = self._obj.attrs.get('CEN_LAT')
        # WRF GRID
        # BASED ON: https://github.com/Esri/python-toolbox-for-rapid/blob/master/toolbox/scripts/CreateWeightTableFromWRFGeogrid.py
        if map_proj == 1:
            # Lambert Conformal Conic
            if standard_parallel_2 is not None:
                print('    Using Standard Parallel 2 in Lambert Conformal Conic map projection.')
                #http://www.remotesensing.org/geotiff/proj_list/lambert_conic_conformal_2sp.html
            else:
                # According to http://webhelp.esri.com/arcgisdesktop/9.2/index.cfm?TopicName=Lambert_Conformal_Conic
                #http://www.remotesensing.org/geotiff/proj_list/lambert_conic_conformal_1sp.html
                standard_parallel_2 = standard_parallel_1
                latitude_of_origin = standard_parallel_1

            Projection_String = ('PROJCS["North_America_Lambert_Conformal_Conic",'
                                 'GEOGCS["GCS_Sphere",'
                                 'DATUM["D_Sphere",SPHEROID["Sphere",6370000.0,0.0]],'
                                 'PRIMEM["Greenwich",0.0],'
                                 'UNIT["Degree",0.0174532925199433]],'
                                 'PROJECTION["Lambert_Conformal_Conic"],'
                                 'PARAMETER["false_easting",0.0],'
                                 'PARAMETER["false_northing",0.0],'
                                 'PARAMETER["central_meridian",{central_meridian}],'
                                 'PARAMETER["standard_parallel_1",{standard_parallel_1}],'
                                 'PARAMETER["standard_parallel_2",{standard_parallel_2}],'
                                 'PARAMETER["latitude_of_origin",{latitude_of_origin}],'
                                 'UNIT["Meter",1.0]]') \
                                 .format(central_meridian=central_meridian,
                                         standard_parallel_1=standard_parallel_1,
                                         standard_parallel_2=standard_parallel_2,
                                         latitude_of_origin=latitude_of_origin)

        elif map_proj == 2:
            # Polar Stereographic

            # Set up pole latitude
            phi1 = float(standard_parallel_1)

            ### Back out the central_scale_factor (minimum scale factor?) using
            # formula below using Snyder 1987 p.157 (USGS Paper 1395)
            ## phi = math.copysign(float(pole_latitude), float(latitude_of_origin))
            #  Get the sign right for the pole using sign of CEN_LAT (latitude_of_origin)
            ## central_scale_factor = (1 + (math.sin(math.radians(phi1))*math.sin(math.radians(phi))) +
            # (math.cos(math.radians(float(phi1)))*math.cos(math.radians(phi))))/2

            # Method where central scale factor is k0, Derivation from C. Rollins 2011,
            # equation 1: http://earth-info.nga.mil/GandG/coordsys/polar_stereographic/Polar_Stereo_phi1_from_k0_memo.pdf
            # Using Rollins 2011 to perform central scale factor calculations.
            # For a sphere, the equation collapses to be much  more compact (e=0, k90=1)

            central_scale_factor = (1 + math.sin(math.radians(abs(phi1))))/2
            # Equation for k0, assumes k90 = 1, e=0. This is a sphere, so no flattening

            print('      Central Scale Factor: {0}'.format(central_scale_factor))
            Projection_String = ('PROJCS["Sphere_Stereographic",'
                                 'GEOGCS["GCS_Sphere",'
                                 'DATUM["D_Sphere",'
                                 'SPHEROID["Sphere",6370000.0,0.0]],'
                                 'PRIMEM["Greenwich",0.0],'
                                 'UNIT["Degree",0.0174532925199433]],'
                                 'PROJECTION["Stereographic"],'
                                 'PARAMETER["False_Easting",0.0],'
                                 'PARAMETER["False_Northing",0.0],'
                                 'PARAMETER["Central_Meridian",{central_meridian}],'
                                 'PARAMETER["Scale_Factor",{central_scale_factor}],'
                                 'PARAMETER["Latitude_Of_Origin",{standard_parallel_1}],'
                                 'UNIT["Meter",1.0]]') \
                                 .format(central_meridian=central_meridian,
                                         central_scale_factor=central_scale_factor,
                                         standard_parallel_1=standard_parallel_1)

        elif map_proj == 3:
            # Mercator Projection
            Projection_String = ('PROJCS["Sphere_Mercator",'
                                 'GEOGCS["GCS_Sphere",'
                                 'DATUM["D_Sphere",'
                                 'SPHEROID["Sphere",6370000.0,0.0]],'
                                 'PRIMEM["Greenwich",0.0],'
                                 'UNIT["Degree",0.0174532925199433]],'
                                 'PROJECTION["Mercator"],'
                                 'PARAMETER["False_Easting",0.0],'
                                 'PARAMETER["False_Northing",0.0],'
                                 'PARAMETER["Central_Meridian",{central_meridian}],'
                                 'PARAMETER["Standard_Parallel_1",{standard_parallel_1}],'
                                 'UNIT["Meter",1.0],AUTHORITY["ESRI",53004]]') \
                                 .format(central_meridian=central_meridian,
                                         standard_parallel_1=standard_parallel_1)

        elif map_proj == 6:
            # Cylindrical Equidistant (or Rotated Pole)
            # Check units (linear unit not used in this projection).  GCS?
            Projection_String = ('PROJCS["Sphere_Equidistant_Cylindrical",'
                                 'GEOGCS["GCS_Sphere",'
                                 'DATUM["D_Sphere",'
                                 'SPHEROID["Sphere",6370000.0,0.0]],'
                                 'PRIMEM["Greenwich",0.0],'
                                 'UNIT["Degree",0.0174532925199433]],'
                                 'PROJECTION["Equidistant_Cylindrical"],'
                                 'PARAMETER["False_Easting",0.0],'
                                 'PARAMETER["False_Northing",0.0],'
                                 'PARAMETER["Central_Meridian",{central_meridian}],'
                                 'PARAMETER["Standard_Parallel_1",{standard_parallel_1}],'
                                 'UNIT["Meter",1.0],AUTHORITY["ESRI",53002]]') \
                                 .format(central_meridian=central_meridian,
                                         standard_parallel_1=standard_parallel_1)

        self._projection = osr.SpatialReference()
        self._projection.ImportFromESRI([Projection_String])
        # make sure EPSG code identified
        self._projection.AutoIdentifyEPSG()

    @property
    def projection(self):
        """Get the osgeo.osr projection for the dataset."""
        if self._projection is None:
            # read projection information from global attributes
            map_proj = self._obj.attrs.get('MAP_PROJ')
            if map_proj is None:
                # default to EPSG 4326
                self._projection = osr.SpatialReference()
                self._projection.ImportFromEPSG(4326)
            else:
                self._load_wrf_projection()

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
            if str(self.epsg) != '4326':
                # BASED ON: https://github.com/Esri/python-toolbox-for-rapid/blob/master/toolbox/scripts/CreateWeightTableFromWRFGeogrid.py
                corner_lats = self._obj.attrs.get('corner_lats')
                corner_lons = self._obj.attrs.get('corner_lons')
                dx = self._obj.attrs.get('DX')
                dy = self._obj.attrs.get('DY')
                if None not in (dx, dy) \
                        and not hasattr(corner_lats, '__len__') \
                        and hasattr(corner_lons, '__len__'):
                    # Create a point geometry object from gathered corner point data
                    pt_proj = osr.SpatialReference()
                    # from http://www.emep.int/mscw/Grid/emep_grid.html
                    pt_proj.ImportFromProj4('proj +ellps=sphere +a=127.4 +e=0 '
                                            '+proj=stere +lat_0=90 +lon_0=-32 '
                                            '+lat_ts=60 +x_0=8 +y_0=110')
                    # pt_proj.ImportFromEPSG(104128) # Using EMEP Sphere (6370000m)

                    # get projected top/left corner
                    tx = osr.CoordinateTransformation(pt_proj, self.projection)
                    x_min_proj, y_max_proj, z =  tx.TransformPoint(float(corner_lons[0]),
                                                                   float(corner_lats[1]))

                    self._geotransform = (x_min_proj, float(dx), 0,
                                          y_max_proj, 0, -float(dy))
                else:
                    lons = self._obj[self.x_var]
                    lats = self._obj[self.y_var]
                    proj_lon, proj_lat = transform(Proj(init='epsg:4326'),
                                                   Proj(self.projection.ExportToProj4()),
                                                   self._obj[self.x_var][0].values,
                                                   self._obj[self.y_var][0].values,
                                                   )

                    self._geotransform = geotransform_from_latlon(proj_lat,
                                                                  proj_lon)

            else:
                self._geotransform = geotransform_from_latlon(self._obj[self.y_var],
                                                              self._obj[self.x_var])

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

    def coords(self, as_2d=False):
        """Returns x, y coordinate lists"""
        x_size = self._obj.dims[self.x_dim]
        y_size = self._obj.dims[self.y_dim]
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
            lon = self._obj[self.x_var]
            lat = self._obj[self.y_var]
            self._center = (float(lon.mean()), float(lat.mean()))
        return self._center

    def subset_geotransform(self, x_index_start, y_index_start):
        """Get the osgeo geotransform for grid subset"""
        x_min, dx, x_skew, y_max, y_skew, dy = self.geotransform
        new_x_min = x_min + dx*x_index_start
        new_y_max = y_max + dy*y_index_start
        return (new_x_min, dx, x_skew, new_y_max, y_skew, dy)

    def _export_dataset(self, variable, new_data, grid, geotransform):
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
                                   'wkt': grid.wkt,
                                   'geotransform': str(geotransform)}
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
                                    resampled_data_grid, self.geotransform)


    def to_utm(self, variable,
               x_index_start=0, x_index_end=-1,
               y_index_start=0, y_index_end=-1,
               calc_4d_method=None,
               calc_4d_dim=None):
        """Convert Grid to UTM Coordinates"""
        # get utm projection
        center_lon, center_lat = self.center
        utm_proj = utm_proj_from_latlon(center_lat, center_lon, as_osr=True)
        geotransform = self.subset_geotransform(x_index_start, y_index_start)
        new_data = []
        for band in range(self._obj.dims[self.time_dim]):
            if len(self._obj[variable].dims) == 4:
                if calc_4d_method is None or calc_4d_dim is None:
                    raise ValueError("The variable {var} has 4 dimension. "
                                     "Need 'calc_4d_method' and 'calc_4d_dim' "
                                     "to proceed ...".format(var=data_var))
                data = self._obj[variable][band,:,
                                           y_index_start:y_index_end,
                                           x_index_start:x_index_end,
                                           ]
                data = getattr(data, calc_4d_method)(dim=calc_4d_dim).values
            else:
                data = self._obj[variable][band,
                                           y_index_start:y_index_end,
                                           x_index_start:x_index_end,
                                           ].values
            arr_grid = ArrayGrid(in_array=data,
                                 wkt_projection=self.projection.ExportToWkt(),
                                 geotransform=geotransform,
                                 )
            gdal_ds = gdal_reproject(arr_grid.dataset,
                                     dst_srs=utm_proj)
            new_data.append(np.array(gdal_ds.ReadAsArray()))

        self.to_datetime()
        ggrid = GDALGrid(gdal_ds)
        return self._export_dataset(variable, np.array(new_data),
                                    ggrid, geotransform)


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import numpy as np
    # path to files
    path_to_files = '/home/rdchlads/scripts/gsshapy/tests/grid_standard/wrf_raw_data/gssha_d03_nc/*.nc'
    with xr.open_mfdataset(path_to_files, concat_dim='Time') as xd:
        xd.lsm.y_var = "XLAT"
        xd.lsm.x_var = "XLONG"
        xd.lsm.time_var = "Times"
        xd.lsm.y_dim = "south_north"
        xd.lsm.x_dim = "west_east"
        xd.lsm.time_dim = "Time"
        print(xd.lsm.geotransform)
        """
        u10_ds = xd.lsm.to_utm("U10",
                               x_index_start=5, x_index_end=7,
                               y_index_start=25, y_index_end=77,
                              )
        v10_ds = xd.lsm.to_utm("V10",
                               x_index_start=5, x_index_end=7,
                               y_index_start=25, y_index_end=77,
                              )
        data = u10_ds["U10"]+v10_ds["V10"]
        data = data.to_dataset(name="velocity")
        data = data.resample('3H', dim='time', how='mean')

        resampled_data = data.resample('1H', dim='time')
        print(data.dims['time'])
        for time_idx in range(data.dims['time']):
            if time_idx+1 < data.dims['time']:
                # interpolate between time steps
                start_time = data.time[time_idx].values
                end_time = data.time[time_idx+1].values
                slope_timeslice = slice(str(start_time), str(end_time))
                slice_size = resampled_data.sel(time=slope_timeslice).dims['time'] - 1
                first_timestep = resampled_data.sel(time=str(start_time)).velocity
                slope = (resampled_data.sel(time=str(end_time)).velocity
                         - first_timestep)/float(slice_size)
                data_timeslice = slice(str(start_time+np.timedelta64(1,'m')),
                                        str(end_time-np.timedelta64(1,'m')))
                data_subset = resampled_data.sel(time=data_timeslice)
                for xidx in range(data_subset.dims['time']):
                    resampled_data.sel(time=data_timeslice).velocity[xidx] = first_timestep + slope * (xidx+1)
        print(resampled_data.velocity[1])
        #for row in data['velocity']:
        #    print(row.values.ravel().astype(str))
        """
