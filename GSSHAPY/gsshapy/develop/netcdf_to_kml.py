from gsshapy.mapit.RasterConverter import RasterConverter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine('postgresql://swainn:(|w@ter@localhost:5432/gis')
Session = sessionmaker(bind=engine)
session = Session()

tableName = 'netcdf_raster'
ramp = 'rainbow'
name = 'NETCDF TEST'
path = '/Users/swainn/projects/netcdf_to_kml/netcdf.kml'



converter = RasterConverter(session=session)
            
kmlString = converter.getAsKmlGrid(tableName=tableName,
                                   rasterId=2,
                                   rasterIdFieldName='rid',
                                   name=name,
                                   rasterType='continuous',
                                   ramp=ramp,
                                   alpha=0.7)

with open(path, 'w') as f:
    f.write(kmlString)

