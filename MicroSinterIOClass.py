import gpiozero
import os
import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter.messagebox import showinfo

class MSIO(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Micro Sinter IO')
        self.geometry("500x400")
        
        # define the variables needed by the class and set default values
        self.targetTemp = tk.StringVar()
        self.holdTime = tk.StringVar()
        self.materials = tk.StringVar()
        self.selectedMaterial = tk.StringVar()
        self.writeFlag = False
        self.processRunning = False
        self.loadedPresets = tk.StringVar()
        self.selectedPreset = tk.StringVar()
        # create a file path to the presets in the current directory
        self.filePath = os.getcwd()
        self.filePath = self.filePath + '/presetParams.txt'
        
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

        # create the primary widgets
        self.createWidgets()
        
        # check if the preset file exists, create the file if not
        if os.path.exists(self.filePath):
            #do nothing to it for now
            pass 
        else:
            #create the file
            with open(self.filePath, 'w') as self.preset:
                self.preset.write("Target Temp, Hold Time, Material \n")
            showinfo(message="No presets exist. Empty file created")            
        
    def createWidgets(self):
        # define the 5 buttons
        ttk.Button(self, text="Save", command=self.saveEntryPrompt).grid(column=0, row=3, sticky=S, **self.padding)
        ttk.Button(self, text="Load Preset", command=self.loadEntryPopup).grid(column=1, row=3, sticky=S, **self.padding)
        ttk.Button(self, text="Run", command=self.confirmProcess).grid(column=0, row=4, sticky=S, **self.padding)
        ttk.Button(self, text="Abort", command=self.abortProcess).grid(column=1, row=4, sticky=S, **self.padding)
        ttk.Button(self, text="Close GUI", command=self.closeApp).grid(column=2, row=3, sticky=S, **self.padding)

        # define the 2 text entry fields
        ttk.Label(self, text="Target Temperature:").grid(column=0, row=0, sticky=E, **self.padding)
        tempEntry = ttk.Entry(self, textvariable=self.targetTemp).grid(column=1, row=0, sticky=E, **self.padding)
        ttk.Label(self, text="Degrees Celcius").grid(column=2, row=0, sticky=W, **self.padding)

        ttk.Label(self, text="Hold Time:").grid(column=0, row=1, sticky=E, **self.padding)
        timeEntry = ttk.Entry(self, textvariable=self.holdTime).grid(column=1, row=1, sticky=E, **self.padding)
        ttk.Label(self, text="Hours").grid(column=2, row=1, sticky=W, **self.padding)

        # define the list box and scroll arrows
        materialScroll = ttk.Scrollbar(self)
        ttk.Label(self, text="Material").grid(column=0, row=2, sticky=E, **self.padding)
        self.materialList = tk.Listbox(self, yscrollcommand = materialScroll.set, listvariable=self.materials, selectmode=tk.SINGLE, height=3)
        self.materialList.insert(1, "Tony's material")
        self.materialList.insert(2, "dummy material")
        
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
        text2 = "Hold time: " + self.holdTime.get() + " Hours"
        text3 = "Material: " + self.selectedMaterial.get()
        ttk.Label(self.savePrompt, text=text1).grid(row=0, **self.padding)
        ttk.Label(self.savePrompt, text=text2).grid(row=1, **self.padding)
        ttk.Label(self.savePrompt, text=text3).grid(row=2, **self.padding)
        
        # prompt user for confirmation
        ttk.Button(self.savePrompt, text="Save?", command=self.saveEntryFields).grid(row=3, **self.padding)
    
    def loadEntryPopup(self):
        # open a popup
        self.loadPrompt = tk.Toplevel(self)
        self.loadPrompt.geometry("300x200")
        self.loadPrompt.title('Saved Presets')
        
        # define the list box and scroll arrows
        presetScroll = ttk.Scrollbar(self.loadPrompt, orient='vertical')
        self.presetList = tk.Listbox(self.loadPrompt, yscrollcommand = presetScroll.set, listvariable=self.loadedPresets, selectmode=tk.SINGLE, height=6, width=30)
        
        # read in the presets from the file
        with open(self.filePath, 'r') as self.preset:
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
        ttk.Button(self.loadPrompt, text='Load Preset', command=self.loadEntryFields).grid(row=1, column=0, **self.padding)
        
    def loadEntryFields(self):
        # load in the preset parameters and split to elements
        params = self.selectedPreset.get()
        params = params.split(',')
        
        # assign elements to correct variables
        self.targetTemp.set(params[0])
        self.holdTime.set(params[1])
        self.selectedMaterial.set(params[2])
        
        # clear the list and destroy the popup
        self.presetList.delete(0,END)
        self.loadPrompt.destroy()
        
    def saveEntryFields(self):
        # check to make sure fields aren't left empty
        if self.validateParams() == False:
            self.savePrompt.destroy()  
        else:
            # generate an entry
            entry = self.targetTemp.get() + "," + self.holdTime.get() + "," + self.selectedMaterial.get() + "\n"
        
            # read the file
            with open(self.filePath, 'r') as self.preset:
                # ensure the preset doesn't already exist
                for line in self.preset:
                    if line == entry:
                        self.writeFlag = False
                    else:
                        self.writeFlag = True
                    
            # rite the entry if it doesn't exist already        
            if self.writeFlag == True:
                    with open(self.filePath, 'a') as self.preset:
                        self.preset.write(entry)      
            else:
                showinfo(message="Preset already exists. Use the 'load preset' button") 
        
            # kill the prompt window        
            self.savePrompt.destroy()
 
    def runProcess(self):
        # ensure a process is not already running
        if self.processRunning == True:
            showinfo(message="A process is already running! Wait for process to finish or abort the current process to run another.")
            self.runPrompt.destroy()
            
        else:
            # check to make sure fields aren't left empty
            if self.validateParams() == False:
                self.runPrompt.destroy()
            else:
                # get rid of the prompt
                self.runPrompt.destroy()
                # change the run flag to True
                self.processRunning = True
                # let the user know the process has begun
                showinfo(message="Process will begin when this window is closed. Be cautious of hot materials!")
                # convert the user inputs to floats
                runTemp = float(self.targetTemp.get())
                processTime = float(self.holdTime.get())
                # insert open loop control code here
        
    def abortProcess(self): 
        # send a stop signal to the microwave
        
        # set the run flag to False
        self.processRunning = False
            
        # display a message about closing the app
        self.abortPopup = tk.Toplevel(self)
        self.abortPopup.columnconfigure(0, weight=1)
        ttk.Label(self.abortPopup, text="The process was aborted. Be cautious of potentially hot materials!").grid(row=0, **self.padding)
        ttk.Button(self.abortPopup, text="Return to GUI", command=self.confirmAbort).grid(row=1, **self.padding)
        
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
        text2 = "Hold time: " + self.holdTime.get() + " Hours"
        text3 = "Material: " + self.selectedMaterial.get()
        ttk.Label(self.runPrompt, text=text1).grid(row=0, **self.padding)
        ttk.Label(self.runPrompt, text=text2).grid(row=1, **self.padding)
        ttk.Label(self.runPrompt, text=text3).grid(row=2, **self.padding)
        ttk.Button(self.runPrompt, text="Run Process?", command=self.runProcess).grid(row=3, **self.padding)

    def confirmAbort(self):
        self.abortPopup.destroy()
        
    def validateParams(self):
        # check to make sure fields aren't left empty
        if self.targetTemp.get() == '':
            showinfo(message="Temperature field must be populated")
            # return false
            return False
        elif self.holdTime.get() == '':
            showinfo(message="Time field must be populated")
            # return false
            return False
        elif self.selectedMaterial.get() == '':
            showinfo(message="A material must be selected")
            # return false
            return False   
        else:
            # return True
            return True

    def closeApp(self):
        # display a message about closing the app
        self.closePopup = tk.Toplevel(self)
        self.closePopup.columnconfigure(0, weight=1)
        ttk.Label(self.closePopup, text="GUI will exit now. Be cautious of potentially hot materials!").grid(row=0, **self.padding)
        ttk.Button(self.closePopup, text="Close the GUI", command=self.killApp).grid(row=1, **self.padding)

    def killApp(self):
        self.destroy()
      
#run the app
if __name__ == "__main__":
    app = MSIO()
    app.mainloop()