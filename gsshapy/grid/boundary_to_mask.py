from grid_tools import rasterize_shapefile

shapefile_path = '/home/rdchlads/scripts/gsshapy/tests/grid_standard/phillipines/phillipines_5070115700.shp'
mask_grid = '/home/rdchlads/scripts/gsshapy/tests/grid_standard/grid_51N.msk'
mask_ascii_grid = '/home/rdchlads/scripts/gsshapy/tests/grid_standard/grid_ascii.msk'
wkt = 'PROJCS["WGS 84 / UTM zone 51N",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],UNIT["metre",1,AUTHORITY["EPSG","9001"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",123],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],AUTHORITY["EPSG","32651"],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'
gr = rasterize_shapefile(shapefile_path,
                         #mask_grid,
                         x_num_cells=100,
                         y_num_cells=100,
                         raster_nodata=0,
                         as_gdal_grid=True,
                         #raster_wkt_proj=wkt,
                         convert_to_utm=True
                         )
gr.to_grass_ascii(mask_ascii_grid, print_nodata=False)
