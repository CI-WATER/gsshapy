***************
Supported Files
***************

**Last Updated:** July 30, 2014

Not all files are supported by GsshaPy. A summary of the files that are supported and
the *file* class handler that reads the file is provided in the following table.

---------------------
Input Files Supported
---------------------

The following table lists the input files that are supported by the current 
version of GsshaPy. The files are listed with the appropriate project file card
and *file* class handler. Some files do not have a specified file extension. These are indicated with
an ellipses ( ... ).

=======================  ================  ==============================================
Project File Card        File Extension    Handler                
=======================  ================  ==============================================
#PROJECTION_FILE         pro               :doc:`ProjectionFile <api/file-io/pro>`
MAPPING_TABLE            cmt               :doc:`MapTableFile <api/file-io/cmt>`
PRECIP_FILE              gag               :doc:`PrecipitationFile <api/file-io/gag>`
CHANNEL_INPUT            cif               :doc:`ChannelInputFile <api/file-io/cif>`
STREAM_CELL              gst               :doc:`GridStreamFile <api/file-io/gst>`
IN_THETA_LOCATION        ith               :doc:`OutputLocationFile <api/file-io/loc>`
IN_HYD_LOCATION          ihl               :doc:`OutputLocationFile <api/file-io/loc>`
IN_SED_LOC               isl               :doc:`OutputLocationFile <api/file-io/loc>`
IN_GWFLUX_LOCATION       igf               :doc:`OutputLocationFile <api/file-io/loc>`
HMET_WES                 ...               :doc:`HmetFile<api/file-io/hmet>`
NWSRFS_ELEV_SNOW         ...               :doc:`NwsrfsFile <api/file-io/snw>`
HMET_OROG_GAGES          ...               :doc:`OrthographicGageFile <api/file-io/snw>`
STORM_SEWER              spn               :doc:`StormPipeNetworkFile <api/file-io/spn>`
GRID_PIPE                gpi               :doc:`GridPipeFile <api/file-io/gpi>`
OVERLAND_DEPTH_LOCATION  odi               :doc:`OutputLocationFile <api/file-io/loc>`
OVERLAND_WSE_LOCATION    owi               :doc:`OutputLocationFile <api/file-io/loc>`
OUT_WELL_LOCATION        igw               :doc:`OutputLocationFile <api/file-io/loc>`
REPLACE_PARAMS           ...               :doc:`ReplaceParamFile <api/file-io/rep>`
REPLACE_VALS             ...               :doc:`ReplaceValFile <api/file-io/rep>`
ELEVATION                ele               :doc:`RasterMapFile <api/file-io/map>`
WATERSHED_MASK           msk               :doc:`RasterMapFile <api/file-io/map>`
ROUGHNESS                ovn               :doc:`RasterMapFile <api/file-io/map>`
RETEN_DEPTH              ...               :doc:`RasterMapFile <api/file-io/map>`
READ_OV_HOTSTART         ...               :doc:`RasterMapFile <api/file-io/map>`
STORAGE_CAPACITY         ...               :doc:`RasterMapFile <api/file-io/map>`
INTERCEPTION_COEFF       ...               :doc:`RasterMapFile <api/file-io/map>`
CONDUCTIVITY             ...               :doc:`RasterMapFile <api/file-io/map>`
CAPILLARY                ...               :doc:`RasterMapFile <api/file-io/map>`
POROSITY                 ...               :doc:`RasterMapFile <api/file-io/map>`
MOISTURE                 ...               :doc:`RasterMapFile <api/file-io/map>`
PORE_INDEX               ...               :doc:`RasterMapFile <api/file-io/map>`
RESIDUAL_SAT             ...               :doc:`RasterMapFile <api/file-io/map>`
FIELD_CAPACITY           ...               :doc:`RasterMapFile <api/file-io/map>`
SOIL_TYPE_MAP            ...               :doc:`RasterMapFile <api/file-io/map>`
WATER_TABLE              wte               :doc:`RasterMapFile <api/file-io/map>`
READ_SM_HOTSTART         ...               :doc:`RasterMapFile <api/file-io/map>`
ALBEDO                   alb               :doc:`RasterMapFile <api/file-io/map>`
WILTING_POINT            wtp               :doc:`RasterMapFile <api/file-io/map>`
TCOEFF                   tcf               :doc:`RasterMapFile <api/file-io/map>`
VHEIGHT                  vht               :doc:`RasterMapFile <api/file-io/map>`
CANOPY                   cpy               :doc:`RasterMapFile <api/file-io/map>`
INIT_SWE_DEPTH           ...               :doc:`RasterMapFile <api/file-io/map>`
AQUIFER_BOTTOM           aqe               :doc:`RasterMapFile <api/file-io/map>`
GW_BOUNDFILE             bnd               :doc:`RasterMapFile <api/file-io/map>`
GW_POROSITY_MAP          por               :doc:`RasterMapFile <api/file-io/map>`
GW_HYCOND_MAP            hyd               :doc:`RasterMapFile <api/file-io/map>`
EMBANKMENT               dik               :doc:`RasterMapFile <api/file-io/map>`
DIKE_MASK                dik               :doc:`RasterMapFile <api/file-io/map>`
CONTAM_MAP               ...               :doc:`RasterMapFile <api/file-io/map>`
INDEX_MAP*               idx			   :doc:`IndexMapFile <api/file-io/map>`
=======================  ================  ==============================================


.. note::

    *Index maps are listed in the mapping table file with the INDEX_MAP card.

----------------------
Output Files Supported
----------------------

The following table lists the output files that are supported by the current 
version of GsshaPy. The files are listed with the appropriate project file card
and *file* class handler. Some files do not have a specified file extension. These are indicated with
an ellipses ( ... ).

==========================  ==================  ==============================================
Project File Card           File Extension      Handler
==========================  ==================  ==============================================
OUTLET_HYDRO                otl                 :doc:`TimeSeriesFile <api/file-io/tim>`
OUT_THETA_LOCATION          oth                 :doc:`TimeSeriesFile <api/file-io/tim>`      
OUT_HYD_LOCATION            ohl                 :doc:`TimeSeriesFile <api/file-io/tim>`
OUT_DEP_LOCATION            odl                 :doc:`TimeSeriesFile <api/file-io/tim>`
OUT_SED_LOC                 osl                 :doc:`TimeSeriesFile <api/file-io/tim>`
CHAN_DEPTH                  cdp                 :doc:`LinkNodeDatasetFile <api/file-io/lnd>`
CHAN_STAGE                  cds                 :doc:`LinkNodeDatasetFile <api/file-io/lnd>`
CHAN_DISCHARGE              vdq                 :doc:`LinkNodeDatasetFile <api/file-io/lnd>`
CHAN_VELOCITY               cdv                 :doc:`LinkNodeDatasetFile <api/file-io/lnd>`               
OUT_GWFULX_LOCATION         ogf                 :doc:`TimeSeriesFile <api/file-io/tim>`
OUTLET_SED_FLUX             osf                 :doc:`TimeSeriesFile <api/file-io/tim>`
OUTLET_SED_TSS              oss                 :doc:`TimeSeriesFile <api/file-io/tim>`
OUT_TSS_LOC                 tss                 :doc:`TimeSeriesFile <api/file-io/tim>`
MAX_SED_FLUX                ...                 :doc:`LinkNodeDatasetFile <api/file-io/lnd>`
OUT_CON_LOCATION            ocl                 :doc:`TimeSeriesFile <api/file-io/tim>`
OUT_MASS_LOCATION           oml                 :doc:`TimeSeriesFile <api/file-io/tim>`
SUPERLINK_JUNC_FLOW         ...                 :doc:`TimeSeriesFile <api/file-io/tim>`
SUPERLINK_NODE_FLOW         ...                 :doc:`TimeSeriesFile <api/file-io/tim>`
OVERLAND_DEPTHS             odo                 :doc:`TimeSeriesFile <api/file-io/tim>`
OVERLAND_WSE         		owo                 :doc:`TimeSeriesFile <api/file-io/tim>`
GW_OUTPUT                   ...                 :doc:`WMSDatasetFile <api/file-io/wms_dataset>`
DISCHARGE                   ...                 :doc:`WMSDatasetFile <api/file-io/wms_dataset>`
INF_DEPTH                   ...                 :doc:`WMSDatasetFile <api/file-io/wms_dataset>`
SURF_MOIS                   ...                 :doc:`WMSDatasetFile <api/file-io/wms_dataset>`
RATE_OF_INFIL               ...                 :doc:`WMSDatasetFile <api/file-io/wms_dataset>`
DIS_RAIN                    ...                 :doc:`WMSDatasetFile <api/file-io/wms_dataset>`
GW_OUTPUT                   ...                 :doc:`WMSDatasetFile <api/file-io/wms_dataset>`
GW_RECHARGE_CUM             ...                 :doc:`WMSDatasetFile <api/file-io/wms_dataset>`
GW_RECHARGE_INC             ...                 :doc:`WMSDatasetFile <api/file-io/wms_dataset>`
DEPTH                       dep                 :doc:`WMSDatasetFile <api/file-io/wms_dataset>`
SNOW_SWE_FILE               swe                 :doc:`WMSDatasetFile <api/file-io/wms_dataset>`
==========================  ==================  ==============================================

.. note::

    WMS Dataset Files can only be read in if the map type was set to 1 during the model run.

---------------
Partial Support
---------------

Many files are not fully supported by GsshaPy, meaning that they are not abstracted into several objects to make working
with them easy. However, many of these files are partially supported via the :class:`gsshapy.orm.GenericFile` object.
This file works by reading the entire contents of the file into a single text field in the database. The files that are
supported by this class are listed in the following table. Some files do not have a specified file extension. These are indicated with
an ellipses ( ... ).

========================  ================
Project Card              File Extension
========================  ================
ST_MAPPING_TABLE          smt
SECTION_TABLE             ...
SOIL_LAYER_INPUT_FILE     ...
EXPLIC_HOTSTART           ...
READ_CHAN_HOTSTART        ...
CHAN_POINT_INPUT          ...
HMET_SURFAWAYS            ...
HMET_SAMSON               ...
HMET_ASCII                ...
GW_FLUXBOUNDTABLE         flx
SUPERLINK_JUNC_LOCATION   ...
SUPERLINK_NODE_LOCATION   ...
SUMMARY                   sum
EXPLIC_BACKWATER          ...
WRITE_CHAN_HOTSTART       ...
LAKE_OUTPUT               lel
GW_WELL_LEVEL             owl
ADJUST_ELEV               ele
NET_SED_VOLUME            ...
VOL_SED_SUSP              ...
OPTIMIZE                  opt
========================  ================