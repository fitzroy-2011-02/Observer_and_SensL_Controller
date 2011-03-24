#http://python.net/crew/theller/ctypes/tutorial.html

import ctypes   # for -Dll
import copy
import os

import pythoncom
import gc       # garbage collector

# TBD:  LIZ-Test !!, GetRegistrationInfo


LD_ERROR = -1
MESSAGE_BUFFER_LENGTH = 1000    ## the maximum number of characters per message + 1


#def myPrin


def MessageBox( message, title, mode = 5168 ):
    try:
        import win32gui
        return win32gui.MessageBox( 0, message, title, mode )
    except:
        pass


class dmxDecoder:
    # das mit dem COM war irgendwie nix
    # TBD LIZ-Test !!
    # Achtung! z.Zt. nur eine msg


    def GetLibPath(self):
        return self.libPath

         
    def __init__(self):

        # ***  Select the libary path for tests ***
        # removed: SetLibPath()


        # Path Ermittlung, wie von Legeo genutzt:
        ##import win32api
        ##import ctypes
        ##
        ##print "GetModuleFileName(0):", win32api.GetModuleFileName(0)        # 0 == NULL !!!
        ###print "GetModuleFileName(None):", win32api.GetModuleFileName(None)  # ERROR
        ##
        ##
        ##print win32api.GetComputerName()
        ##ctypes.windll.LoadLibrary('legeoDev.dll')
        ##
        ##handle = win32api.GetModuleHandle('legeoDev.dll')
        ##print "GetModuleHandle:", handle
        ##
        ##print "GetModuleFileName:", win32api.GetModuleFileName(handle)
        

        local = 0
        system = 0

        if local:
            libPath = os.path.abspath(os.path.curdir)
            libPath = os.path.join(libPath, 'legeoDev.dll')
        elif system:
            # Default PaternExpert installation path 
            libPath = 'C:\\WINDOWS\\system\\legeoDev.dll'
        else:
##            libPath = os.path.join(os.path.curdir, 'LegeoDev', 'legeoDev.dll')
##            libPath = os.path.abspath(libPath)
            libPath = 'legeoDev.dll'

        print '*** libPath', libPath
            
        self.libPath =  libPath

        # *** Einbindung der Lib ***

        self.dmxDLL = ctypes.windll.LoadLibrary(libPath) 

        # *** Einbindung der Lib (Alternativen) ***
        
        ##from ctypes import cdll
        ##from ctypes import windll 

        # without path parameter
        ##dmxDLL = ctypes.cdll.legeoDev    # cdecl
        ##dmxDLL = ctypes.windll.legeoDev  # stdcall   !!

        ##dll = cdll.LoadLibrary("C:\\WINDOWS\\system\\legeoDev.dll") 
        ##dll = windll.LoadLibrary(u"C:\\WINDOWS\\system\\legeoDev.dll")        



    def dmxDecodeFile( self, fp ):
        ## Nur fuer eine DMX im Bild
      
        message = '***'
        
        s = str(copy.deepcopy(fp))
        s = s.replace('\\', '/')    #!!
        s = unicode(s)

        dmxDLL = self.dmxDLL

        x = ctypes.c_char_p(s)
        rtv = dmxDLL.legeoDev_ReadFile(x)

        print 'rtvReadFile ::', rtv
        if rtv == -1:
            errMsg = ' '* MESSAGE_BUFFER_LENGTH
            #?? -> charpointer ??
            lenErr = dmxDLL.legeoDev_GetLastError(errMsg, MESSAGE_BUFFER_LENGTH)
            print 'errMsg::', errMsg , '\n\n'
            message = errMsg
        elif rtv == 0:
            pass
            print 'cant find a DMX'
        elif rtv == 1:
            msg = ' '* MESSAGE_BUFFER_LENGTH
            lenMsg =  dmxDLL.legeoDev_GetNextMessage(msg, MESSAGE_BUFFER_LENGTH, None, None)
            print 'DMX-Code ::', msg.strip()
            message = msg
        else:
            pass
            print 'DMX count > 1 ::', rtv
            
        # CString Bereinigen
        message = message.split('\x00')[0].strip()
        #print "DMX::message:", message

        # Achtung! z.Zt. nur eine msg
        return (rtv, message)

    def test(self):
        print "dmxDecoder.test"
##        self.dmxDLL = None
##        del self.dmxDLL

##        import time
##        if 1:
##            gc.collect()
##        time.sleep(2)

    def __del__(self):
        # siehe Versuche, die unter function test liefen
        pass



class dmxDecoder_COM:

    # current state - for testing only !

    if 0:
        _reg_progid_ = "Python.AM_dmxDecoder_TST_B"
        _reg_clsid_  = "{8D36F94D-F980-4047-9806-5B51511B23CF}"
        _reg_clsctx_ = pythoncom.CLSCTX_LOCAL_SERVER

    else:
        _reg_progid_ = "Python.AM_dmxDecoder_TST"
        _reg_clsid_  = "{71806091-3F8D-4F72-A715-BB54FFB243D8}"
        _reg_clsctx_ = pythoncom.CLSCTX_INPROC_SERVER
        

    _public_methods_ = [ 'Version',
                         'dmxDecodeFile',
                         'GetLibPath']    

    def Version(self):
        return '080118 - 01'
    
    def GetLibPath(self):
        dmxDec = dmxDecoder()
        return dmxDec.GetLibPath()

    def dmxDecodeFile( self, fp ):
        ## Nur fuer eine DMX im Bild

        dmxCode = -1 # None

        dmxDec = dmxDecoder()

        #(rtv, message) = dmxDec.dmxDecodeFile(fp)
        rtv = dmxDec.dmxDecodeFile(fp)
        print rtv #, message
        if rtv[0] == 1: 
            dmxCode = rtv[1]
        return dmxCode

    
if __name__ == "__main__":


    mode = 20   

    if mode == 10: 
        #neue COM-Registrierung

        import win32com.server.register
        print "Registering ..."
        win32com.server.register.UseCommandLine( dmxDecoder_COM )
        # run this file itself to register COM 

    if mode == 11: 
        #Standard COM-Nutzung (no treading)
        
        from win32com.client import Dispatch
        dmx = Dispatch("Python.AM_dmxDecoder_TST")

        print 'Version:', dmx.Version()
        ret = dmx.dmxDecodeFile('.\dmx_test.bmp')
        print 'ret:', ret

    if mode == 20:
        # Standard Nutzung (ohne COM)
        dmx = dmxDecoder()
        print dmx.dmxDecodeFile('.\dmx_test.bmp')

    if mode == 30:
        dmx = dmxDecoder()


        #ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)

        #myDll.myFunc(byref(n), byref(Id_dat))
        #myDll.myFunc(byref(n), byref(Id_dat))
        #pf_aAA = c_char_p( myAaa ) 
        #pf_srLen = c_int(strLen) 

