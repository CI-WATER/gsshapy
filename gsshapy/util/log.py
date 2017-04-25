#
# Originally from quest python library
# Adapted for GSSHApy
#
# License BSD-3 Clause

import logging
import appdirs
import os

from .metadata import version

logger = logging.getLogger('gsshapy')
null_handler = logging.NullHandler()
logger.addHandler(null_handler)

default_log_dir = appdirs.user_log_dir('gsshapy', 'logs')
default_log_file = os.path.join(default_log_dir, 'gsshapy.log')


def log_to_console(status=True, level=None):
    """Log events to  the console.

    Args:
        status (bool, Optional, Default=True)
            whether logging to console should be turned on(True) or off(False)
        level (string, Optional, Default=None) :
            level of logging; whichever level is chosen all higher levels will be logged.
            See: https://docs.python.org/2/library/logging.html#levels
      """

    if status:

        console_handler = logging.StreamHandler()

        logger.addHandler(console_handler)

        if level is not None:
            logger.setLevel(level)

        logger.info("GSSHApy {0}".format(version()))

    else:
        for i, j in enumerate(logger.handlers):
            if type(j).__name__ == 'StreamHandler':
                logger.removeHandler(logger.handlers[i])




def log_to_file(status=True, filename=default_log_file, level=None):
    """Log events to a file.

    Args:
        status (bool, Optional, Default=True)
            whether logging to file should be turned on(True) or off(False)
        filename (string, Optional, Default=None) :
            path of file to log to
        level (string, Optional, Default=None) :
            level of logging; whichever level is chosen all higher levels will be logged.
            See: https://docs.python.org/2/library/logging.html#levels
      """

    if status:
        try:
            os.mkdir(os.path.dirname(filename))
        except OSError:
            pass

        file_handler = logging.FileHandler(filename)
        logger.addHandler(file_handler)

        if level is not None:
            logger.setLevel(level)

        logger.info("GSSHApy {0}".format(version()))

    else:
        for i, j in enumerate(logger.handlers):
            if type(j).__name__ == 'FileHandler':
                logger.removeHandler(logger.handlers[i])
