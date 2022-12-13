# MicrowaveSintering
Repository for the code that runs the microwave furnace. The main code block is the MicroSinterIOClass.py: this contains the code for the UI and the open loop control that is being used at the moment.  
  
Other code that will (potentially) be added will be the scripts used to configure a raspberry pi from scratch and download all the necessary packages and what not.   
  
Alternatively, a compiled version of the GUI will be included here. This would allow future users to simply download the executable appimage and run it on any linux system with compatible hardware, removing the need for a user to download and properly configure packages before running the program.    
# Basic Overview
The main window shows entry fields for holding temperature and hold time, and also contains a list of materials the user can select from. leaving these blank and attempting to hit the "run" button will result in an error.  
  
The top row of the preset file is a header line that shows what the collumns are. The user can mistakenly select this row, but attempting to "run" this process will again result in an error.  
    
The control loop recursively calls itself after one second, this allows the main GUI to stay open and accessible to the user while a process is running in the background. This way, a user can close the GUI or hit the "abort" button and the process will stop.  
  
### Details of class attributes (in alphebetical order)
###### __init__  
This initializes the GUI object, setting the default values for class variables and calling the createWidgets() function to generate the main widgets.   
###### abortProcess()    
This sets the PWM signal to the magnetron off and also sets the logic flag that indicates a process is running to false *wether or not a process was running in the first place*.    
###### cancelRun()   
This closes the pop-up for running the process.     
###### cancelSave()    
This closes the pop-up for saving the entry fields.     
###### closeApp()   
This turns off the PWM signal to the magnetron and closes the GUI by destroying the main window.     
###### confrimAbort()    
This closes the pop-up that asks the user to confirm their intent to abort the process.     
###### confirmProcess()    
This shows the currently entered parameters and asks the user to confirm them and proceed with the process, or cancel and return to the main window of the GUI.     
###### controlLoop()    
This is the state machine loop for controlling the process. It contails the functions eventCheck() and eventService(), as well as an event that calls itself after 1 second has passed. This allows the control loop to run in the background and leaves the main window accessible to the user.    
###### createWidgets()    
This creates the entry boxes, the material selection list, as well as the 5 buttons on the main window.    
###### currentTime()   
This gets the current time relative to the start of the process. *This still needs development and currently just returns a value of 0.*    
###### eventCheck()   
This has the logic to check for events based on the current state of the machine. Events are: 
1. timer expiers
2. user aborts the process   
When an event is detected, this function sets the appropriate next state of the machine, which is used by eventService().    
###### eventService()   
This takes the current state and the specified next state and modifies machine parameters to transition correctly.    
###### killApp()
This is the actual function that destroys the GUI. It is called by closeApp().     
###### loadEntryFields()    
This takes the selected entry of the presets and splits it into the appropriate parameters. It also closes the pop-up from which the user selects a preset.     
###### loadEntryPopup()
This generates a pop-up with a scoll list that displays all the saved presets. The user can then select one and load it into the process parameters to be run.     
###### lookUpDutyCycle()    
This takes the input hold temp and finds out what duty cycle has that as it's steady state temperature. *this requires more testing to generate the appropriate look up tables.*     
###### lookUpRampTime()   
This takes the input hold temperature and finds out how long it will take to reach that on full power. *this requires more testing to generate the appropriate look up tables.*     
###### materialSelect()   
This takes the selected material from the main GUI list and sets it to be the material for the process.    
###### presetSelect()   
This takes the selected preset in the "load presets" pop-up and sets it to be split up by the loadEntryFields() function.    
###### runProcess()   
This starts the process running by using lookUpDutyCycle() and lookUpRampTime() to set the appropriate timers and steady state duty cycle to be sent to the magnetron.    

