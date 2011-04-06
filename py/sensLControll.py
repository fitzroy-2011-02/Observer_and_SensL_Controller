# -*- coding: latin-1 -*-

__docformat__ = "restructuredtext en"

"""
File:						sensLControll.py
Functionality:	Control Meilhaus I/O -USB device - with special respect to a connected sensL APD sensor
Dependancies:		- does not depend on but is based on Meilhaus_RedLab.py file
                - where all parts not necessary are removed
Created:				Matt, 19.04.06
Last modified:	Alex, 14.03.2011  
Version:		
Copyright:			CCT

"""


## Changes:
## - 07.12.2009 remove camera; reduced to Meilhaus only
## - 07.12.2009 Bugfix: FlashLED
## - 07.12.2009 move TimeoutLock to module
## used Driver: RedLab_Web_2_8
##
##


#-------------------------------------------------------------------

import threading
import time

class TimeoutError( ValueError ):
    pass

class TimeoutLock:
    # implements a lock with timeout - in seconds
    def __init__( self, timeout = 5.0 ):
        self.timeout = timeout
        self.lock = threading.RLock()

    def acquire( self, blocking = 1, timeout = 0 ):
        if blocking:
            start = time.time()
            if not timeout:
                timeout = self.timeout
            got_it = 0
            while not got_it:
                if time.time() - start > timeout:
                    raise TimeoutError( "Lock could not be acquired" )
                got_it = self.lock.acquire( 0 )
        else:
            got_it = self.lock.acquire( 0 )

        return got_it            

    def release( self ):
        self.lock.release()

#-------------------------------------------------------------------


import os
import time
import shutil

import ctypes
import ctypes.wintypes


meDLL = ctypes.windll.cbw32

TIMEOUT_ME = 3.0

#import Misc
#lockHardware = Misc.TimeoutLock( TIMEOUT_ME )

#import TimeoutLock
#lockHardware = TimeoutLock.TimeoutLock( TIMEOUT_ME )

lockHardware = TimeoutLock( TIMEOUT_ME )

# constants for error reporting
DONTPRINT =         0
PRINTWARNINGS =     1
PRINTFATAL =        2
PRINTALL =          3

# types of error handling
DONTSTOP =          0
STOPFATAL =         1
STOPALL =           2

# Types of digital input ports
DIGITALOUT =        1
DIGITALIN =         2

# Types of digital I/O Ports 
AUXPORT =           1
FIRSTPORTA =        10
FIRSTPORTB =        11
FIRSTPORTCL =       12
FIRSTPORTCH =       13

# max error string length
ERRSTRLEN =         256

# further UL definitions
BIP2VOLTS =         14
BACKGROUND  =       0x0001
CONTINUOUS =        0x0002
SINGLEIO  =         0x0020
AIFUNCTION =        1
CURRENTREVNUM =     6.10

# one of my definitions
MAX_COUNT_FOR_CONT_SCAN = ctypes.c_long(500000) # max number of signals we are able to
                                                # acquire in one run

SAMPLE_RATE =       50000                       # max sample rate availabel with the A/D converter

NULL_VALUE =        32768                       # we substract this value from the signal
                                                # beaause 32768 means null light and 0
                                                # means sensor saturation 

class HardwareError( ValueError ):
    pass

class Hardware:
    '''
    Functionality to control Meilhaus I/O-Card
    '''
    
    def __init__( self, boardNumber = 0, lowChan = 0, highChan = 1, counts = 50, rate = SAMPLE_RATE,  fileNamePath = ".\\data\\raw\\" ):
        '''
        Initialize meilhaus class

        :param verbose:     The higher the more output
        '''
        
        self.deviceNr = ctypes.c_int(boardNumber)   # Meilhaus card/board number to deal with
                                                    # - starts from 0 where 0 is the dummy/test
                                                    # board, when dealing with USB devices
        
        self.lowChan =  ctypes.c_short(lowChan)     # first input chanel we scan 
        self.highChan = ctypes.c_short(highChan)    # last input chanel we scan
        self.counts =   ctypes.c_long(counts)       # number of measurements - we are using
                                                    # continuous option so ?
                                                    # seems to be, that it has to be a multiple of 31
                                                    
        self.rate =     ctypes.c_long(rate)         # frequency of measurement [Hz] 
        
        #self.options =  ctypes.c_int(BACKGROUND + CONTINUOUS)   # measurement runs in background
        #                                                        # as long as we do not stop it
        self.options = ctypes.c_int(0)
        
        self.range =    ctypes.c_int(BIP2VOLTS)                 # signal alternate between +/- 2V

        self.fileNamePath = fileNamePath            # path of the directory where we want to
                                                    # save the raw data to
                                                   
        self.stopSignalCollection = threading.Event()       # we set this event when we want
                                                            # to finish
        self.signalCollectionFinished = threading.Event()   # is set after the last sum signal
                                                            # is generated
                                                   
        # here we try to connect the  dataArray param with the memory handle so we can access the
        # scan result more easyly
        # cast(obj, type)
        #       This function is similar to the cast operator in C. It returns a new instance
        #       of type which points to the same memory block as obj. type must be a pointer
        #       type, and obj must be an object that can be interpreted as a pointer.
        
        #self.memHandle =  meDLL.cbWinBufAlloc(MAX_COUNT_FOR_CONT_SCAN)  # reserve some memory
                                                                         # returns a int value
                                                                         
        #self.dataArray = ctypes.cast( self.memHandle, ctypes.POINTER( ctypes.wintypes.WORD ) )
        
        # here we collect the signals
        # each entry is the sum of one sampling run (samping rate = 50kHz, count number
        # give by user)
        # self.sumSignalArray = []
        
        # error string
        self.errString = ctypes.c_char_p( "a" * ERRSTRLEN )
        
    def __del__( self ):
        '''
        Deconstructor
        '''
        # close hardware
        try:
            self.CloseHardware()
        except:
            pass
          
    def CloseHardware( self ):
        pass
        
    def OpenHardware( self ):
        '''
        Initialize error handling behaviour
        Set port configuration and reset outputs
        '''
        lockHardware.acquire()
        try:
            Hardware.CloseHardware( self )
            
            # test if sensor is connected
            # Declare Revision level of the Universal Library
            # if hardware is not connected a errorcode is returned, else 0
            revNumber = ctypes.c_float(CURRENTREVNUM)
            ULStat = meDLL.cbDeclareRevision(ctypes.byref(revNumber))
            
            if( ULStat == 0 ):
                # initialize error reporting
                meDLL.cbErrHandling( DONTPRINT, DONTSTOP )
                # when we check later in the process for error, 0 means error so we return 1, cause
                # we have no error                
                ULStat = 1
            
        finally:
            lockHardware.release()
            return ULStat
            
    def FlashLED(self):
        meDLL.cbFlashLED( self.deviceNr )
        
        # without this sleep, there is an runtime error on new fast computers, mostly
        # at the second following command ..
        # HardwareError: Digital device is not responding - Is base address correct?
        time.sleep(0.5)
        #time.sleep(0.3)  # > 0.3 !!!

    def SetOutput( self, nr, val = 1 ):
        '''
        Set output

        :param nr:      Number of output, starts with 0
        :param val:     0 or 1 to reset or set output respectively
        '''
        lockHardware.acquire()
        try:
            err = meDLL.cbDBitOut ( self.deviceNr, FIRSTPORTA, nr, val )  # org
            if err:
                meDLL.cbGetErrMsg( err, self.errString )
                raise HardwareError( self.errString.value )
        finally:
            lockHardware.release()

    def GetInput( self, nr ):
        '''
        Get input of camera

        :param nr:      Number of input, starts with 0
        :return:        0 or 1 if input is reset or set respectively
        '''
        lockHardware.acquire()
        try:
            bit_val = ctypes.c_ushort()
            # first 16 bits are outputs
            err = meDLL.cbDBitIn( self.deviceNr, FIRSTPORTA, nr + 16, ctypes.byref( bit_val ) )
            if err:
                meDLL.cbGetErrMsg( err, self.errString )
                raise HardwareError( self.errString.value )
        finally:
            lockHardware.release()

        return bit_val.value
    
    def startReadToFile( self, fileName ):
        '''
        Scans a range of A/D channels and stores the samples
        in a disk file. cbFileAInScan() reads the specified
        number of A/D samples at the specified sampling rate
        from the specified range of A/D channels from the
        specified board.
        
        - the problem is you need to decide how many signal points
          you want to read in advance - so no continuous scan is possible
        '''
        
        # here we want to save the signal values
        fileName = self.fileNamePath + str(fileName) + ".dat"
        
        # but first check if this file already exists, we do not want to override
        # precious data
        counter = 0
        while( os.path.exists( fileName ) == True ):
            # we insert a counter
            fileName = self.fileNamePath + str(fileName) + "_" + str(counter) + ".dat"
            counter = counter + 1
        
        """
        Check the status of the current background operation
        Parameters:
            BoardNum  :the number used by CB.CFG to describe this board
            Status    :current status of the operation (IDLE or RUNNING)
            CurCount  :current number of samples collected
            CurIndex  :index to the last data value transferred 
            FunctionType: A/D operation (AIFUNCTIOM)
        """
        
        status =    ctypes.c_int()    # 0 = not running, 1 = running
        curCount =  ctypes.c_long()
        curIndex =  ctypes.c_long()
        fileName =  ctypes.c_char_p(fileName)
        
        ULStat = meDLL.cbGetStatus (self.deviceNr, ctypes.byref(status), ctypes.byref(curCount), ctypes.byref(curIndex))
                
        # not running
        if( status.value == 0 ):
            ULStat = meDLL.cbFileAInScan ( self.deviceNr, self.lowChan, self.highChan, self.counts, ctypes.byref(self.rate), self.range, fileName, self.options )
            return ULStat
        # running
        else:
            ULStat = "running"
            return ULStat
    
    def readToMemory( self, dataPointCounts = -1 ):
        """
        param
            dataPointCounts:    if we do not want to make a continuous meausrement, until
                                the stop button is pressed
                                we here can define a number of dataPoints that has to
                                be aquired

        Check the status of the current background operation
        Parameters:
            BoardNum    :the number used by CB.CFG to describe this board
            Status      :current status of the operation (IDLE or RUNNING)
            CurCount    :current number of samples collected
            CurIndex    :index to the last data value transferred 
            FunctionType: A/D operation (AIFUNCTIOM)
        """
        # reset thread Events
        sensLAPD.stopSignalCollection.clear()
        sensLAPD.signalCollectionFinished.clear()
        
        self.memHandle =  meDLL.cbWinBufAlloc(MAX_COUNT_FOR_CONT_SCAN)  # reserve some memory
                                                                        # returns a int value
                                                                         
        status =    ctypes.c_int()    # 0 = not running, 1 = running
        curCount =  ctypes.c_long()
        curIndex =  ctypes.c_long()
        
        ULStat = meDLL.cbGetStatus (self.deviceNr, ctypes.byref(status), ctypes.byref(curCount), ctypes.byref(curIndex))
        
        self.sumSignalArray = []
        
        # not running
        if( status.value == 0 ):
            while( ULStat == 0 and self.stopSignalCollection.isSet() == 0 ):
                # we are not in continous and not in background mode so the function cbAInScan
                # will return when samples have been collected
                # when finished we sum all signals and put it in our data Array then we wait
                # a short time and do it again
            
                # than go get them
                ULStat = meDLL.cbAInScan ( self.deviceNr, self.lowChan, self.highChan, self.counts, ctypes.byref(self.rate), self.range, self.memHandle, self.options )
                
                ULStatCounts = meDLL.cbGetStatus (self.deviceNr, ctypes.byref(status), ctypes.byref(curCount), ctypes.byref(curIndex))
                signalNumber = curCount.value
                
                # now save memory data to a array
                arrayData = (ctypes.c_ushort * signalNumber)()
                conversionStat = meDLL.cbWinBufToArray( self.memHandle, ctypes.byref(arrayData), 0, self.counts.value )
                
                
                sumSig = 0
                for i in xrange( 0, signalNumber, 2 ):
                    sumSig = sumSig + NULL_VALUE - arrayData[i]
                    #print arrayData[i]
                
                self.sumSignalArray.append(sumSig)
                
                # lets count down if we are using non continuous mode (dataPointCounts != -1)
                if( dataPointCounts > -1 ):
                    
                    # decrement index
                    dataPointCounts = dataPointCounts - 1
                    
                    # check if we aquired all points
                    if( dataPointCounts > 0 ):
                        dataPointCounts = dataPointCounts - 1
                    else:
                        # do not set stopSignalCollection here because in the stopReadToMemory
                        # function we call this event must not be set to go through
                        # so normally the stopReadToMemory function is called in an own
                        # thread to cancel this thread - in this scenario we just call the
                        # function in the same thread because we cancel this thread now -
                        # this dataPointCounts stuff was added later, so this is very, very
                        # dirty :)
                        
                        # we now do it another way, do not call the stopReadToMemory function
                        # beacause we write a new wirte to file function 
                        self.stopSignalCollection.set()
                        self.signalCollectionFinished.set()
                        
                        # free buffer
                        meDLL.cbWinBufFree( self.memHandle )
                        
                        # just return collected data
                        res = self.sumSignalArray
                        return res
            
                # wait a short time for other actions
                time.sleep(0.01)
            
            if( ULStat == 0 and self.stopSignalCollection.isSet() == 1 ):
                
                self.signalCollectionFinished.set()
                
                return "Sensor collection finished"
            else:
                return "Error " + str(ULStat)
        
        # running
        else:
            ULStat = "Sensor currently working"
            return ULStat
                
    def stopReadToMemory( self, fileName ):        
        # check if there is a running process
        #status =    ctypes.c_int()    # 0 = not running, 1 = running
        #curCount =  ctypes.c_long()
        #curIndex =  ctypes.c_long()
        
        #ULStat = meDLL.cbGetStatus (self.deviceNr, ctypes.byref(status), ctypes.byref(curCount), ctypes.byref(curIndex))
        
        # running
        if( self.stopSignalCollection.isSet() == 0 ):        
            # stop process
            #ULStatStopBackground = meDLL.cbStopBackground ( self.deviceNr )
            
            # set the event to stop collecting signals
            self.stopSignalCollection.set()
            
            # wait until we get the signal that the collection has finished
            self.signalCollectionFinished.wait()

            # now data should be available
            # we now also calculate the mean value
            meanSig = 0
            for i in xrange( len(self.sumSignalArray) ):
                meanSig = meanSig + self.sumSignalArray[i]
            meanSig = meanSig / len(self.sumSignalArray)

            # here we want to save the signal values
            fileNameURL = self.fileNamePath + str(fileName) + ".csv"
            
            # but first check if this file already exists, we do not want to override
            # precious data
            counter = 0
            try:
                while( os.path.exists( fileNameURL ) == True ):
                    # we insert a counter
                    newFileName = fileName + "_" + str(counter)
                    fileNameURL = self.fileNamePath + str(newFileName) + ".csv" 
                    counter = counter + 1
                
                fileObj = open( fileNameURL, "w")
                
                labelLine = "time,signal,mean\n"
                fileObj.write(labelLine)
                
                # !!!!!! ---------------------------------------------------------- !!!!!!!!!!
                # I just take every second entry in the memory, because the values between are
                # alwayes 32768, why I do not know - I do this (take every 2'nd) now in
                # readToMemory function the sign
                # !!!!!! ---------------------------------------------------------- !!!!!!!!!!
                k = 0
                for i in xrange( len(self.sumSignalArray) ):
                  #dataLine = str(i) + "," + str(self.dataArray[i]) +"\n"
                  dataLine = str(k) + "," + str(self.sumSignalArray[i]) + "," + str(meanSig) + "\n"
                  fileObj.write(dataLine)
                  k = k + 1
                fileObj.close()
            except Exception, e:
                returnValue = "Python error: " + str(e)
                return (1, returnValue)
            
            # now I can delet the buffer
            memBufCleanReturn = meDLL.cbWinBufFree( self.memHandle )
            
            # check if everthing went fine
            sensLRes =  memBufCleanReturn
            
            # no error occured in the meDLL function calls
            if(sensLRes == 0):
                if(counter == 0):
                    returnValue = (0, fileName)
                else:
                    returnValue = (0, newFileName)
                                    
            else:
                returnValue = (1, "An error in the Sensor function calls occured")
 
            return returnValue
        
        # not running, nothing to stop
        else:
            returnVal = (1, "Nothing to stop. Sensor is not running.")
            return returnVal


    def readDataFile( self, fileName, firstPoint = 1, numPoints = 0 ):
      '''
      Reads data from a streamer file.
      '''
      
      FileName =      ctypes.c_char_p(fileName)
      
      # first get infos of the file we want to open
      LowChan =       ctypes.c_short()
      HighChan =      ctypes.c_short()
      PretrigCount =  ctypes.c_long() 
      Count =         ctypes.c_long()
      Rate =          ctypes.c_long()                     # sampling rate (samples per second)
      Range =         ctypes.c_int()
      
      
      fileInfoErr = meDLL.cbFileGetInfo( FileName, ctypes.byref(LowChan), ctypes.byref(HighChan), ctypes.byref(PretrigCount), ctypes.byref(Count), ctypes.byref(Rate), ctypes.byref(Range) )
      
      if( fileInfoErr != 0 ):
        return fileInfoErr
      else:
        FirstPoint = ctypes.c_long(firstPoint)
        
        if(numPoints != 0):
          Count.value = numPoints
        else:
          Count.value = Count.value
        
        self.DataBuffer = (ctypes.c_ushort * Count.value)()
        #for i in range(Count.value):
        #  DataBuffer[i] = i
        #DataBufferPointer = ctypes.pointer(DataBuffer)
        
        readFileErr = meDLL.cbFileRead( FileName, FirstPoint, ctypes.byref(Count), ctypes.byref(self.DataBuffer) )
        
        #convertDataErr = meDLL.cbAConvertData (self.deviceNr, Count, ctypes.byref(DataBuffer), None);
        
        return self.DataBuffer
        
    def convertToCSV( self, fileName ):
      '''
      tries to read a streamer file and convert it to an CSV file type so we can
      visualize the data using the extraordinary -dygraphs JavaScript Visualization Library-
      '''
      # first read stream file, generated from Meilhaus A/D Converter
      # data [tpye = tuble]
      data = self.readDataFile( fileName )
      if len(data) >1:
        # file we want to save to
        csvFileName = fileName[0:-3]
        csvFileName = csvFileName + "csv"
        csvFile = open(csvFileName,"w")
        labelLine = "time,signal \n"
        csvFile.write(labelLine)
        for i in xrange(len(data) - 1):
          dataLine = str(i) + "," + str(data[i]) +"\n"
          csvFile.write(dataLine)
        csvFile.close()
    
    def readVIn(self, PORT = 0):
        '''
         Reads am A/D input channel, and returns a voltage value.
         If the specified A/D board has programmable gain, the this 
         function sets the gain to the specific range. The voltage
         value is returned to analog_val
         
         @param PORT: channel number or port that is read
         @type PORT: int
         
         @return: voltage value
         @rtype: float
        '''
        timer = time.time()
        lockHardware.acquire()
        #time.sleep(1.0)
        
        try:
            Hardware.CloseHardware( self )
            
            # initialize error reporting
            meDLL.cbErrHandling( DONTPRINT, DONTSTOP )
            
            # configure analog ports 
            analog_val = ctypes.c_float()
            ADRANGE = 1   # 1 for single ended use
            OPTIONS = 0   # for future use

            err = meDLL.cbVIn ( self.deviceNr, PORT, ADRANGE, ctypes.byref( analog_val ), OPTIONS)
            
            if err:
                meDLL.cbGetErrMsg( err, self.errString )
                raise HardwareError( self.errString.value )
            
            # blink to signal success
            #meDLL.cbFlashLED( self.deviceNr )
            #self.FlashLED()

        finally:
            lockHardware.release()
        if analog_val.value < 0.2:
            self.reading = 'OVERFLOW'
            self.calc_value = analog_val.value
            #print "o"
        else:
            self.reading = 'pressed'
            self.calc_value = analog_val.value
            
        return analog_val.value

            
if __name__ == "__main__":
    testing = 3
    if testing == 1:
        h = Hardware( verbose = 1 )
        if 1:
            h.OpenHardware()  #!!
            
            print h.GetInput( 0 )
            h.SetOutput( 0, 1 )
            h.SetOutput( 0, 1 )
            h.FlashLED()
            print h.GetInput( 0 )
            h.SetOutput( 0, 0 )
            print h.GetInput( 0 )

        raw_input('fine..')
    if testing == 2:
        h = Hardware( verbose = 1 )
        for i in range(100):
            time.sleep(1)
            print h.readVIn(0)
            print h.readVIn(1)
            print h.readVIn(2)
            print h.readVIn(3)
            print h.readVIn(4)
            print h.readVIn(5)
            print h.readVIn(6)
            print h.readVIn(7)
            print "---------"
        #h.FlashLED()
        raw_input('fine..')

    if testing == 3:
        h = Hardware( verbose = 1 )
        h.readToFile()
        time.sleep(10)
        
        #h.convertToCSV( "test.txt" )
        
    