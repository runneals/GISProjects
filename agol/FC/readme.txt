1. ShutDownScript.txt
	a. This file contains the python code needed for the FME Shutdown Script
	b. You will need to change the following items:
    	i. Line 32: Change ‘overwrite_WORKSPACENAME’ to the new name of your .py file
		ii. Line 64: Change the path of the config file you’re using for this script in FME Workbench
		iii. Line 65: Only change the config file name, leave the path the same
	c. Note: If running from FME Workbench, comment out Line 65. If running from FME Server, comment out Line 64 and uncomment Line 65
2. overwrite_DB.cfg
	a. This is the Config File needed to run in conjunction with the .py file for creating Feature Collections
	b. You will need to change the following items:
		i. Line 2: Change the Feature Service ID to match the ID of your new Service
		ii. Line 3: Change the Feature Collection ID to match the ID of your new Feature Collection
		iii. Line 19: Delete existing fields listed and add all fields that are contained in your new AGOL Service
		iv. Line 22: Change the name of your log file to correspond to name of your new Python Script
3. overwrite_DB.py
	a. This is the actual python code for the conversion
	b. You will need to change the following items:
		i. Line 166: Change the name of the Config File to match the new name you saved it as
		ii. Line 221: Change the name of the Log File to match the new name you changed in the Config File
 
To run on FME Server, you will have to upload the files via with FME Server Web Interface to this location: MANAGE>RESOURCES>ENGINE>PLUGINS>PYTHON
