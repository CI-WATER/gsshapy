'''
********************************************************************************
* Name: Parse Tools
* Author: Nathan Swain
* Created On: July 15, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''
import shlex, re

def splitLine(line):
    '''
    Split lines read from files and preserve
    paths and strings.
    '''
    splitLine = shlex.split(line)
    return splitLine

def pathSplit(path):
    '''
    Split path by \\ or / to obtain parts
    '''
    path = re.split('/|\\\\', path)
    return path

def relativePath(path):
    '''
    Obtain relative path from a path
    '''
    spath = pathSplit(path)
    return spath[-1]

def chunk(keywords, lines):
    '''
    Divide a file into chunks between
    key words in the list
    '''
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
