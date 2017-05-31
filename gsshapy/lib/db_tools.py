"""
********************************************************************************
* Name: Initialize Database Functions
* Author: Nathan Swain
* Created On: August 6, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

import logging
import os
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool

from ..orm import metadata, ProjectFile

logging.basicConfig()
log = logging.getLogger(__name__)


def del_sqlite_db(path):
    """
    Delete sqlite database
    """
    try:
        os.remove(path)
    except:
        log.error('No DB at this location to delete.')


def init_db(sqlalchemy_url):
    """
    Initialize database with gsshapy tables
    """
    engine = create_engine(sqlalchemy_url)
    start = time.time()
    metadata.create_all(engine)
    return time.time() - start


def init_sqlite_memory(initTime=False):
    """
    Initialize SQLite in Memory Only Database
    
    Args:
        initTime(Optional[bool]): If True, it will print the amount of time to generate database.

    Returns:
        tuple: The tuple contains sqlalchemy_url(str), which is the path to use 
        when creating a session as well as engine(str), which is the path to use
        when creating a session.

    Example::
    
        from gsshapy.lib.db_tools import init_sqlite_memory, create_session
        
        sqlalchemy_url, engine = init_sqlite_memory()
        
        db_work_sessionmaker = get_sessionmaker(sqlalchemy_url, engine)

        db_work_session = db_work_sessionmaker()
        ##DO WORK
        
        db_work_session.close()
    """
    sqlalchemy_url = 'sqlite://'
    engine = create_engine(sqlalchemy_url,
                           poolclass=SingletonThreadPool)
    start = time.time()
    metadata.create_all(engine)
    
    if initTime:
        print('TIME: {0} seconds'.format(time.time() - start))
        
    return sqlalchemy_url, engine
    
    
def init_sqlite_db(path, initTime=False):
    """
    Initialize SQLite Database
    
    Args:
        path(str): Path to database (Ex. '/home/username/my_sqlite.db').
        initTime(Optional[bool]): If True, it will print the amount of time to generate database.

    Example::
    
        from gsshapy.lib.db_tools import init_sqlite_db, create_session
        
        sqlite_db_path = '/home/username/my_sqlite.db'   
        
        init_postgresql_db(path=sqlite_db_path)
        
        sqlalchemy_url = init_sqlite_db(path=sqlite_db_path)
        
        db_work_sessionmaker = get_sessionmaker(sqlalchemy_url)

        db_work_session = db_work_sessionmaker()
        
        ##DO WORK
        
        db_work_session.close()
    """
    sqlite_base_url = 'sqlite:///'
    
    sqlalchemy_url = sqlite_base_url + path

    init_time = init_db(sqlalchemy_url)
    
    if initTime:
        print('TIME: {0} seconds'.format(init_time))
        
    return sqlalchemy_url
    
    
def init_postgresql_db(username, host, database, port='', password='', initTime=False):
    """
    Initialize PostgreSQL Database
    
    .. note:: psycopg2 or similar driver required
    
    Args:
        username(str): Database username.
        host(str): Database host URL.
        database(str): Database name.
        port(Optional[int,str]): Database port.
        password(Optional[str]): Database password.
        initTime(Optional[bool]): If True, it will print the amount of time to generate database.

    Example::
    
        from gsshapy.lib.db_tools import init_postgresql_db, create_session
        
        sqlalchemy_url = init_postgresql_db(username='gsshapy', 
                                            host='localhost', 
                                            database='gsshapy_mysql_tutorial', 
                                            port='5432', 
                                            password='pass')

        db_work_sessionmaker = get_sessionmaker(sqlalchemy_url)

        db_work_session = db_work_sessionmaker()
        
        ##DO WORK
        
        db_work_session.close()
    """
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
        print('TIME: {0} seconds'.format(init_time))
    
    return sqlalchemy_url


def init_mysql_db(username, host, database, port='', password='', initTime=False):
    """
    Initialize MySQL Database
    
    .. note:: mysql-python or similar driver required
    
    Args:
        username(str): Database username.
        host(str): Database host URL.
        database(str): Database name.
        port(Optional[int,str]): Database port.
        password(Optional[str]): Database password.
        initTime(Optional[bool]): If True, it will print the amount of time to generate database.

    Example::
    
        from gsshapy.lib.db_tools import init_mysql_db, create_session
        
        sqlalchemy_url = init_mysql_db(username='gsshapy', 
                                       host='localhost', 
                                       database='gsshapy_mysql_tutorial', 
                                       port='5432', 
                                       password='pass')
                                       
        db_work_sessionmaker = get_sessionmaker(sqlalchemy_url)

        db_work_session = db_work_sessionmaker()
        ##DO WORK
        
        db_work_session.close()
    """
    
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
        print('TIME: {0} seconds'.format(init_time))
    
    return sqlalchemy_url


def get_sessionmaker(sqlalchemy_url, engine=None):
    """
    Create session with database to work in
    """
    if engine is None:
        engine = create_engine(sqlalchemy_url)
    return sessionmaker(bind=engine)


def get_project_session(project_name, project_directory, map_type=None):
    """
    Load project manager and in memory sqlite db sessionmaker for GSSHA project
    """
    sqlalchemy_url, sql_engine = init_sqlite_memory()
    gdb_sessionmaker = get_sessionmaker(sqlalchemy_url, sql_engine)
    project_manager = ProjectFile(name=project_name,
                                  project_directory=project_directory,
                                  map_type=map_type)
    return project_manager, gdb_sessionmaker
