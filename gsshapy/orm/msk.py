"""
********************************************************************************
* Name: RaserMapModel
* Author: Nathan Swain
* Created On: August 1, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

__all__ = ['WatershedMaskFile']


from gridtogssha.grid_tools import rasterize_shapefile
import os

from .map import RasterMapFile


class WatershedMaskFile(RasterMapFile):
    """
    Object interface for generating a watershed mask.

    This object inherits the :class:`gsshapy.orm.RasterMapFile` base class.

    See: http://www.gsshawiki.com/Project_File:Project_File
    """

    def __init__(self):
        """
        Constructor
        """
        super(WatershedMaskFile, self).__init__()
        self.fileExtension = 'msk'

    def generateFromWatershedShapefile(self,
                                       shapefile_path,
                                       out_raster_path=None,
                                       x_num_cells=None,
                                       y_num_cells=None,
                                       x_cell_size=None,
                                       y_cell_size=None):
        '''
        Generates a mask from a watershed_shapefile
        '''
        match_grid = None
        wkt_projection = None
        if self.projectFile:
            try:
                match_grid = self.projectFile.getGrid()
            except ValueError:
                try:
                    wkt_projection = self.projectFile.getWkt()
                except ValueError:
                    pass
                pass

            if out_raster_path is None:
                project_path = ''
                project_path_card = self.projectFile.getCard('PROJECT_PATH')
                if project_path_card:
                    project_path = project_path_card.value.strip('"').strip("'")
                out_raster_path = os.path.join(project_path,
                                               '{0}.{1}'.format(self.projectFile.name,
                                                                self.extension),
                                                )
        elif out_raster_path is None:
            raise ValueError("If watershed mask is not assiciated with a "
                             "project file, out_raster_path must be set ...")

        gr = rasterize_shapefile(shapefile_path,
                                 x_num_cells=x_num_cells,
                                 y_num_cells=y_num_cells,
                                 x_cell_size=x_cell_size,
                                 y_cell_size=y_cell_size,
                                 match_grid=match_grid,
                                 raster_nodata=0,
                                 as_gdal_grid=True,
                                 raster_wkt_proj=wkt_projection,
                                 convert_to_utm=True
                                 )
        gr.to_grass_ascii(out_raster_path, print_nodata=False)

        self.filename = out_raster_path
