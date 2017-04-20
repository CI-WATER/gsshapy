"""
********************************************************************************
* Name: ElevationGridFile
* Author: Alan D. Snow
* Created On: Feb. 10, 2017
* License: BSD 3-Clause
********************************************************************************
"""

__all__ = ['ElevationGridFile']

import os
from osgeo import gdalconst
from ..lib.grid_tools import resample_grid
from .map import RasterMapFile


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

    def generateFromRaster(self, elevation_raster,
                           out_elevation_grid=None,
                           resample_method=gdalconst.GRA_Average,
                           calculate_outlet_slope=True):
        '''
        Generates an elevation grid for the GSSHA simulation
        from an elevation raster

        Example::

            from gsshapy.orm import ProjectFile, ElevationGridFile
            from gsshapy.lib import db_tools as dbt

            from os import path, chdir

            gssha_directory = '/gsshapy/tests/grid_standard/gssha_project'
            elevation_raster = 'elevation.tif'

            # Create Test DB
            sqlalchemy_url, sql_engine = dbt.init_sqlite_memory()

            # Create DB Sessions
            db_session = dbt.create_session(sqlalchemy_url, sql_engine)

            # Instantiate GSSHAPY object for reading to database
            project_manager = ProjectFile()

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
        '''
        if not self.projectFile:
            raise ValueError("Must be connected to project file ...")

        # must match elevation mask grid
        mask_grid = self.projectFile.getGrid()
        if out_elevation_grid is None:
            project_path = ''
            project_path_card = self.projectFile.getCard('PROJECT_PATH')
            if project_path_card:
                project_path = project_path_card.value.strip('"').strip("'")
            out_elevation_grid = os.path.join(project_path,
                                              '{0}.{1}'.format(self.projectFile.name,
                                                               self.fileExtension),
                                              )

        elevation_grid = resample_grid(elevation_raster,
                                       mask_grid,
                                       resample_method=resample_method,
                                       as_gdal_grid=True)
        elevation_grid.to_grass_ascii(out_elevation_grid, print_nodata=False)

        self.filename = out_elevation_grid
        self.projectFile.setCard("ELEVATION", out_elevation_grid, add_quotes=True)
        # read raster into object
        self._load_raster_text(out_elevation_grid)
        if calculate_outlet_slope:
            self.projectFile.calculateOutletSlope(elevation_grid=elevation_grid,
                                                  mask_grid=mask_grid)
