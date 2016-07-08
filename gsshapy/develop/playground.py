'''
Created on Sep 20, 2013

@author: swainn
'''

from osgeo import gdal
from osgeo.gdalconst import *
import numpy

# Example reading file and converting using GDAL

# Register Driver
driver = gdal.GetDriverByName('GRASSASCIIGrid')
driver.Register()

# Open file into GDAL dataset
filename = '/Users/swainn/testing/test models/ParkCityBasic/combo.idx'
dataset = gdal.Open(filename, GA_ReadOnly)

# Dataset Properties
columns = dataset.RasterXSize
rows = dataset.RasterYSize
bands = dataset.RasterCount

# Get the georeference information from the image
geoTransform = dataset.GetGeoTransform()
originX = geoTransform[0]
originY = geoTransform[3]
pixelWidth = geoTransform[1]
pixelHeight = geoTransform[5]

# Get the band object using indexes (1-based)
band = dataset.GetRasterBand(1)

# Read entire array into 2D array
data = band.ReadAsArray(0, 0, columns, rows).astype(numpy.float)

# Set arrays to None when done
band = None
dataset = None

# Writing out to file

# For same driver as the input dataset, use dataset.GetDriver()
driver2 = dataset.GetDriver()

# Write the file 
outfile = '/Users/swainn/testing/out.idx'
outDataset = driver2.Create(outfile, columns, rows, 1)

# NOTE: there is no create method implemented for GRASS ASCII maps at the moment.
# We'll need to implment one.

# # Reproject Rasters Example
# import gdal, osr
# from gdalconst import *
# inFn = 'd:/data/classes/python/data/aster.img'
# outFn = 'd:/data/classes/python/data/aster_geo.img'
# driver = gdal.GetDriverByName('HFA')
# driver.Register()
# # input WKT
# inDs = gdal.Open(inFn)
# OS Python week 6: More raster processing [4]
# inWkt = inDs.GetProjection()
# # output WKT
# outSr = osr.SpatialReference()
# outSr.ImportFromEPSG(4326)
# outWkt = outSr.ExportToWkt()
# # reproject
# gdal.CreateAndReprojectImage(inDs, outFn, src_wkt=inWkt, 
# dst_wkt=outWkt, dst_driver=driver, 
# eResampleAlg=GRA_Bilinear)
# inDs = None