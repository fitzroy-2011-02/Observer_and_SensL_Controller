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
definiert. 
            Aber wenn du das liest dann wirst du das lesen kannst 
            wirst du auch die Parameter finden.

"""

#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import hwConnection
from Tkinter import *
import time

class App:

    def __init__(self, master):

        # ----------------------------------------------------------
        # PARAMETER INIT VALUES
        # ----------------------------------------------------------
        # com port number
        self.mikCOMport = 0
        # velocity of movement mm/s
        self.mikVel = 5
        # distance to move um
        self.mikDist = 1000
        # number of cycle we want to move pace around
        self.mikCycles = 1
        # direction we want to move ( 0=horizontal, 1=vertical)
        self.mikDirection = 0
        #-----------------------------------------------------------

        # ----------------------------------------------------------
        # GUI
        # ----------------------------------------------------------
        frame = Frame(master)

        # function we use to check the enty values
        vcmd = (frame.register(self.OnValidate), 
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        # connect to the COM 1 port
        self.butConnect = Button(master, text="CONNECT", bg="red", fg="white", command=self.connect)
        self.butConnect.grid(row=0, columnspan=2, stick=W+E)

        # set parameters
        Label(master, text="Velocity [mm/s]", bg="white").grid(row=1, column=0, stick=W+E)
        self.entryVel = Entry(master, validate="key", validatecommand=vcmd)
        self.entryVel.insert(END, self.mikVel)
        self.entryVel.grid(row=1, column=1)
        
        Label(master, text="Distance [um]").grid(row=2, column=0, stick=W+E)
        self.entryDist = Entry(master, validate="key", validatecommand=vcmd)
        self.entryDist.insert(END, self.mikDist)
        self.entryDist.grid(row=2, column=1)
        
        Label(master, text="Cycles", bg="white").grid(row=3, column=0, stick=W+E)
        self.entryCycle = Entry(master, validate="key", validatecommand=vcmd)
        self.entryCycle.insert(END, self.mikCycles)
        self.entryCycle.grid(row=3, column=1)

        Label(master, text="Direction").grid(row=4, column=0, stick=W+E)
        self.listDirection = Listbox(master, height=2)
        self.listDirection.insert( END, "horizontal")
        self.listDirection.insert( END, "vertikal")
        self.listDirection.grid(row=4, column=1)
        self.listDirection.selection_set(self.mikDirection)

        # start process
        self.butStart = Button(master, text="START", bg="black", fg="white", command=self.startProcess)
        self.butStart.grid(row=5, column=0, stick=W+E)

        # stop process
        self.butStop = Button(master, text="STOP", bg="white", fg="black", command=self.stopProcess)
        self.butStop.grid(row=5, column=1, stick=W+E)

        # ----------------------------------------------------------

    def connect(self):
        self.observerDevice = hwConnection.Serial_Observer()
        rtv = self.observerDevice.myInit( port = int(self.mikCOMport) )
        # we will get a empty string is no device is connected to the given COM Port
        if rtv != "":
            self.butConnect.configure(bg="green")
            return 1
        else:
            self.butConnect.configure(bg="red")
            return 1

    def startProcess(self):
        if self.butConnect.cget("bg") == "green":
            
            # _______________first get current velocity
            oriVelCall = "S X? Y?"
            #oriVel = self.observerDevice.Call(oriVelCall)
            # return something like ":A X=7.5 Y=7.5"

            # _______________set new velocity
            newVelCall = "S X=" + self.entryVel.get() + " Y=" + self.entryVel.get()
            #self.observerDevice.Call(newVelCall)

            # _______________now get move call together
            # convert to micro meter 
            moveDist = str( int(self.entryDist.get()) * 10)
            # get direction ( 0=horizontal, 1=vertical)
            if self.listDirection.curselection()[0] == "0":
                directionString = "X="
            else:
                directionString = "Y="
            
            moveFinish = 0

            for i in xrange(int(self.entryCycle.get())):
                # change direction each time
                vorzeichen = str((-1)**i)[0:-1]
                moveCall = "R " + directionString + vorzeichen + moveDist
                #print moveCall
                #self.observerDevice.Call(moveCall)
                while moveFinish == 0:
                    time.sleep(0.1)
                    moveStatus = self.observerDevice.Call("STATUS")
                    if moveStatus == "N":
                        moveFinish == 1
            
            # reset velocity
            resetVelCall = oriVel[2:]
            resetVelCall = "S" + resetVelCall
            #self.observerDevice.Call(resetVelCall)

        return 1

    def stopProcess(self):
        self.observerDevice.Call("HALT")
        return 1

    def OnValidate(self, d, i, P, s, S, v, V, W):
        
        # valid percent substitutions (from the Tk entry man page)
        # %d = Type of action (1=insert, 0=delete, -1 for others)
        # %i = index of char string to be inserted/deleted, or -1
        # %P = value of the entry if the edit is allowed
        # %s = value of entry prior to editing
        # %S = the text string being inserted or deleted, if any
        # %v = the type of validation that is currently set
        # %V = the type of validation that triggered the callback
        #      (key, focusin, focusout, forced)
        # %W = the tk name of the widget
        """
        print "OnValidate:"
        print "d='%s'" % d
        print "i='%s'" % i
        print "P='%s'" % P
        print "s='%s'" % s
        print "S='%s'" % S
        print "v='%s'" % v
        print "V='%s'" % V
        print "W='%s'" % W
        """

        res = 0
        # depending on the entry type we set the validator
        if W == str(self.entryVel):
            # float number is allowed
            if S.isdigit() or S == ".":
                res = 1

        elif W == str(self.entryDist) or W == str(self.entryCycle):
            # int number is allowed
            if S.isdigit():
                res = 1

        return (res)


root = Tk()

app = App(root)

root.mainloop()

