"""
********************************************************************************
* Name: ElevationGridFile
* Author: Alan D. Snow
* Created On: Feb. 10, 2017
* License: BSD 3-Clause
********************************************************************************
"""
from __future__ import unicode_literals

__all__ = ['ElevationGridFile']

import os

from osgeo import gdalconst
from gazar.grid import resample_grid

from .map import RasterMapFile
from ..util.context import tmp_chdir

class ElevationGridFile(RasterMapFile):
    """
    Object interface for generating an elevation grid.

    This object inherits the :class:`gsshapy.orm.RasterMapFile` base class.

    See: http://www.gsshawiki.com/Project_File:Project_File
    """

    def __init__(self, session=None, project_file=None):
        """
        Constructor
        """
        super(ElevationGridFile, self).__init__()
        self.fileExtension = 'ele'
        if session is not None and project_file is not None:
            # delete existing instances
            self._delete_existing(project_file, session)
        # add to project_file
        self.projectFile = project_file

    def generateFromRaster(self,
                           elevation_raster,
                           shapefile_path=None,
                           out_elevation_grid=None,
                           resample_method=gdalconst.GRA_Average,
                           load_raster_to_db=True):
        """
        Generates an elevation grid for the GSSHA simulation
        from an elevation raster

        Example::

            from gsshapy.orm import ProjectFile, ElevationGridFile
            from gsshapy.lib import db_tools as dbt


            gssha_directory = '/gsshapy/tests/grid_standard/gssha_project'
            elevation_raster = 'elevation.tif'

            project_manager, db_sessionmaker = \
                dbt.get_project_session('grid_standard',
                                        gssha_directory)

            db_session = db_sessionmaker()

            # read project file
            project_manager.readInput(directory=gssha_directory,
                                      projectFileName='grid_standard.prj',
                                      session=db_session)

            # generate elevation grid
            elevation_grid = ElevationGridFile(session=db_session,
                                               project_file=project_manager)
            elevation_grid.generateFromRaster(elevation_raster)

            # write out updated parameters
            project_manager.writeInput(session=db_session,
                                       directory=gssha_directory,
                                       name='grid_standard')
        """
        if not self.projectFile:
            raise ValueError("Must be connected to project file ...")

        # make sure paths are absolute as the working directory changes
        elevation_raster = os.path.abspath(elevation_raster)
        shapefile_path = os.path.abspath(shapefile_path)

        # must match elevation mask grid
        mask_grid = self.projectFile.getGrid()
        if out_elevation_grid is None:
            out_elevation_grid = '{0}.{1}'.format(self.projectFile.name,
                                                  self.fileExtension)

        elevation_grid = resample_grid(elevation_raster,
                                       mask_grid,
                                       resample_method=resample_method,
                                       as_gdal_grid=True)

        with tmp_chdir(self.projectFile.project_directory):
            elevation_grid.to_grass_ascii(out_elevation_grid, print_nodata=False)

            # read raster into object
            if load_raster_to_db:
                self._load_raster_text(out_elevation_grid)

        self.filename = out_elevation_grid
        self.projectFile.setCard("ELEVATION", out_elevation_grid, add_quotes=True)

        # find outlet and add slope
        self.projectFile.findOutlet(shapefile_path)
