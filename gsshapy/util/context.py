#
# context.py
# Author: Alan D. Snow, 2017
#
# License BSD-3 Clause
"""The purpose of this module is to provide context managers."""

from contextlib import contextmanager
import os


@contextmanager
def tmp_chdir(new_path):
    """Change directory temporarily and return when done."""
    prev_cwd = os.getcwd()
    os.chdir(new_path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)
