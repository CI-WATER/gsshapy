'''
********************************************************************************
* Name: Parser v5
* Author: Herman Dolder
* Created On: June 13, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

#Done:
#Define Unknowns unto end of file (or line)
#recursivity
#3 try to implement the file reading
#3b try to implement the unknown in rows
#3c try to implement the unknown in columns
#3d put everything into class
#4 executes at init
#Parser5 take depth info out

#Future tasks:
#Work a little with var names and document
#Create codes for different files

codegag = \
    [ \
        ["R", None,\
            [\
                ["R", 1, ["C", "D", "T-DESC"]],\
                ["R", 1, ["C", "D", "I-NRPDS"]],\
                ["R", 1, ["C", "D", "I-NRGAG"]],\
                ["R", "NRGAG", ["C", "D", "F-X", "F-Y", "T-DESC"]],\
                ["R", "NRPDS" , ["C", "D", "I-YEAR", "I-MONTH", "I-DAY", "I-HOUR", "I-MIN", ["R", "NRGAG", ["C", "F-GAGVAL"]]]]\
            ]\
         ]\
    ]
  
filegag = "Z:/Desktop/Files/SkyDrive/Pendrive/BYU/Parser/test.gag"

codehead = \
     [ \
        ["R", 1, ["C", "D"]],\
        ["R", 1, ["C", "D", "F-ALPHA"]],\
        ["R", 1, ["C", "D", "F-BETA"]],\
        ["R", 1, ["C", "D", "F-THETA"]],\
        ["R", 1, ["C", "D", "I-LINKS"]],\
        ["R", 1, ["C", "D", "I-MAXNODES"]],\
        ["R", "MAXNODES" , ["C", "D", ["R", None, ["C", "I-CONNECT"]]]]\
    ]

filehead = "Z:/Desktop/Files/SkyDrive/Pendrive/BYU/Parser/header.cif"

class gpparser:
    instruct = None
    file = None
    i_array = None
    f_array = None
    o_array = None
    list = None

    def __init__(self, instruct, file):
        self.list = []
        self.instruct = instruct
        self.file = file
        self.f_array = self.readFile(file)
        self.f_array = self.cleanupArray(self.f_array)
        self.search(self.instruct, 0, 0, 0)

    def printList(self):
        for elem in self.list:
            print str(elem)

    def readFile(self, kind):
        f = open(kind, "r")
        arr_struc = []
        for line in f:
            arr_line = []
            tuples = line.split("\n")[0].split(" ")
            for tuple in tuples:
                elem = tuple.split("~")
                arr_line.append(elem)
            arr_struc.append(arr_line)
        f.close()
        return arr_struc

    def cleanupArray(self, array):
        cleanarray = []
        for line in array:
            cleanline = []
            numelem = 0
            while numelem < len(line):
                elem = line[numelem]
                content = elem[0]
                #print str(content)
                if content.startswith('"') and not content.endswith('"'):
                    on = True
                    while on:
                        numelem = numelem + 1
                        elem = line[numelem]
                        new_content = elem[0]
                        content = content + " " + new_content
                        if content[-1:] == '"':
                            on = False
                if content != '':    
                    cleanline.append([content])
                numelem = numelem + 1
            if cleanline != []:
                cleanarray.append(cleanline)
        return cleanarray
                    
    def searchList(self, code, order):
        for variable in self.list:
            if variable[3] == code and variable[0] == order:
                return int(variable[5])
        return None

    def search(self, code, depth, rowindex, rowi): 
        for part in code:  
            ##Define repetitions
            if isinstance(part[1], int):
                repeat = part[1]
            elif isinstance(part[1], str):
                repeat = self.searchList(part[1], rowi)
            elif part[1] == None:
                repeat = 1
            ##
            instructions = part[2]
            ##Go read columns
            if instructions[0] == "C":
                i = 0
                rowi2 = 0
                while i < repeat:
                    rowindex = rowindex + 1
                    colindex = -1
                    rowi2 = rowi2 + 1
                    self.analyze(instructions, 0, colindex, depth, rowindex, rowi, rowi2, 0)
                    i = i + 1
            ##Go one more level deep
            else:
                i = 0
                index = 0
                while i < repeat:         
                    rowindex = self.search(instructions, depth + 1, rowindex, index)
                    index = index + 1
                    if part[1] == None:
                        if rowindex == len(self.f_array):#rowmax:          
                            i = repeat
                    else:
                        i = i + 1
        return rowindex
    
    def analyze(self, line, depth, colindex, rowdepth, rowindex, rowi, rowi2, coli):
        #coli = 0
        for elem in line:
            if isinstance(elem, str):
                #do stuff
                colindex = colindex + 1    
                if elem != "C" and elem != "D":
                    coli = coli + 1
                    splval = elem.split("-")
                    name = splval[1]
                    type = splval[0]
                    self.list.append([rowi, rowi2, coli, name, type, self.f_array[rowindex - 1][colindex - 1][0]])
                   # print str([rowdepth, rowi, rowi2, depth, coli, name, type, self.f_array[rowindex - 1][colindex - 1][0]])
            else: 
                if isinstance(elem[1], int):
                    repeat = elem[1]
                elif isinstance(elem[1], str):
                    repeat = self.searchList(elem[1], rowi) #Could it need also a column reference??
                elif elem[1] == None:
                    repeat = 1
                subline = elem [2]
                i = 0
                index = 0
                while i < repeat:              
                    colindex = self.analyze(subline, depth + 1, colindex - 1, rowdepth, rowindex, rowi, rowi2, index)
                    index = index + 1 #see how to pass
                    if elem[1] == None:
                        if colindex == len(self.f_array[rowindex - 1]):
                            i = repeat
                    else:    
                        i = i + 1
        return colindex


qqq = gpparser(codehead, filehead)
ppp = gpparser(codegag, filegag)
