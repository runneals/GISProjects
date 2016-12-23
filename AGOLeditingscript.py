#-------------------------------------------------------------------------------
# Name:        Disables/ReEnables Editing for Service
# Purpose:
#
# Author:      Kelly Gerrow/Hunter Praska/Mark McCart
# Contact:      kgerrow@esri.com
#
# Created:     9/8/2016
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
#defCapabilities= '{"capabilities":"Query"}' #editing disabled (uncomment this after updating a service)
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
