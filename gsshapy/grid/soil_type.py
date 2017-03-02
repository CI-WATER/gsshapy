import fiona

file_path = '/home/rdchlads/scripts/gsshapy/tests/grid_standard/phillipines/phillipines_5070115700.shp'
with fiona.open(file_path) as c:
    print(c.bounds)


'''
import csv, pyodbc

# set up some constants
MDB = '/home/rdchlads/GSSHAModeling/Raw Data/JudysBranch/SSURGOGSoil/Raw/soildb_US_2002.mdb'
DRV = '{Microsoft Access Driver (*.mdb)}'
# connect to db
con = pyodbc.connect('DRIVER={};DBQ={}'.format(DRV,MDB))
cur = con.cursor()

# run a query and get the results
SQL = 'SELECT * FROM component;' # your query goes here
rows = cur.execute(SQL).fetchall()
cur.close()
con.close()

print(rows)
'''
