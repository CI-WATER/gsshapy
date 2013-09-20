'''
Created on Sep 20, 2013

@author: swainn
'''
import psycopg2
from psycopg2 import Binary

host = 'localhost'
port = '5432'
username = 'swainn'
password = '(|w@ter'
database = 'gis'
sql = "SET bytea_output TO escape; SELECT ST_AsGDALRaster(rast, 'JPEG') As rastjpg FROM idx_index_maps WHERE filename='combo.idx';"


conn = psycopg2.connect("dbname=%s user=%s host=%s password=%s port=%s" % (database, username, host, password, port))
cur = conn.cursor()
cur.execute(sql)

bill = cur.fetchall()
print bill

with open('/Users/swainn/testing/bob.jpg', 'wb') as f:
    f.write(bill[0][0])

# SQL: SELECT ST_AsGDALRaster(rast, 'JPEG') AS rastjpg FROM idx_index_maps WHERE filename='combo.idx';