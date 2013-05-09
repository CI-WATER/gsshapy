'''
Created on Mar 12, 2013

@author: swainn
'''

if __name__ == '__main__':
    pass

from model import init_model, DBSession
from sqlalchemy import create_engine
from model.gsshapy import *

engine = create_engine('postgresql+pg8000://sdc50@localhost:5432/post_gssha_test')
metadata.create_all(engine)


