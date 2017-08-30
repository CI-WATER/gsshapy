import geopandas as gpd


def check_watershed_boundary_geometry(shapefile_path):
    """Make sure that there are no random artifacts in the file."""
    wfg =  gpd.read_file(shapefile_path)
    first_shape = wfg.iloc[0].geometry
    if hasattr(first_shape, 'geoms'):
        raise ValueError(
            "Invalid watershed boundary geometry. "
            "To fix this, remove disconnected shapes or run "
            "gsshapy.modeling.GSSHAModel.clean_boundary_shapefile")