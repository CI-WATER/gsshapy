'''
********************************************************************************
* Name: ORM Tests
* Author: Nathan Swain
* Created On: June 7, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''
from gsshapy.lib import db_tools as dbt

dbt.del_sqlite_db('/Users/swainn/testing/db/gsshapy_lite.db')
dbt.init_sqlite_db('/Users/swainn/testing/db/gsshapy_lite.db', time=True)

# dbt.init_postgresql_db(username='swainn',
#                            host='localhost',
#                            database='gsshapy_lite',
#                            port='5432',
#                            password='(|w@ter',
#                            time=True
#                            )
