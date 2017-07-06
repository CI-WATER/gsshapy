"""
********************************************************************************
* Name: WatershedMaskFile
* Author: Alan D. Snow
* Created On: Feb. 9, 2017
* License: BSD 3-Clause
********************************************************************************
"""
from __future__ import unicode_literals

__all__ = ['WatershedMaskFile']

import os

from gazar.shape import rasterize_shapefile

from .map import RasterMapFile
from .pro import ProjectionFile
from ..util.context import tmp_chdir


class WatershedMaskFile(RasterMapFile):
    """
    Object interface for generating a watershed mask.

    This object inherits the :class:`gsshapy.orm.RasterMapFile` base class.

    See: http://www.gsshawiki.com/Project_File:Project_File
    """

    def __init__(self, session=None, project_file=None):
        """
        Constructor
        """
        super(WatershedMaskFile, self).__init__()
        self.fileExtension = 'msk'
        if session is not None and project_file is not None:
            # delete existing instances
            self._delete_existing(project_file, session)
        # add to project_file
        self.projectFile = project_file
        self.session = session

    def generateFromWatershedShapefile(self,
                                       shapefile_path,
                                       cell_size,
                                       out_raster_path=None,
                                       load_raster_to_db=True):
        """
        Generates a mask from a watershed_shapefile

        Example::

            from gsshapy.orm import ProjectFile, WatershedMaskFile
            from gsshapy.lib import db_tools as dbt


            gssha_directory = '/gsshapy/tests/grid_standard/gssha_project'
            shapefile_path = 'watershed_boundary.shp'

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

            # generate watershed mask
            watershed_mask = WatershedMaskFile(session=db_session,
                                               project_file=project_manager)
            watershed_mask.generateFromWatershedShapefile(shapefile_path,
                                                          x_num_cells=50,
                                                          y_num_cells=50,
                                                          )
            # write out updated parameters
            project_manager.writeInput(session=db_session,
                                       directory=gssha_directory,
                                       name='grid_standard')
        """
        if not self.projectFile:
            raise ValueError("Must be connected to project file ...")

        # match elevation grid if exists
        match_grid = None
        try:
            match_grid = self.projectFile.getGrid(use_mask=False)
        except ValueError:
            pass

        # match projection if exists
        wkt_projection = None
        try:
            wkt_projection = self.projectFile.getWkt()
        except ValueError:
            pass

        if out_raster_path is None:
            out_raster_path = '{0}.{1}'.format(self.projectFile.name, self.extension)

        # make sure paths are absolute as the working directory changes
        shapefile_path = os.path.abspath(shapefile_path)

        gr = rasterize_shapefile(shapefile_path,
                                 x_cell_size=cell_size,
                                 y_cell_size=cell_size,
                                 match_grid=match_grid,
                                 raster_nodata=0,
                                 as_gdal_grid=True,
                                 raster_wkt_proj=wkt_projection,
                                 convert_to_utm=True)

        with tmp_chdir(self.projectFile.project_directory):
            gr.to_grass_ascii(out_raster_path, print_nodata=False)
            self.filename = out_raster_path

            # update project file cards
            self.projectFile.setCard('WATERSHED_MASK', out_raster_path, add_quotes=True)
            self.projectFile.setCard('GRIDSIZE', str((gr.geotransform[1] - gr.geotransform[-1])/2.0))
            self.projectFile.setCard('ROWS', str(gr.y_size))
            self.projectFile.setCard('COLS', str(gr.x_size))

            # write projection file if does not exist
            if wkt_projection is None:
                proj_file = ProjectionFile()
                proj_file.projection = gr.wkt
                proj_file.projectFile = self.projectFile
                proj_path = "{0}_prj.pro".format(os.path.splitext(out_raster_path)[0])
                gr.write_prj(proj_path)
                self.projectFile.setCard('#PROJECTION_FILE', proj_path, add_quotes=True)
            # read raster into object
            if load_raster_to_db:
                self._load_raster_text(out_raster_path)