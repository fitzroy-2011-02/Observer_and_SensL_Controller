"""
Wir versuchen ein wirklich einfaches Programm zum Testen des
SiAPD Sensors von SensL zu schreiben.

Idee:
Das Mikroskop wird an eine Position gefahren, an welcher sich nur
ein Farbstoffmol. befindet. Das Mikroskop soll dann nach dem Start des
Prozesses den Tisch hin und her fahren, so dass das Farbmolekuel sich
mit einer definierten Geschwindigkeit durch,daraus heraus den Sensorbereich
bewegt.

Als Parameter stehen im Programm zur Verfuegung

- Verfahrgeschwindigkeit
- Entfernung
- Anzahl der Wiederholungen
- Verfahrrichtungsauswahl: horizontal / vertikal

Es gibt keine Parameterdatei, alle Parameter sind fest im Programmcode
definiert. Aber wenn du das liest dann wirst du auch die Parameter finden.


Wir probieren das jetzt ueber eine schicke HTML GUI, yes yes yes :)
"""

#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

sys.path.append("./py")
import hwConnection
import sensLControll

import time
from bottle import route, run, response, request, debug, static_file, send_file
import threading
import thread
import Queue
import os
import ctypes

pathToCSV =     """.\\\\data\\\\raw\\\\"""    # localtion of the htmlPage

pathToHTMLPage =".\\data\\htmlPage\\"         # location of this python file

# ______________________ release some directories
@route('/:filename')
def send_static(filename):
    return static_file(filename, root='.')

@route('/js/:filename')
def send_static(filename):
    return static_file(filename, root='./js')

@route('/css/:filename#.+#')
def send_static(filename):
    return static_file(filename, root='./css')

@route('/fonts/:filename')
def send_static(filename):
    return static_file(filename, root='./fonts')

@route('/data/:filename#.+#')
def send_static(filename):
    return static_file(filename, root='./data')

@route('/data/raw/:filename#.+#')
def send_static(filename):
    return static_file(filename, root='./data/raw')

@route('/data/htmlPage/:filename#.+#"')
def send_static(filename):
    return static_file(filename, root='./data/htmlPage')

@route('/img/:filename')
def send_static(filename):
    return static_file(filename, root='./img')
# ________________________________________________

# ______________________ main page
@route('/')
def main():
    return open("index.xhtml","r")
# ________________________________

""" ____________________________________________________________________________
Die Idee fuer das Threading ist, dass jeder Befehlsaufruf an den Mikroskoptisch
und an den SensL Sensor einen eigenen Thread bekommt.
____________________________________________________________________________ """

# ________________________ in this class we handle custom microscop commands
class executeCmd( threading.Thread ):
    # Override Thread's __init__ method to accept the parameters needed:
    def __init__ ( self, cmd ):
        self.cmd = cmd
        threading.Thread.__init__ ( self )

    def run( self ):
        res = mik.observerDevice.Call( self.cmd )
        myQueue.put( res )
# __________________________________________________________________________        


# __________________________ in this class we handle the sensL START command
class startReadToMemory( threading.Thread ):
    # Override Thread's __init__ method to accept the parameters needed:
    def __init__ ( self ):
        threading.Thread.__init__ ( self )

    def run( self ):
        res = sensLAPD.readToMemory()
        # do not read queue value so do not put result of start proces in there
        # sensLQueue.put( res )
# __________________________________________________________________________ 


# __________________________ in this class we handle the sensL STOP command
class stopReadToMemory( threading.Thread ):
    # Override Thread's __init__ method to accept the parameters needed:
    def __init__ ( self, fileName ):
        self.fileName = fileName
        threading.Thread.__init__ ( self )

    def run( self ):
        res = sensLAPD.stopReadToMemory( self.fileName )
        sensLQueue.put( res )
# __________________________________________________________________________ 

   
# _________________________________ main mic class
class observerMik:
    def __init__(self):
        self.observerDevice = hwConnection.Serial_Observer()
        # ----------------------------------------------------------
        # PARAMETER INIT VALUES
        # ----------------------------------------------------------
        # com port number
        self.mikCOMport = 0
        # velocity of movement mm/s
        self.mikVel = 6.43
        # distance to move um
        self.mikDist = 1000
        # number of cycle we want to move pace around
        self.mikCycles = 1
        # direction we want to move ( 0=horizontal, 1=vertical)
        self.mikDirection = 0        

    def connectMik(self, portNumber):
        res = self.observerDevice.myInit( port = int(portNumber) )
        # we will get a empty string is no device is connected to the given COM Port
        if res != "":
            return {res}
        else:
            return {0}

    def moveMik(self):
        # _______________first get current velocity
        oriVelCall = "S X? Y?"
        # print oriVelCall
        oriVel = self.observerDevice.Call(oriVelCall)
        # return something like ":A X=7.5 Y=7.5"

        # _______________set new velocity
        newVelCall = "S X=" + str(self.mikVel) + " Y=" + str(self.mikVel)
        self.observerDevice.Call(newVelCall)

        # _______________now get move call together
        # convert to micro meter 
        moveDist = str( int(self.mikDist) * 10)
        # get direction ( 0=horizontal, 1=vertical)
        if self.mikDirection == "0":
            directionString = "X="
        else:
            directionString = "Y="

        for i in xrange(int(self.mikCycles)):
            moveFinish = 0
            # change direction each time
            vorzeichen = str((-1)**i)[0:-1]
            moveCall = "R " + directionString + vorzeichen + moveDist
            # print moveCall
            # we are threading this call so we can stop movement if necessary
            thread.start_new_thread( executeCmd, ( moveCall ) )
            # self.observerDevice.Call(moveCall)
            while moveFinish == 0:
                time.sleep(0.1)
                moveStatus = self.observerDevice.Call("STATUS")
                # print moveStatus
                if moveStatus == "N":
                    moveFinish = 1
        
        # reset velocity
        resetVelCall = oriVelCall[2:]
        resetVelCall = "S" + resetVelCall
        #self.observerDevice.Call(resetVelCall)
        
        return 1        

    def stopMik(self):
        self.observerDevice.Call("HALT")
        return 1
# ________________________________________________

@route('/cCOM', method = "POST")
def connect():
    # try to connect to Microscop
    comPort = request.POST['comPort']
    resConnectMik = mik.connectMik(int(comPort))
    # returns an set type variable so we have to use the pop function
    # to get the content
    
    # try to connect to Sensor
    resConnectSAPD = sensLAPD.OpenHardware()
    
    return { "resMic": str(resConnectMik.pop()),
             "resSAPD": str(resConnectSAPD) }

@route('/stopMOVE', method = "POST")
def stop():
    res = mik.stopMik()
    return {"res": res}

@route('/callCMD', method = "POST")
def callCMD():
    callString = request.POST['callString']
    callThread = executeCmd( callString )
    callThread.start()
    res = myQueue.get()
    
    return {"res": res}

@route('/startSensLAPD', method = "POST")
def startSensLAPD():
    expTime = request.POST['expTime']
    
    # set the data acquisition time [ms]
    # cause of a lack of thinking ability this variable
    # was first supposed to be a frequency - thats wrong -
    # it a time in ms - and it defines how long we sum the
    # signal by the maximum frequency available 50kHz
    
    # so this means we have to calculate how many signals we have
    # to accumulate so we get the desired acquisition time
    # 50 000 Hz = 50 signals/ms
    # have to double the count because for a reason I do not know every 2'nd
    # signal is 32768 ?? I leave these alone
    countNumber = int(expTime) * 50 * 2
    
    # I also have to calculate the max value of the range option, from
    # chart drawing
    # so max would be (have to divide by 2? look a few lines above)
    global maxRange
    maxRange = 32768 * countNumber / 2
    
    sensLAPD.counts = ctypes.c_long(int(countNumber))
    startSensLThread = startReadToMemory()
    startSensLThread.start()
    
    # can't wait for result because thread is running until we end it
    # no result will be available - program is would stuck here
    # res = sensLQueue.get()
    res = "Get Signal Thread gestartet."
    return {"res": res}

@route('/startSensLZStapel', method = 'POST')
def startSensLZStapel():
    # there is no use of threads in this function, so you have to wait until
    # it's finished :) -quick and dirty
    
    # here we want to find the focus position for the z axes
    # we start at the current z position and going up the number, dist
    # of given steps and aquire given number of signals for the given time
    zCount =    int( request.POST['zcount'] )         # number of steps
    zDist =     int( request.POST['zdist'] )          # step width [um]
    zExpTime =  int( request.POST['expTime'] )        # exposure time [ms]
    zExpCount = int( request.POST['expCount'] )       # number of exposures
    
    # we need a 2D array to save the results
    # one dimension for each z step
    # one dimension for for the signal array related to the step
    focusSignals = []
    # here we save the calculated mean values
    focusMeanSignals = []
    
    # description see startSensLAPD function
    countNumber = zExpTime * 50 * 2
    sensLAPD.counts = ctypes.c_long(int(countNumber))

    global maxRange
    maxRange = 32768 * countNumber / 2    
    
    # instruction we send to the mikroscope z axes to move it
    moveString = "R Z=" + str(zDist)
    
    # we need a filename
    filename =      "zSearch"
    fileNameURL =   pathToCSV + filename + ".csv"
    
    counter = 0
    while( os.path.exists( fileNameURL ) == True ):
        # we insert a counter
        newFileName = filename + "_" + str(counter)
        fileNameURL = pathToCSV + newFileName + ".csv" 
        counter = counter + 1
    
    if counter != 0:
        htmlFileName = pathToHTMLPage + newFileName + ".html"
    else:
        htmlFileName = pathToHTMLPage + filename + ".html"
    
    # we make a series of "pictures" add the current z position
    zStepSignalArrary = sensLAPD.readToMemory(zExpCount)
    focusSignals.append(zStepSignalArrary)
    
    # for each step we make 
    for zstep in xrange(zCount):
        
        # we go up by given dist
        mvRes = mik.observerDevice.Call( moveString )
        
        # we make a series of "pictures" at the current z position
        zStepSignalArrary = sensLAPD.readToMemory(zExpCount)
        focusSignals.append(zStepSignalArrary)
    
    # so first we calc the mean values
    meanSig = 0
    for signalStepArray in xrange( len(focusSignals) ):
        meanSig = 0
        for signal in xrange( len(focusSignals[signalStepArray]) ):
            meanSig = meanSig + focusSignals[signalStepArray][signal]
            
        meanSig = meanSig / len( focusSignals[signalStepArray] )
        
        focusMeanSignals.append(meanSig)
    try:         
        # now we have to save the result in a csv
        # we jsut save the mean values
        fileObj = open( fileNameURL, "w")
        
        # add labelline
        labelLine = "z step with z dist: " + str(zDist) + ", mean signal from Exp Time: " + str(zExpTime)
        fileObj.write(labelLine + "\n")
        
        k = 0
        for meanSig in xrange( len(focusMeanSignals) ):
            dataLine = str(k) + "," + str(focusMeanSignals[meanSig]) + "\n"
            fileObj.write(dataLine)
            k = k + 1
        fileObj.close()
        
        # and last but not least generate the html page
        htmlPageURL = generateHTMLPage( fileNameURL, htmlFileName, labelLine)
        
        return { "error": "0",
                 "res": htmlPageURL}
        
    except Exception, e:
        returnValue = "Python error: " + str(e)
        return { "error": "1",
                 "res": returnValue }        
    
    
    
@route('/stopSensLAPD', method = 'POST')
def stopSensLAPD():
    fileName = request.POST['fileName']
    
    stopSensLThread = stopReadToMemory( fileName )
    
    stopSensLThread.start()
    
    res = sensLQueue.get()  # res is a tuple
                            # 0 = 0 no error, 1 error
                            # 1 = error description or data filename
    # reset thread Events
    sensLAPD.stopSignalCollection.clear()
    sensLAPD.signalCollectionFinished.clear()

    # everything went fine
    if( res[0] == 0):
        # now generte htmlPage
        csvFileNameURL = pathToCSV + res[1] + ".csv"
        htmlFileName = pathToHTMLPage + res[1] + ".html"
        
        htmlFileURL = generateHTMLPage( csvFileNameURL, htmlFileName )
        
        return { "error": "0",
                 "res": htmlFileURL}
    
    else:
        return { "error": "1",
                 "res": res[1]}
        
@route('/showResult', method = "POST")
def showScanResult():
    # we generate a new html page with the plot of the csv file
    # we made with the dygraph library
    csvFileName = request.POST['fileName']
    
    csvFileNameURL = pathToCSV + csvFileName + ".csv"
    htmlFileName = pathToHTMLPage + csvFileName + ".html"
    
    htmlPageURL = generateHTMLPage( csvFileNameURL, htmlFileName )
    
    return {"res": htmlPageURL}
    
def generateHTMLPage( csvFileNameURL, htmlFileName, labelString = "\"time\", \"signal\", \"mean\"" ):
    #print csvFileNameURL
    #print htmlFileName
    
    # want to put the data in the file so I can watch it without server side support
    dataContent = ""
    csvFile = open( csvFileNameURL, "r" )
    i = 0
    for line in csvFile:
        if(i!=0):
            dataContent = dataContent + "[" + line[0:-1] + "]" + ",\n"
        
        if(line == ""):
            dataContent = dataContent + "[" + line[0:-1] + "]" + "\n"
        
        i = i+1    
    
    # we also need to write the js file into the file
    dyGraphJSFile = open(".\js\dygraph-combined.js", "r")
    dyGraphJSContent = dyGraphJSFile.read()
    
    headString = str("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//DE"
                    "http://www.w3.org/TR/html4/loose.dtd">
                    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
                    <html>
                    <head>
                    <title></title>
                    <script type="text/javascript">
                    """+ dyGraphJSContent +
                    """
                    </script>

                    </head>
                    <body>
                    <div id="graphDIV" style="width:800px; height:600px;"></div>
                    <script type="text/javascript">
                        g2 = new Dygraph(
                          document.getElementById("graphDIV"),
                          [""") + dataContent  + str("""], // path to CSV file
                          {valueRange:[-750, """ + str(maxRange) + """ ],
                          labels:[""" + labelString + """] }                                    // options
                        );
                    </script>
                    </body>
                    </html>
                    """)
    
    htmlPageURL =  htmlFileName
    dataHTMLPage = open( htmlPageURL, "w")
    dataHTMLPage.write(headString)
    dataHTMLPage.close()
    
    return htmlPageURL
    
if __name__ == '__main__':
    # wir legen erstmal eine comConnection classe an
    global mik
    mik = observerMik()
    
    global myQueue
    myQueue = Queue.Queue()
    
    # sensL/Meilhaus hardware controll class
    global sensLAPD
    sensLAPD = sensLControll.Hardware()
    
    global sensLQueue
    sensLQueue = Queue.Queue()
    
    debug(True)
    run(host='localhost', port=8080)

