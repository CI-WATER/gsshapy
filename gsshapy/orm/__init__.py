"""
********************************************************************************
* Name: Object Relational Model
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Base class for all of model classes
DeclarativeBase = declarative_base()

# Global metadata. This is used to
# Initialize a database with the
# Appropriate tables. See db_tools
metadata = DeclarativeBase.metadata

# Import GSSHAPY Model Classes/Tables
from .prj import *
from .idx import *
from .cmt import *
from .ele import *
from .tim import *
from .gag import *
from .cif import *
from .hmet import *
from .gst import *
from .spn import *
from .gpi import *
from .snw import *
from .loc import *
from .map import *
from .msk import *
from .pro import *
from .rep import *
from .lnd import *
from .generic import *
from .wms_dataset import *
