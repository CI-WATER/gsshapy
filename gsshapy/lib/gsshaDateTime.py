"""
********************************************************************************
* Name: TimeSeriesModel
* Author: Scott Christensen, Nathan Swain
* Created On: July 31, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

import time

def convertOtlFile(otlFile, convertedOtlFile):
    #Convert .otl file into an ODM uploadable foramt
    
    fileNew = open(convertedOtlFile, 'w')
    fileNew.write("LocalDateTime,DataValue" + "\n")
    for line in open(otlFile): #maybe add an if statement that alerts if there is no such filepath
        dateTime, discharge = line.split()
        fileNew.write("%s,%s\n" % (convertDateTime(dateTime), discharge))
    fileNew.close()

def convertDateTime(gsshaDateTime):
    #TODO: WHAT DOES THIS DO???????? it returns itself...
    year,frac = gsshaDateTime.split(".")
    daysInYear = 365
    d = float("0." + frac)
    day, d = getValueAndFraction(daysInYear,d)
    hour, d = getValueAndFraction(24, d)
    minutes, d = getValueAndFraction(60,d)
    minutes += d
    minutes = int(round(minutes,0))

    if(minutes < 60):
        pass
    else:
        hour += 1
        minutes -= 60
    
    if(hour == 24):
        hour = 0
        day += 1
    
    parsedTime = "%s %s %s:%02d" % (year, day, hour, minutes)
    convertedDateTime = time.strptime(parsedTime,"%Y %j %H:%M")
    convertedDateTimeStr = time.strftime("%Y-%m-%d %H:%M",convertedDateTime)
    return gsshaDateTime

def getValueAndFraction(devisor, decimal):
    value = int(devisor * decimal)
    fraction = decimal*devisor - value
    return (value, fraction)

if __name__ == '__main__':
    convertOtlFile()
