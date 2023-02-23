# MicrowaveSintering
Repository for the code that runs the microwave furnace. The main code block is the MicroSinterIO.py: this contains the code for the UI and the open loop control that is being used at the moment. It is built on the tkinter library in python as this is a well supported and easy to use package. The main GUI window is configured as a 5x5 grid in which widgets are placed. The main widgets are: entry fields for the hold temp and hold time, as well as a material selection list; 6 buttons for functions such as saving and loading presets, running and aborting a process, closing the GUI window, and running a development process; and finally, readouts for the current state of the microwave and the timer associated with that state.       

## Setting up the Pi
They system runs by executing a compiled version of the code on a Rasberry Pi. Setting up the Raspberry Pi is fairly straight forward and numerous resources exist online to help future users recreate the environment needed to run the GUI. A basic outline will be included here to help guide future users to the proper resources.          
         
Visit [raspberrypi.com](https://www.raspberrypi.com/) and download the raspberry pi imager. Guides exist as well, but the process is as straightforward as plugging in a micro SD card, selecting the default operating system in imager (Raspberry Pi OS 32 bit), and flashing the image. Optional steps such as setting the default username and hostname are recommended, but not required.        
       
Once the Pi is booted for the first time it will need to be connected to the internet so that the repository can be cloned. Users could also use software such as WinSCP or even a thumb drive to move the repository onto the Pi, but the A+ version of the Pi currently in use only has one USB jack so inputs are limited. Personally, I installed a USB WiFi dongle and used ssh to clone the repository from the command line after identifying the Pi on my local network. The command to clone the repository from the command line is: `git clone https://github.com/ReillyBex/MicrowaveSintering.git`. This command will clone the repository to the home directory. It is also recommended to run the commands: `sudo apt-get update && sudo apt-get upgrade` to ensure that the Pi is running on the most up to date packages. This step can be ommitted, but if future problems arise this is a good place to start.       
           
Next, users will want to drag the app from the cloned MicrowaveSintering directory into the desktop for easy access. Finally, users will need to enable the pi GPIO deamon to run on boot. This can be done by running the following command from the command line: `sudo systemctl enable pigpiod`        
             
The pi can now be restarted, or the pi GPIO deamon manually started using: `sudo pigpiod start`. The Pi should now be fully configured to run the GUI.         
        
## Other Tools
The main code is compiled using a tool called "auto-py-to-exe". Simply use PIP to install it and run it from the command line. Helpful debugging info is found [here](https://nitratine.net/blog/post/issues-when-using-auto-py-to-exe/)   
            
The app is configured to compile as a single file that runs from the terminal. It should have a name resembling "MicroSinterIO", though that may change in the future. The app is currently not optimized to run on the 512mB of RAM on the Pi A+, so the current load times are slow. However, realistically the app will only need to be opened once as the Pi is directly connected to the microwaves AC power and will remain on as long as the microwave is plugged in. 
  
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
###### closeLoopControl()     
This is basic code for a PID controller. This would necessitate some way of reading the temperature of the specimen each time through the control loop, which does not currently exist. Future users might acheive this, so I added it in for placeholding sake. 
###### confrimAbort()    
This closes the pop-up that asks the user to confirm their intent to abort the process.     
###### confirmProcess()    
This shows the currently entered parameters and asks the user to confirm them and proceed with the process, or cancel and return to the main window of the GUI.     
###### controlLoop()    
This is the state machine loop for controlling the process. It contails the functions eventCheck() and eventService(), as well as an event that calls itself after 1 second has passed. This allows the control loop to run in the background and leaves the main window accessible to the user.    
###### createWidgets()    
This creates the entry boxes, the material selection list, as well as the 5 buttons on the main window.    
###### currentTime()   
This gets the current time relative to the start of the process. a variable called self.tempTime is set with time.monotonic() in the control loop to be the time that each state begins. This is then compared to the current value of time.monotonic() and the difference is divided by 60 to return minutes since that is what the user inputs and the look up tables are coded for. 
###### debugFunc()     
This is just a function that can be filled with anything you want to debug. It is run before the main loop so you can see if functions have runtime errors or unexpected behavior.     
###### eventCheck()   
This has the logic to check for events based on the current state of the machine. Events are: 
1. timer expiers
2. user aborts the process   
When an event is detected, this function sets the appropriate next state of the machine, which is used by eventService().    
###### eventService()   
This takes the current state and the specified next state and modifies machine parameters to transition correctly.  
###### getTemp()       
This would get the real time temperature of the specimen if we had a way to do so. Needed in the closeLoopControl() function, so I added it in as a placeholder.      
###### killApp()
This is the actual function that destroys the GUI. It is called by closeApp().     
###### loadEntryFields()    
This takes the selected entry of the presets and splits it into the appropriate parameters. It also closes the pop-up from which the user selects a preset.     
###### loadEntryPopup()
This generates a pop-up with a scoll list that displays all the saved presets. The user can then select one and load it into the process parameters to be run.     
###### lookUpDutyCycle(temperature, material)    
This takes the input hold temp and finds out what duty cycle has that as it's steady state temperature. It creates a list of the last temperature in each row of measurements, which we are assuming to be steady state temperatures. Once this list has been generated, it then checks if the items in that list of temperatures are within the specified tolerance of the input hold temperature. It calculates the duty cycle if it is, and returns 0 if not. 
###### lookUpRampTime(temperature, material)   
This takes the input hold temperature and finds out how long it will take to reach that on full power. If the input temperature matches an entry on the 100% duty cycle row exactly, it returns the time associated with that entry. Otherwise, it linearly interpolates the time required by finding the data points on either side. 
###### materialSelect()   
This takes the selected material from the main GUI list and sets it to be the material for the process.    
###### presetSelect()   
This takes the selected preset in the "load presets" pop-up and sets it to be split up by the loadEntryFields() function.      
###### runMicrowave()      
This allows users to run the microwave at the input duty cycle for the input amount of time in minutes. Must be called from executed code; not available in the compiled app. 
###### runProcess()   
This starts the process running by using lookUpDutyCycle() and lookUpRampTime() to set the appropriate timers and steady state duty cycle to be sent to the magnetron.    
###### saveEntryFields()   
This takes the current values of the run parameters and generates an entry. If the entry is not already present in the preset file, it is added for future use.    
###### saveEntryPrompt() 
This creates a pop-up that displays the current process parameters and asks the user to confirm or cancel the save function.     
###### validateParams()   
This runs the currently input process parameters through various checks to ensure the parameters are actually usable by the program. It displays errors prompting the user to make the necessary changes so the process can run.         
###### updateTimer()       
This updates the countdown timer on the main GUI. It uses ramp time or process time depending on the state, and uses a function called divmod() to convert the raw seconds of the timer into minutes + seconds. 
### Future work   
I would like to have the 3 main sections of the GUI visually broken up somehow, perhaps using frames? Overall the GUI looks basic and could use some polish.   
             
Better optimization to minimize RAM usage on the Pi. Perhaps only import the packages needed as opposed to the whole tkinter suite?            
           
This whole system could be launched as a web server similar to how Klipper works. This would allow users to simply launch a web browser from wherever is conveneient, and also remove the need to have any UI on the Pi itself. 
