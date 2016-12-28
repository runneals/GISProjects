#-------------------------------------------------------------------------------
# Name:        Disables/ReEnables Editing for Service & Writes Feature Collections to AGOL
# Purpose:
#
# Authors:     Kelly Gerrow (Esri); Mark McCart (HNTB); Hunter Praska (Iowa DOT); Eric Rodenberg (Esri)
# Contact:     kgerrow@esri.com; mmccart@hntb.com; hunter.praska@iowa.dot.gov; erodenberg@esri.com
#
# Created:     11/18/2015
# Modified:    8/10/2016 - To include Feature Collection Creation on AGOL (Mark and Eric)
#-------------------------------------------------------------------------------

def getToken(adminUser, pw):
        data = {'username': adminUser,
            'password': pw,
            'referer' : 'https://www.arcgis.com',
            'f': 'json'}
        url  = 'https://arcgis.com/sharing/rest/generateToken'
        jres = requests.post(url, data=data, verify=False).json()
        return jres['token'],jres['ssl']

#generates account information
def GetAccount(pref, tokenfun):
    URL= pref+'www.arcgis.com/sharing/rest/portals/self?f=json&token=' + tokenfun
    response = requests.get(URL, verify=False)
    jres = json.loads(response.text)
    return jres['urlKey']

import requests, json

# Next 3 lines of code are required to copy/create Feature Collections on AGOL
import sys
#sys.path.append(r"C:\TEMP\OverwriteScript") Originally provied by Eric R. at Esri, but not needed to run in FME
from overwrite_FC import run #Rename 'overwrite_FC' to name of .py file you want to run. Store it here: C:\apps\FME\2016\python\python27\ for FME Desktop. For FME Server: Load to RESOURCES>ENGINE>PLUGINS>PYTHON via Web UI

#Enter Username and Password
user= "USERNAME" #raw_input('What is the ArcGIS Online Username?')
pw = "PASSWORD" #raw_input('What is the ArcGIS Online Password?')

#get account information
token= getToken(user, pw)
if token[1] == False:
           pref='http://'
else:
           pref='https://'
#Create Portal URL
t=GetAccount(pref,token[0])
portalUrl=pref+t


restURL='http://services.arcgis.com/ORGIDTHING/arcgis/rest/admin/services/SERVICENAME/FeatureServer/updateDefinition' #modify URL
#defCapabilities= '{"hasStaticData":false,"capabilities":"Query,Editing,Create,Update,Delete,Extract"}' #editing enabled (uncomment this before updating a service)
#defCapabilities= '{"capabilities":"Query,Extract"}' #editing disabled (uncomment this after updating a service)
data = {'updateDefinition': defCapabilities,
            'token':token[0],
            'f': 'json'}

#Send Request
res =requests.post(restURL, data = data, verify=False).json()
print res
if res['success']==True:
    print 'Service successfully Added'
else:
    print 'Service NOT ADDED'

# Run the Feature Collection creation script provided by Esri and modified for each FC
#config_file = r"C:\Apps\FME\2016_1_2_16673\python\python27\overwrite_FC.cfg" #For FME Desktop Only. Must copy .cfg and .py file here
config_file = r"C:\ProgramData\Safe Software\FME Server\resources\engine\Plugins\python\overwrite_FC.cfg" #For FME Server Only. Must load to FME Server Resources
run(config_file)
