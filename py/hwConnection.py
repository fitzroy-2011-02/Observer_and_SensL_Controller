## Thomas


## History:
## mySerialEx 0.1 -> 0.2 : unterdruecken des EOL returns in read mySerialEx



def DebugString(str):
    print '-- dStr--'
    for c in str:
        print 'dStr:', ord(c), "'"+ c +"'"
    return str

##>>> ord('\r')
##13
##>>> ord('\n')
##10

import serial   # for Const
from serial import Serial
import time
import traceback


class mySerial(Serial):
    #Log: siehe ASP
    # diese Classe erlaubt das Loggen der COM-Kommunikation

    def Version(self):
        return '0.1'
    
    def __init__(self):
        Serial.__init__(self)
        self.lastDirection = None
        self.logging = 'OFF'

    def read(self, size):

        if self.logging == 'ON':
            try:
                pass
            except:
                pass

##        if self.logging == 'ON':
##            if self.lastDirection == 'WRITE' or self.lastDirection == None:   # newDirection in '"rite , None'
##                self.lastDirection = 'READ'
##                #print # fuer zeilenumbruch
##                print "<<",
##        rtv = Serial.read(self, size)
##
##        if len(rtv) == 0: print 'timeout !!!' #TBD raise
##        
##        if self.logging == 'ON':
##            print rtv,

        rtv = Serial.read(self, size)
        return rtv

    def write(self, s):
        
        if self.logging == 'ON':
            try:
                pass
            except:
                pass

##        if self.logging == 'ON':
##            if self.lastDirection == 'READ' or self.lastDirection == None:   # newDirection
##                self.lastDirection = 'WRITE'
##                #print # fuer zeilenumbruch
##                print ">>",
##        print s,

        rtv = Serial.write(self, s)
        return rtv

class mySerialEx(mySerial):
    
    def Version(self):
        return '0.2'
    
    def __init__(self):
        mySerial.__init__(self)

    def myInit(self, port=0):   #TBD !!
        rtv = 0
        try:
            self.port = port                #0-COM1, 1-COM2 #print ser.portstr
            #_________________________# open the serial
            # check if open already
            rtv = self.isOpen()
            # if not try to open
            if not rtv:   
                # open the serial
                rtv = self.open()
                # check the Serial if it worked
                rtv = self.isOpen()
                # if not give serial free
                if not rtv:   #break
                    self.serial = None # New ??
                    # 'can not open the serial'
            
            # now send a command to see if device is connected
            # because just because the COM is available does not mean there is
            # a device connected to it
            #_________________________# check if the right device is connected
            # hopefully no other devices uses this command, so I test it,
            # connect flag: cause I know that if there is no device we will hang in
            #               the readEx function, so now there is kind of timeout(2s)
            rtv = self.Call('VERSION', connect = 1)
            
        except:
            print "exception"
            traceback.print_exc()
            
        return rtv   

    def readEx(self, deleteEOL = 'ON', connecting = 0):    ##  ~ Get Answer
        # deleteEOL: EOL wird im returnstring nicht mit zurueckgegeben
        # the connecting flag is for testing if there is a device at the COMPort
        # sometimes the timeout flag doesn't work cause you get a empty string back, so
        # the timeout doesn't catch it and it's not the EOL char either
        aStr = ''
        if connecting == 0:
            while not self.EOL in aStr:     # TBD abbruch -> timeout !!
                aStr = aStr + self.read(1)
             #   if i == 1 and aStr =='':
             #       break
             #   i = i+1
        else:
            i = 0
            while not self.EOL in aStr:     
                aStr = aStr + self.read(1)
                if i == 1 and aStr =='':            # timeout
                    break
                i = i+1
        
        if deleteEOL == 'ON': #delete EOL
            aStr = aStr[0:-len(self.EOL)]
        rtv = aStr
        return rtv

    def writeEx(self, s):
        s = s + self.EOL
        rtv = Serial.write(self, s)
        return rtv

    def Call(self, cmd, noResp = 0, connect = 0):
        # sometimes we don't need to wait for an answer, or sometimes
        # there won't be an answer at all, newer
        self.writeEx(cmd)
        if noResp == 0:
            rtv = self.readEx(connecting = connect)
            return rtv
        else:
            return 0


## OWIS ##
class Serial_OWIS(mySerialEx):
    # Protokol-Regeln fuer OWIS Lstep extern via COM 

    def Version(self):
        return '0.1'
    
    def __init__(self):
        mySerialEx.__init__(self)
        #self.logging = 'OFF'

        self.EOL = '\r'

        self.baudrate = 9600
        self.parity = serial.PARITY_ODD
        self.stopbits = 2
        self.timeout = 1.0

class Serial_Observer(mySerialEx):
    # Protokol-Regeln fuer Mikroskoptisch Observer Lstep extern via COM 

    def Version(self):
        return '0.1'
    
    def __init__(self):
        mySerialEx.__init__(self)
        #self.logging = 'OFF'

        self.EOL = '\r\n'

        self.baudrate = 9600
        self.parity = serial.PARITY_NONE
        self.stopbits = 1
        self.timeout = 1.0    


if __name__ == "__main__":

    port_ESE = 6
    port_OWIS = 4

    print "start"

##    owis = Serial_OWIS()
##    owis.myInit(port = port_OWIS)
##    ese = Serial_ESE()
##    ese.myInit(port = port_ESE)

##    eseMtpr = Serial_ESE()
##    eseMtpr.myInit(port = 7)    

    # TBD: Port !!
    

    if 1 == 0:
        print owis.Call('!cal X')
        print owis.Call('?status')

    if 1 == 1:
        
        eseMtpr = ESE_MTPR()
        eseMtpr.myInit(port = 7)

        tStart = time.clock()

        xOffset = 20.0
        yOffset = 36.0

        eseMtpr.MoveXY( xOffset, yOffset, mode = "ABSOLUTE")
        #test: (hinter schwarz)
        #eseMtpr.MoveXY( 0, 20, mode = "RELATIVE")
        for i in range(1,2):
            eseMtpr.MoveXY( xOffset, yOffset + i, mode = "ABSOLUTE")
            #eseMtpr.MoveXY( 0, 1, mode = "RELATIVE")

            tStart = time.clock()
            eseMtpr.ScopeXY()
            print i, 'time (ScopeXY()):', time.clock() - tStart

            tStart = time.clock()
            values = eseMtpr.GetScopeResults()
            print i, 'time (GetScopeResults()):', time.clock() - tStart

##        print 'time (move x):', time.clock() - tStart
##


            fp = 'c:\\lala001.txt'
            if fp <> '':
                #f = open(fp, 'a+')
                f = open(fp, 'w')
                for i in range(len(values)):
                    #f.write( str(i) + '\t' + str(values[i]) )
                    f.write( str(i+1) + '\t' + str(values[i]) + '\n' )
                f.close()  

            print len(values)
            
####        
####        values = eseMtpr.GetScopeResults()
##            print '-' * 40
##            #print values
##            for v in values:
##                print v
##            print '-' * 40

        

    if 1 == 0:
        #Test Scopemodus 2


        ##    Scope modus:
        ##
        ##    br 1 - board remote, umd ein zweites ok nach methodenstart zu bekommen
        ##    bmm <n> - setze methode 12=scope A1E1, 13=scope E1D2, 14=scope E2D2
        ##    bms - starte methode, wenn br 1 dann kommt ein ok fuer den befehl und ein  ok fuer das ende der messung
        ##    bmas <n> - scope average 1-250, bestimmt wieviele punkte zu einem zusammengefasst werden
        ##    die beteutet die messung wird laenger
        ##    bmbd? <n> - liefert bis zu 10 messwerten, n=index des ersten datenpunktes(0-1490)
        ##
        ##    beispiel:
        ##    bmbd? 1490
        ##    4875.133057 4874.264160 4874.100830 4873.100586 4872.441895 4872.410400 4871.584
        ##    961 4870.784424 4870.648438 4869.903320
        ##
        ##    Anmerkung:
        ##    um alle daten der scope methode abzufragen muss der index des bmbd? befehls erhoeht werden.

# nicht realisiert
##        print eseMtpr.Call('bmbf?')     # abtastfrequenz
##        print eseMtpr.Call('bmbf 10')   # abtastfrequenz    3000 error
##        print eseMtpr.Call('bmbf?')     # abtastfrequenz

        ## New nach Telefonat:
        ## Abtastfrequenz gibt es zwar in der Befehlsliste ist aber nicht realisiert.
        ## Geschwindigkeit geht z.Zt. nur ueber Averige (bmas) 0- 250
        ## bei Av 1 ca. 0.7 sec fuer alle Werte
        ## bei aver > .. wird punkt zu Strich ;-)

        ## returnwerte: ueberlauffunction ist deactiviert  > 4096 ist Schwachsinn
        ## laut Wiest 4V == 4000 nimmt er als Schwelle


        eseMtpr = ESE_MTPR()
        eseMtpr.myInit(port = 7)

        tStart = time.clock()

        xOffset = 20.0
        yOffset = 36.0
        eseMtpr.MoveXY( xOffset, yOffset, mode = "ABSOLUTE")
        #test: (hinter schwarz)
        eseMtpr.MoveXY( 0, 20, mode = "RELATIVE")



        print 'time (move x):', time.clock() - tStart

        eseMtpr.ScopeXY()
        
                

##        print eseMtpr.Call('srd')       # delete all records
##        print eseMtpr.Call('br 1')      # board remote, umd ein zweites ok nach methodenstart zu bekommen
##        print eseMtpr.Call('bmm 13')    # bmm <n> - setze methode 12=scope A1E1, 13=scope E1D2, 14=scope E2D2
##                                        #13 lt. fl a1e2 scope
##        # es geht nur 13 sonst error
##        print eseMtpr.Call('bmas?')     # scope average 1-250, bestimmt wieviele punkte zu einem zusammengefasst werden
##        print eseMtpr.Call('bmas 3')  # 98,5 sec (incl. predel - 250) 3 sec (incl. predel - 1) 
##        print eseMtpr.Call('bmas?')
##
##        #print eseMtpr.Call('bmm 13')    # bmm <n> - setze methode 12=scope A1E1, 13=scope E1D2, 14=scope E2D2
##
##
##        
##        tStart = time.clock()
##        print eseMtpr.Call('bms')       # starte methode, wenn br 1 dann kommt ein ok fuer den befehl und ein  ok fuer das ende der messung
##        ## warte ! auf 2. O.K.
##        #for i = 1 to .. len(..)
##        #while int(self.Call('bs?')) <> 0:  # ?? bs oder direkt auf ok warten?
##        if eseMtpr.readEx() == 'O.K.':
##            print 'time (scope):', time.clock() - tStart
##
        values = eseMtpr.GetScopeResults()
        print '-' * 40
        #print values
        for v in values:
            print v
        print '-' * 40
            
##        #get scan results
##        counts = int(eseMtpr.Call('bmbr?'))
##        print 'counts', counts
##        countsPerCall = 10
##        values = []
##        for i in range(0, counts, countsPerCall): # count + 1 ??
##            valBlock = eseMtpr.Call('bmbd? '+ str(i))   # liefert einen String mit max. 10 values ab offset
##            valStrings = valBlock.split(' ')            # values werden separiert
##            for valString in valStrings:
##                val = float(valString)
##                if val > 4000:                          # THRESHOLD
##                    val = -1                            # > 4000 == Ueberlauf
##                values.append(val)
##                #values.extend(val)      
##
##        print '*' * 40
##
##                
##        #print values
##        for v in values:
##            print v
##        #print eseMtpr.Call('bmbd? '+ str(0))   # Started mit 0


    if 1 == 0:
        #Test Scopemodus


        ##    Scope modus:
        ##
        ##    br 1 - board remote, umd ein zweites ok nach methodenstart zu bekommen
        ##    bmm <n> - setze methode 12=scope A1E1, 13=scope E1D2, 14=scope E2D2
        ##    bms - starte methode, wenn br 1 dann kommt ein ok fuer den befehl und ein  ok fuer das ende der messung
        ##    bmas <n> - scope average 1-250, bestimmt wieviele punkte zu einem zusammengefasst werden
        ##    die beteutet die messung wird laenger
        ##    bmbd? <n> - liefert bis zu 10 messwerten, n=index des ersten datenpunktes(0-1490)
        ##
        ##    beispiel:
        ##    bmbd? 1490
        ##    4875.133057 4874.264160 4874.100830 4873.100586 4872.441895 4872.410400 4871.584
        ##    961 4870.784424 4870.648438 4869.903320
        ##
        ##    Anmerkung:
        ##    um alle daten der scope methode abzufragen muss der index des bmbd? befehls erhoeht werden.

# nicht realisiert
##        print eseMtpr.Call('bmbf?')     # abtastfrequenz
##        print eseMtpr.Call('bmbf 10')   # abtastfrequenz    3000 error
##        print eseMtpr.Call('bmbf?')     # abtastfrequenz

        ## New nach Telefonat:
        ## Abtastfrequenz gibt es zwar in der Befehlsliste ist aber nicht realisiert.
        ## Geschwindigkeit geht z.Zt. nur ueber Averige (bmas) 0- 250
        ## bei Av 1 ca. 0.7 sec fuer alle Werte
        ## bei aver > .. wird punkt zu Strich ;-)

        ## returnwerte: ueberlauffunction ist deactiviert  > 4096 ist Schwachsinn
        ## laut Wiest 4V == 4000 nimmt er als Schwelle


        eseMtpr = ESE_MTPR()
        eseMtpr.myInit(port = 7)

        tStart = time.clock()
        
        eseMtpr.MoveXY( 0, 5, mode = "ABSOLUTE")
        eseMtpr.MoveXY( 60, 5, mode = "ABSOLUTE")
        
        print 'time (move x):', time.clock() - tStart

        print eseMtpr.Call('srd')       # delete all records
        print eseMtpr.Call('br 1')      # board remote, umd ein zweites ok nach methodenstart zu bekommen
        print eseMtpr.Call('bmm 13')    # bmm <n> - setze methode 12=scope A1E1, 13=scope E1D2, 14=scope E2D2
                                        #13 lt. fl a1e2 scope
        # es geht nur 13 sonst error
        print eseMtpr.Call('bmas?')     # scope average 1-250, bestimmt wieviele punkte zu einem zusammengefasst werden
        print eseMtpr.Call('bmas 3')  # 98,5 sec (incl. predel - 250) 3 sec (incl. predel - 1) 
        print eseMtpr.Call('bmas?')

        #print eseMtpr.Call('bmm 13')    # bmm <n> - setze methode 12=scope A1E1, 13=scope E1D2, 14=scope E2D2


        
        tStart = time.clock()
        print eseMtpr.Call('bms')       # starte methode, wenn br 1 dann kommt ein ok fuer den befehl und ein  ok fuer das ende der messung
        ## warte ! auf 2. O.K.
        #for i = 1 to .. len(..)
        #while int(self.Call('bs?')) <> 0:  # ?? bs oder direkt auf ok warten?

        if eseMtpr.readEx() == 'O.K.':
            print 'time (scope):', time.clock() - tStart
            
        #get scan results
        counts = int(eseMtpr.Call('bmbr?'))
        print 'counts', counts
        countsPerCall = 10
        values = []
        for i in range(0, counts, countsPerCall): # count + 1 ??
            valBlock = eseMtpr.Call('bmbd? '+ str(i))   # liefert einen String mit max. 10 values ab offset
            valStrings = valBlock.split(' ')            # values werden separiert
            for valString in valStrings:
                val = float(valString)
                if val > 4000:                          # THRESHOLD
                    val = -1                            # > 4000 == Ueberlauf
                values.append(val)
                #values.extend(val)      

        print '*' * 40

                
        #print values
        for v in values:
            print v


        



        #print eseMtpr.Call('bmbd? '+ str(0))   # Started mit 0

    if 1 == 0:
        #diese funktion ist fuer das positionieren wichtig
        eseMtpr = ESE_MTPR()
        eseMtpr.myInit(port = 7)
        print 'test', eseMtpr.Call('fl1?')  #Licht an
        print eseMtpr.Call('fl1 1')  #Licht an
        time.sleep(10)
        print eseMtpr.Call('fl1 0')  #Licht aus


    if 1 == 0: # test der "neuen Classen"   !
        eseMtpr = ESE_MTPR()
        eseMtpr.myInit(port = 7)

        ##        print eseMtpr.Call('po')
        ##        print eseMtpr.Call('pc')

        #err: -> 0OK
        print 'se?', eseMtpr.Call('se?')

        eseMtpr.Eject('OPEN')       #wird automatisch geschlossen
        #eseMtpr.Eject('CLOSE')
        
        for i in range(10):
            eseMtpr.MoveXY(0,0)
            eseMtpr.MoveXY(30,30)
            eseMtpr.lala()  #ESE_FLLOG  -> messung ausfuehren

    if 1 == 0:
        # --
##        print eseMtpr.Call('po')
##        print eseMtpr.Call('pc')

        STEPSIZE = 0.0125

        import time

        if 1 == 0:

            print 'pr' , eseMtpr.Call('pr')
            print eseMtpr.Call('pi')
            print 'pv?' , eseMtpr.Call('pv?')   #Error
            print 'pv?' , eseMtpr.Call('pv?')
            time.sleep(30)
            print 'pi' , eseMtpr.Call('pi') # erstes geht immer schief (nach reset) .. nee warten !
##            print 'pi' , eseMtpr.Call('pi')

            print 'ps?' , eseMtpr.Call('ps?')
            print 'pv?' , eseMtpr.Call('pv?')

            for i in range(3):
                print eseMtpr.Call('px 0.0')
                print eseMtpr.Call('py 15.0')
                print eseMtpr.Call('pg')
                
                while int(eseMtpr.Call('ps?')) <> 0:
                    pass # vs. sleep
                    #print 'nicht fertig'

                print eseMtpr.Call('px 35.0')
                print eseMtpr.Call('py 10.0')
                print eseMtpr.Call('pg')
                while int(eseMtpr.Call('ps?')) <> 0:
                    print 'nicht fertig 2'

            print 'se?', eseMtpr.Call('se?')    # ESMO10-MB-4019 OSN0074    Flu Log geht ueber gleichen port !
                
##          # LOK ??
##        ##====================
##        ##XOK
##        ##
##        ##--------------------
##        ##YOK
##        ##
##        ##--------------------
##        ##OOK


        if 1 == 1:
            def ModalGo(): # TBD x,y
                print eseMtpr.Call('pg')
                while int(eseMtpr.Call('ps?')) <> 0:
                    pass # vs. sleep
                    #print 'nicht fertig'

##            print 'pr' , eseMtpr.Call('pr')
##            print eseMtpr.Call('pi')
##            print 'pv?' , eseMtpr.Call('pv?')   #Error
##            print 'pv?' , eseMtpr.Call('pv?')
##            #time.sleep(30)
            print 'pi' , eseMtpr.Call('pi') # erstes geht immer schief (nach reset) .. nee warten !
##            print 'pi' , eseMtpr.Call('pi')

            print 'ps?' , eseMtpr.Call('ps?')
            print 'pv?' , eseMtpr.Call('pv?')            


            for i in range(3):
                print eseMtpr.Call('px 0.0')
                print eseMtpr.Call('py 15.0')
                ModalGo()

                print eseMtpr.Call('px 35.0')
                print eseMtpr.Call('py 10.0')
                ModalGo()


##start
##ps? 10.000000
##
##py? 15.000000
##
##px? 10.000000
##
##py? 15.000000
##
##px? 10.000000
##
##py? 0
##
##px? 15.000000

    print "fine"


