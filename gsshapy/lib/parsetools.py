"""
********************************************************************************
* Name: Parse Tools
* Author: Nathan Swain
* Created On: July 15, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

import logging
import shlex
import re

logging.basicConfig()
log = logging.getLogger(__name__)

# CONSTANTS
REPLACE_NO_VALUE = -999999

def splitLine(line):
    """
    Split lines read from files and preserve
    paths and strings.
    """
    splitLine = shlex.split(line)
    return splitLine


def pathSplit(path):
    """
    Split path by \\ or / to obtain parts
    """
    path = re.split('/|\\\\', path)
    return path


def relativePath(path):
    """
    Obtain relative path from a path
    """
    spath = pathSplit(path)
    return spath[-1]


def chunk(keywords, lines):
    """
    Divide a file into chunks between
    key words in the list
    """
    chunks = dict()
    chunk = []
      
    # Create an empty dictionary using all the keywords
    for keyword in keywords:
        chunks[keyword] = []
    
    # Populate dictionary with lists of chunks associated
    # with the keywords in the list   
    for line in lines:
        if line.strip():
            token = line.split()[0]
            if token in keywords:
                chunk = [line]   
                chunks[token].append(chunk)   
            else:
                chunk.append(line)

    return chunks


def valueReadPreprocessor(valueString, replaceParamsFile=None):
    """
    Apply global pre-processing to values during reading throughout the project.

    Args:
        valueString (str): String representing the value to be preprocessed.
        replaceParamsFile (gsshapy.orm.ReplaceParamFile, optional): Instance of the replace param file. Required if
            replacement variables are included in the project.

    Returns:
        str: Processed value as a string
    """
    if type(valueString) is bool:
        log.warning("Only numerical variable types can be handled by the valueReadPreprocessor function.")
        return valueString

    # Default
    processedValue = valueString

    # Check for replacement variables
    if replaceParamsFile is not None and valueString is not None:
        if '[' in valueString or ']' in valueString:
            # Set default value
            processedValue = '{0}'.format(REPLACE_NO_VALUE)

            # Find the matching parameter and return the negative of the id
            for targetParam in replaceParamsFile.targetParameters:
                if targetParam.targetVariable == valueString:
                    processedValue = '{0}'.format(-1 * targetParam.id)
                    break

    return processedValue


def valueWritePreprocessor(valueString, replaceParamsFile=None):
    """
    Look up variable name in replace param file for the negative id given and return it.

    Args:
        valueString (str): String representing the value to be preprocessed.
        replaceParamsFile (gsshapy.orm.ReplaceParamFile, optional): Instance of the replace param file. Required if
            replacement variables are included in the project.

    Returns:
        str: Processed value as a string
    """
    if type(valueString) is bool:
        log.warning("Only numerical variable types can be handled by the valueReadPreprocessor function.")
        return valueString

    # Default
    variableString = valueString

    # Check for replacement variables
    if replaceParamsFile is not None:
        # Set Default
        if variableString == REPLACE_NO_VALUE:
            variableString = '[NO_VARIABLE]'
        else:
            try:
                number = int(valueString)
                if number < 0:
                    parameterID = number * -1

                    # Find the matching parameter
                    for targetParam in replaceParamsFile.targetParameters:
                        if targetParam.id == parameterID:
                            variableString = targetParam.targetVariable
                            break
            except:
                pass

    return variableString