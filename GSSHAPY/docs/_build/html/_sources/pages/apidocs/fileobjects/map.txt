*********
Map Files
*********

Although index maps and other raster maps are both GRASS ASCII maps, a special
table was created for index maps for easier implementation.

Index Map File Object
=====================

File extension: **idx**

.. autoclass:: gsshapy.orm.IndexMap
	:members:
	:inherited-members:
	
	.. autoattribute:: gsshapy.orm.IndexMap.__tablename__
	
	
Raster Map File Object
======================

File extensions: **Variable** (e.g.: ele, msk, aqe)

.. autoclass:: gsshapy.orm.RasterMapFile
	:members:
	:inherited-members:
	
	.. autoattribute:: gsshapy.orm.RasterMapFile.__tablename__