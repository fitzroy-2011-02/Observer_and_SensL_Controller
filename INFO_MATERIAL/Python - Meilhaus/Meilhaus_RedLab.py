# -*- coding: latin-1 -*-

__docformat__ = "restructuredtext en"

"""
File:			Meilhaus.py
Functionality:	Control Meilhaus I/O-Card
Dependancies:	
Created:		Matt, 19.04.06
Last modified:	        Tom, 07.12.2009  
Version:		
Copyright:		CCT

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




class HardwareError( ValueError ):
    pass


class Hardware:
    '''
    Functionality to control Meilhaus I/O-Card
    '''
    
    def __init__( self, param = None, verbose = 0 ):
        '''
        Initialize meilhaus class

        :param param:       Parameter object - SimpleReg.Param()
        :param verbose:     The higher the more output
        '''
        ## Meilhaus card number to deal with - starts from 0
        self.deviceNr = 0

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

        
    def OpenHardware( self ):
        '''
        Initialize error handling behaviour
        Set port configuration and reset outputs
        '''
        lockHardware.acquire()
        try:
            Hardware.CloseHardware( self )
            
            # initialize error reporting
            meDLL.cbErrHandling( DONTPRINT, DONTSTOP )
            
            # configure ports - first two -> output, third -> input
            err = meDLL.cbDConfigPort( self.deviceNr, FIRSTPORTA, DIGITALOUT )
            if err:
                meDLL.cbGetErrMsg( err, self.errString )
                raise HardwareError( self.errString.value )
            err = meDLL.cbDConfigPort( self.deviceNr, FIRSTPORTB, DIGITALOUT )
            if err:
                meDLL.cbGetErrMsg( err, self.errString )
                raise HardwareError( self.errString.value )
            err = meDLL.cbDConfigPort( self.deviceNr, FIRSTPORTCL, DIGITALIN )
            if err:
                meDLL.cbGetErrMsg( err, self.errString )
                raise HardwareError( self.errString.value )
            err = meDLL.cbDConfigPort( self.deviceNr, FIRSTPORTCH, DIGITALIN )
            if err:
                meDLL.cbGetErrMsg( err, self.errString )
                raise HardwareError( self.errString.value )
            
            # reset outputs
            err = meDLL.cbDOut( self.deviceNr, FIRSTPORTA, 0 )
            if err:
                meDLL.cbGetErrMsg( err, self.errString )
                raise HardwareError( self.errString.value )
            err = meDLL.cbDOut( self.deviceNr, FIRSTPORTB, 0 )
            if err:
                meDLL.cbGetErrMsg( err, self.errString )
                raise HardwareError( self.errString.value )

            # blink to signal success
            #meDLL.cbFlashLED( self.deviceNr )
            self.FlashLED()

        finally:
            lockHardware.release()
            
    def FlashLED(self):
        meDLL.cbFlashLED( self.deviceNr )
        
        # without this sleep, there is an runtime error on new fast computers, mostly at the second following command ..
        # HardwareError: Digital device is not responding - Is base address correct?
        time.sleep(0.5)
        #time.sleep(0.3)  # > 0.3 !!!


    def CloseHardware( self ):
        pass


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
    testing = 2
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
        
        
    