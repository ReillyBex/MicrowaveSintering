import gpiozero
import os
import tkinter as tk
import csv
import time
from numpy import interp
from tkinter import ttk
from tkinter import *
from tkinter.messagebox import showinfo

class MSIO(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Micro Sinter IO')
        self.geometry("800x460")

        # define the variables needed by the class and set default values
        # variables used by widgets
        self.targetTemp = tk.StringVar()
        self.holdTime = tk.StringVar()
        self.materials = tk.StringVar()
        self.selectedMaterial = tk.StringVar()
        self.loadedPresets = tk.StringVar()
        self.selectedPreset = tk.StringVar()
        self.devCycle = tk.StringVar()
        self.devTime = tk.StringVar()
        # variables used to check conditions
        self.writeFlag = BooleanVar(value=False)
        self.processRunning = BooleanVar(value=False)
        # variables used in the control loop
        self.dutyCycle = 0
        self.rampTime = 0
        self.processTemp = 0
        self.processTime =0
        self.PWM = gpiozero.PWMLED(13, frequency=60)
        self.controlState = 0 # 0 for not running, 1 for ramping, 2 for holding
        self.nextState = 0 # used to switch between ramp, hold, and off
        self.debug = True # turns on or off debug print outs
        self.startTime = 0
        # variables used in open loop scaffolding
        self.error = 0
        self.lastError = 0
        self.kp = 1
        self.kd = 1
        self.ki = 1
        self.pidTimer = 0
        # create a file path to the presets in the current directory
        self.currentDirectory = os.getcwd()
        self.presetFilePath = self.currentDirectory + '/presetParams.txt'
        self.materialsDirectory = self.currentDirectory + '/materials'

        # set up the app grid to be 3 x 5
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)

        # set up the padding between widgets
        self.padding = {'padx': 5, 'pady': 5}

        # check if the preset file exists, create the file if not
        if os.path.exists(self.presetFilePath):
            #do nothing to it for now
            pass
        else:
            #create the file
            with open(self.presetFilePath, 'w') as self.preset:
                self.preset.write("Target Temp, Hold Time, Material \n")
            showinfo(message="No presets exist. Empty file created")

        # check to see if the materials folder exists, create it if not
        if os.path.exists(self.materialsDirectory):
                #do nothing to it
                pass
        else:
                # create the directory
                os.mkdir(self.materialsDirectory)
                showinfo(message='Materials directory not present. Please add material profiles to new directory.')

        # create the primary widgets
        self.createWidgets()

        # start the control loop in the background
        self.controlLoop()

    def createWidgets(self):

        # define the 5 buttons
        Button(self, text="Save", command=self.saveEntryPrompt, bg='blue', fg='#fff').grid(column=1, row=3, **self.padding)
        Button(self, text="Load Preset", command=self.loadEntryPopup, bg='blue', fg='#fff').grid(column=1, row=4, **self.padding)
        Button(self, text="Run", command=self.confirmProcess, bg='green').grid(column=0, row=3, **self.padding)
        Button(self, text="Abort", command=self.abortProcess, bg='red').grid(column=0, row=4, **self.padding)
        Button(self, text="Close GUI", command=self.closeApp).grid(column=2, row=3, **self.padding)
        Button(self, text="Run Dev Process", command=self.runDevEntry).grid(column=2, row=4, **self.padding)

        # define the 2 text entry fields
        ttk.Label(self, text="Target Temperature:").grid(column=0, row=0, sticky=E, **self.padding)
        tempEntry = ttk.Entry(self, textvariable=self.targetTemp).grid(column=1, row=0, sticky=E, **self.padding)
        ttk.Label(self, text="Degrees Celcius").grid(column=2, row=0, sticky=W, **self.padding)

        ttk.Label(self, text="Hold Time:").grid(column=0, row=1, sticky=E, **self.padding)
        timeEntry = ttk.Entry(self, textvariable=self.holdTime).grid(column=1, row=1, sticky=E, **self.padding)
        ttk.Label(self, text="Minutes").grid(column=2, row=1, sticky=W, **self.padding)

        # define the list box and scroll arrows
        materialScroll = ttk.Scrollbar(self)
        ttk.Label(self, text="Material").grid(column=0, row=2, sticky=E, **self.padding)
        self.materialList = tk.Listbox(self, yscrollcommand = materialScroll.set, listvariable=self.materials, selectmode=tk.SINGLE, height=3)
        # read in the materials from the folder
        self.materials = os.listdir(self.materialsDirectory)
        if self.debug:
                print('materials are: ')
                print(self.materials)
        i = 0
        for item in self.materials:
                self.materialList.insert(i, item)
                i += 1
        # configure list and scroll bar in window
        self.materialList.grid(column=1, row=2, sticky=tk.NS, **self.padding)
        materialScroll.config( command = self.materialList.yview)
        materialScroll.grid(column=2, row=2, sticky=tk.NS, **self.padding)

        # bind events and callbacks for main widgets
        self.materialList.bind('<<ListboxSelect>>', self.materialSelect)

    def saveEntryPrompt(self):
        # display a top level with the current values
        self.savePrompt = tk.Toplevel(self)
        self.savePrompt.geometry("300x200")
        self.savePrompt.columnconfigure(0, weight=1)
        self.savePrompt.title('Save these settings?')

        # generate setting strings and display them
        text1 = "Hold Temp: " + self.targetTemp.get() + " Degrees Celcius"
        text2 = "Hold time: " + self.holdTime.get() + " Minutes"
        text3 = "Material: " + self.selectedMaterial.get()
        ttk.Label(self.savePrompt, text=text1).grid(row=0, **self.padding)
        ttk.Label(self.savePrompt, text=text2).grid(row=1, **self.padding)
        ttk.Label(self.savePrompt, text=text3).grid(row=2, **self.padding)

        # prompt user for confirmation
        Button(self.savePrompt, text="Save?", command=self.saveEntryFields, bg='green').grid(row=3, **self.padding)
        Button(self.savePrompt, text="Cancel", command=self.cancelSave, bg='red').grid(row=4, **self.padding)

    def loadEntryPopup(self):
        # open a popup
        self.loadPrompt = tk.Toplevel(self)
        self.loadPrompt.geometry("300x200")
        self.loadPrompt.title('Saved Presets')

        # define the list box and scroll arrows
        presetScroll = ttk.Scrollbar(self.loadPrompt, orient='vertical')
        self.presetList = tk.Listbox(self.loadPrompt, yscrollcommand = presetScroll.set, listvariable=self.loadedPresets, selectmode=tk.SINGLE, height=6, width=30)

        # read in the presets from the file
        with open(self.presetFilePath, 'r') as self.preset:
            i = 1
            for line in self.preset:
                self.presetList.insert(i, line)
                i += 1

        # configure the widgets in the popup
        self.presetList.grid(row=0, column=0, sticky=tk.NS, **self.padding)
        presetScroll.config(command = self.presetList.yview)
        presetScroll.grid(row=0, column=1, sticky=tk.NS, **self.padding)

        # bind events and callbacks for the popup
        self.presetList.bind('<<ListboxSelect>>', self.presetSelect)
        Button(self.loadPrompt, text='Load Preset', command=self.loadEntryFields).grid(row=1, column=0, **self.padding)

    def loadEntryFields(self):
        # load in the preset parameters and split to elements
        params = self.selectedPreset.get()
        params = params.split(',')

        # assign elements to correct variables
        self.targetTemp.set(params[0])
        self.holdTime.set(params[1])
        self.selectedMaterial.set(params[2].strip("\n"))

        # clear the list and destroy the popup
        self.presetList.delete(0,END)
        self.loadPrompt.destroy()

    def saveEntryFields(self):
        # check to make sure fields are valid
        if self.validateParams() == False:
            self.savePrompt.destroy()
        else:
            # generate an entry
            entry = self.targetTemp.get() + "," + self.holdTime.get() + "," + self.selectedMaterial.get() + "\n"
            if self.debug == True:
                print(entry)

            # read the file
            with open(self.presetFilePath, 'r') as self.preset:
                # ensure the preset doesn't already exist
                for line in self.preset:
                    if line == entry:
                        self.writeFlag = False
                        break
                    else:
                        self.writeFlag = True

            # rite the entry if it doesn't exist already
            if self.writeFlag == True:
                    with open(self.presetFilePath, 'a') as self.preset:
                        self.preset.write(entry)
            else:
                showinfo(message="Preset already exists.")

            # kill the prompt window
            self.savePrompt.destroy()

    def runProcess(self):
        # ensure a process is not already running
        if self.processRunning == True:
            showinfo(message="A process is already running! Wait for process to finish or abort the current process to run another.")
            self.runPrompt.destroy()

        else:
            # check to make sure fields are valid
            if self.validateParams() == False:
                self.runPrompt.destroy()
            else:
                # get rid of the prompt
                self.runPrompt.destroy()
                # let the user know the process has begun
                showinfo(message="Process will begin when this window is closed. Be cautious of hot materials!")
                # convert the user inputs to floats
                self.processTemp = float(self.targetTemp.get())
                self.processTime = float(self.holdTime.get())
                # look up how long to run at full power
                self.rampTime = self.lookUpRampTime(self.processTemp, self.selectedMaterial.get())
                # look up what duty cycle to hold at
                self.dutyCycle = self.lookUpDutyCycle(self.processTemp, self.selectedMaterial.get())
                #check to see that duty cycle completed successfully
                if self.dutyCycle == 0:
                        # if we haven't found an acceptable duty cycle, let the user know the parameters are invalid
                        showinfo(message='Unable to find a duty cycle that matches the tolerance specified. Please adjust the hold temp or material profile')
                else:
                        if self.debug:
                                print('process duty cycle and ramp time: ', self.dutyCycle, self.rampTime)
                        # change the run flag to True
                        self.processRunning = True
                        # begin the control loop
                        self.controlLoop()

    def runDev(self):
        # ensure a process is not already running
        if self.processRunning == True:
            showinfo(message="A process is already running! Wait for process to finish or abort the current process to run another.")
            self.runPrompt.destroy()
        else:
            # get rid of the prompt
            self.runDevPrompt.destroy()
            # let the user know the process has begun
            showinfo(message="Process will begin when this window is closed. Be cautious of hot materials!")
            # convert the user inputs to floats
            self.dutyCycle = float(self.devCycle.get()) / 100
            self.processTime = float(self.devTime.get())
            if self.debug == True:
                print(self.dutyCycle)
                print(self.processTime)
            self.nextState = 2
            # change the run flag to True
            self.processRunning = True
            # begin the control loop
            self.controlLoop()
            
    def runDevEntry(self):
        # open a popup
        self.runDevPrompt = tk.Toplevel(self)
        self.runDevPrompt.geometry("350x200")
        self.runDevPrompt.title('Run Development Process')
        # define the 2 text entry fields
        ttk.Label(self.runDevPrompt, text="Duty Cycle: ").grid(column=0, row=0, sticky=E, **self.padding)
        tempEntry = ttk.Entry(self.runDevPrompt, textvariable=self.devCycle).grid(column=1, row=0, sticky=E, **self.padding)
        ttk.Label(self.runDevPrompt, text="percent").grid(column=2, row=0, sticky=W, **self.padding)

        ttk.Label(self.runDevPrompt, text="Hold Time:").grid(column=0, row=1, sticky=E, **self.padding)
        timeEntry = ttk.Entry(self.runDevPrompt, textvariable=self.devTime).grid(column=1, row=1, sticky=E, **self.padding)
        ttk.Label(self.runDevPrompt, text="Minutes").grid(column=2, row=1, sticky=W, **self.padding)
        
        # prompt user for confirmation
        Button(self.runDevPrompt, text="Run?", command=self.runDev, bg='green').grid(column = 1, row=3, **self.padding)
        Button(self.runDevPrompt, text="Cancel", command=self.cancelDev, bg='red').grid(column = 1, row=4, **self.padding)
        
    def cancelDev(self):
        self.runDevPrompt.destroy()
        
    def abortProcess(self):
        # send a stop signal to the microwave
        self.PWM.off()
        self.dutyCycle = 0.0

        # set the run flag to False
        self.processRunning = False

        # display a message about closing the app
        self.abortPopup = tk.Toplevel(self)
        self.abortPopup.columnconfigure(0, weight=1)
        ttk.Label(self.abortPopup, text="The process was aborted. Be cautious of potentially hot materials!").grid(row=0, **self.padding)
        Button(self.abortPopup, text="Return to GUI", command=self.confirmAbort).grid(row=1, **self.padding)

    def materialSelect(self, event):
        # determine what entry from the list the user picked
        selectIndicies = self.materialList.curselection()
        inputMaterial = ",".join([self.materialList.get(i) for i in selectIndicies])

        # assign the material variable from the list entry
        self.selectedMaterial.set(inputMaterial)

    def presetSelect(self, event):
        # determine which preset from the list the user picked
        selectIndicies = self.presetList.curselection()
        inputPreset = "\n".join([self.presetList.get(i) for i in selectIndicies])

        # assign the selected preset from the list entry
        self.selectedPreset.set(inputPreset)

    def confirmProcess(self):
        # display a top level that displays the current values
        self.runPrompt = tk.Toplevel(self)
        self.runPrompt.geometry("300x200")
        self.runPrompt.columnconfigure(0, weight=1)
        self.runPrompt.title('Confirm Process Parameters')
        text1 = "Hold Temp: " + self.targetTemp.get() + " Degrees Celcius"
        text2 = "Hold time: " + self.holdTime.get() + " Minutes"
        text3 = "Material: " + self.selectedMaterial.get()
        ttk.Label(self.runPrompt, text=text1).grid(row=0, **self.padding)
        ttk.Label(self.runPrompt, text=text2).grid(row=1, **self.padding)
        ttk.Label(self.runPrompt, text=text3).grid(row=2, **self.padding)
        Button(self.runPrompt, text="Run Process?", command=self.runProcess, bg='green').grid(row=3, **self.padding)
        Button(self.runPrompt, text="Cancel", command=self.cancelRun, bg='red').grid(row=4, **self.padding)

    def confirmAbort(self):
        self.abortPopup.destroy()

    def validateParams(self):
        # check to make sure fields aren't left empty or incorrectly populated
        # check that the material is from our list of known materials
        for item in self.materials:
                if self.debug:
                        print(self.selectedMaterial.get())
                        print(item)
                if self.selectedMaterial.get() == item:
                        materialExists = True
                        break
                else:
                        materialExists = False
        # target temp checks
        if self.targetTemp.get() == '' or self.targetTemp.get() == 'Target Temp':
            showinfo(message="Temperature field must be populated")
            # return false
            return False
        elif not self.targetTemp.get().isnumeric():
            showinfo(message="Temperature entry must be a number")
            return False
        # hold time checks
        elif self.holdTime.get() == '' or self.holdTime.get() == ' Hold Time':
            showinfo(message="Time field must be populated")
            # return false
            return False
        elif not self.holdTime.get().isnumeric():
            showinfo(message="Time entry must be a number")
            return False
        elif self.holdTime.get() == '0':
                showinfo(message="Time entry may not be 0")
                return False
        # material checks
        elif self.selectedMaterial.get() == '' or self.selectedMaterial.get() == ' Material \n':
            showinfo(message="A material must be selected")
            # return false
            return False
        elif materialExists == False:
                showinfo(message='Material not in list of accepted options. Double check your preset parameters.')
                return False
        else:
            # return True only if all other checks pass
            return True



    def cancelRun(self):
        self.runPrompt.destroy()

    def cancelSave(self):
        self.savePrompt.destroy()

    def closeApp(self):
        # send a stop signal to the microwave
        self.PWM.off()
        self.dutyCycle = 0.0
        # display a message about closing the app
        self.closePopup = tk.Toplevel(self)
        self.closePopup.columnconfigure(0, weight=1)
        ttk.Label(self.closePopup, text="GUI will exit now. Be cautious of potentially hot materials!").grid(row=0, **self.padding)
        Button(self.closePopup, text="Close the GUI", command=self.killApp).grid(row=1, **self.padding)

    def lookUpRampTime(self, temp, material):
        rampTime = 0
        # read the file
        with open(os.path.join(self.materialsDirectory, material), newline='', encoding='utf-8') as materialFile:
                # do stuff to the data
                #if self.debug:
                        #for line in materialFile:
                                #print(line)
                
                lookUpTable = csv.reader(materialFile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                lineCount = 0
                for row in lookUpTable:
                        # the first line contains info about how the data is organized
                        if lineCount == 0:
                                dutyStep = row[0]
                                timeStep = row[1]
                                tol = row[2]
                                lineCount += 1
                                if self.debug:
                                        print('duty cycle, time step, tolerance')
                                        print(dutyStep, timeStep, tol)
                        # the next line is the 100% duty cycle line so we need to use it
                        else:
                                readingCount = 1
                                # look at each temperature in the row, keeping track of the number of temperatures we have looked at to back out time
                                for reading in row:
                                        # if our desired temperature is exactly equal to the temperature we are on
                                        if reading == temp:
                                                rampTime = readingCount * timeStep
                                                return rampTime
                                        # if our reading is above the temperature we desire
                                        elif reading >= temp:
                                                # linearly interpolate the ramp time
                                                thisTime = readingCount * timeStep
                                                lastTime = thisTime - timeStep
                                                thisTemp = reading
                                                lastTemp = row[readingCount - 2]
                                                rampTime = lastTime + ((temp - lastTemp) * (thisTime - lastTime) / (thisTemp - lastTemp))
                                                return rampTime
                                        # otherwise check the next reading
                                        else:
                                                readingCount +=1

    def lookUpDutyCycle(self, temp, material):
        dutyCycle = 0
        # read the file
        with open(os.path.join(self.materialsDirectory, material), newline='', encoding='utf-8') as materialFile:
                # do stuff to the data
                lookUpTable = csv.reader(materialFile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                lineCount = 0
                tempArray = []
                for row in lookUpTable:
                        # the first line contains info about how the data is organized
                        if lineCount == 0:
                                dutyStep = row[0]
                                timeStep = row[1]
                                tol = row[2]
                                lineCount += 1
                                if self.debug:
                                        print('duty cycle, time step, tolerance')
                                        print(dutyStep, timeStep, tol)
                        # the next lines contain the temperature data
                        else:
                                #we assume that the last item in the row is the steady state temp
                                tempArray.append(row[-1])
                                lineCount += 1
                # now that we have a steady state temp list, find where our desired temp is within tolerance
                i = 0
                for temps in tempArray:
                        # if the desired temp is within the reading
                        if temps <= temp + tol and temps >= temp - tol:
                                dutyCycle = 1 - (i*dutyStep/100)
                                return dutyCycle
                        i += 1
                # if our for loop didn't find an acceptable duty cycle, return 0 so nothing will turn on
                return 0

    def eventCheck(self):
        # switch case statements
        if self.controlState == 0:
                # if the process run flag is set to true when this is checked, transition to state 1
                if self.processRunning == True:
                        self.nextState = 1
                else:
                        self.nextState = 0
        elif self.controlState == 1:
                if self.processRunning == False:
                        # the abort process button has been pushed and we need to stop
                        self.nextState = 0
                # check time
                elif self.currentTime() <= self.rampTime * 60:
                        # timer has not expired, still ramping
                        self.nextState = 1
                else:
                        # switch to holding
                        self.nextState = 2
        elif self.controlState == 2:
                if self.processRunning == False:
                        # the abort process button has been pushed and we need to stop
                        self.nextState = 0
                elif self.currentTime() <= self.processTime * 60:
                        # timer has not expired, still holding
                        self.nextState = 2
                else:
                        # switch to off
                        self.nextState = 0

    def eventService(self):
        if self.controlState == 0:
            if self.nextState == 1:
                self.PWM.value = 1
                self.startTime = time.monotonic()
                #self.pidTimer = time.monotonic()
            elif self.nextState == 0:
                # we don't need to do anything for this
                pass
            elif self.nextState == 2:
                # this is directly to the dev loop
                self.PWM.value = self.dutyCycle
                self.startTime = time.monotonic()
        elif self.controlState == 1:
            if self.nextState == 1:
                # looping back to continue ramping
                pass
            elif self.nextState == 2:
                # switching to hold temp
                self.PWM.value = self.dutyCycle
            elif self.nextState == 0:
                # process is aborted, turn things off
                self.dutyCycle = 0
                self.PWM.value = 0
        elif self.controlState == 2:
            if self.nextState == 2:
                # looping back to continue holding
                #self.closeLoopControl()
                #self.pwm.value = self.dutyCycle
                pass
            elif self.nextState == 0:
                # process is over, turn things off
                self.dutyCycle = 0
                self.PWM.value = 0
                # set the flag back to false so we can start another process
                self.processRunning = False
        self.controlState = self.nextState

    def controlLoop(self):
        self.eventCheck()
        if self.debug == True:
            print('control loop active')
            print(self.controlState)
            print(self.nextState)
            print('\n')
        self.eventService()
        self.after(1000, self.controlLoop)

    def currentTime(self):
        if self.debug:
            print("current time is: " + str(time.monotonic()-self.startTime) + " seconds")
        return time.monotonic() - self.startTime

    def killApp(self):
        self.destroy()

    def debugFunc(self):
        print(self.lookUpRampTime(1200, 'hydroxyappatite.csv'))
        print(self.lookUpDutyCycle(1250, 'hydroxyappatite.csv'))
    
    def closeLoopControl(self):
        # establish interation parameters
        self.error = self.processTemp - getTemp()
        dt = time.monotonic() - self.pidTimer
        prop = self.error
        integral = integral + (self.error * dt)
        derivative = (self.error - self.lastError) / dt
        # perform output calculation
        self.dutyCycle = (self.kp * prop) + (self.kd * derivative) + (self.ki * integral)
        # replace iteration terms for next cycle
        self.pidTimer = time.monotonic()
        self.lastError = self.error
        # limit output value
        if self.dutyCycle > 1:
                self.dutyCycle = 1
        if self.dutyCycle < 0:
                self.dutyCycle = 0
        
    def getTemp(self):
        # do stuff with some sensor to get the real time temp of the sample
        return 0
            
#run the app
if __name__ == "__main__":
    app = MSIO()
    app.mainloop()
