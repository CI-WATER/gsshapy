'''
********************************************************************************
* Name: Initialize Database Functions
* Author: Nathan Swain
* Created On: August 6, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''
import os, time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool

from gsshapy.orm import metadata


def del_sqlite_db(path):
    try:
        os.remove(path)
    except:
        print 'Error: No DB at this location to delete.'


def init_db(sqlalchemy_url):
    '''
    Initialize database with gsshapy tables
    '''
    engine = create_engine(sqlalchemy_url)
    start = time.time()
    metadata.create_all(engine)
    return time.time() - start
    
def init_sqlite_memory(initTime=False):
    '''
    Initialize SQLite in Memory Only Database
    '''
    sqlalchemy_url = 'sqlite://'
    engine = create_engine(sqlalchemy_url,
                           poolclass=SingletonThreadPool)
    start = time.time()
    metadata.create_all(engine)
    
    if initTime:
        print 'TIME:', time.time() - start, 'seconds'
        
    return sqlalchemy_url
    
    
def init_sqlite_db(path, initTime=False):
    '''
    Initialize SQLite Database
    '''
    sqlite_base_url = 'sqlite:///'
    
    sqlalchemy_url = sqlite_base_url + path

    init_time = init_db(sqlalchemy_url)
    
    if initTime:
        print 'TIME:', init_time, 'seconds'
        
    return sqlalchemy_url
    
    
def init_postgresql_db(username, host, database, port='', password='', initTime=False):
    '''
    Initialize PostgreSQL Database
    '''
    ## NOTE: psycopg2 or similar driver required
    
    postgresql_base_url = 'postgresql://'
    
    if password != '':
        password = ':%s' % password
        
    if port != '':
        port = ':%s' % port
        
    sqlalchemy_url = '%s%s%s@%s%s/%s' % (
                      postgresql_base_url,
                      username,
                      password,
                      host,
                      port,
                      database
                      )
    
    init_time = init_db(sqlalchemy_url)
    
    if initTime:
        print 'TIME:', init_time, 'seconds'
    
    return sqlalchemy_url
        
def init_mysql_db(username, host, database, port='', password='', initTime=False):
    '''
    Initialize MySQL Database
    '''
    ## NOTE: mysql-python or similar driver required
    
    mysql_base_url = 'mysql://'
    
    if password != '':
        password = ':%s' % password
        
    if port != '':
        port = ':%s' % port
        
    sqlalchemy_url = '%s%s%s@%s%s/%s' % (
                      mysql_base_url,
                      username,
                      password,
                      host,
                      port,
                      database
                      )
    
    init_time = init_db(sqlalchemy_url)
    
    if initTime:
        print 'TIME:', init_time, 'seconds'
    
    return sqlalchemy_url

def create_session(sqlalchemy_url):
    engine = create_engine(sqlalchemy_url)
    maker = sessionmaker(bind=engine)
    session = maker()
    return session
    