#-------------------------------------------------------------------------------
# Name:        Disables/ReEnables Editing for Service & Writes Feature Collections to AGOL
# Purpose:
#
# Authors:     Kelly Gerrow (Esri); Mark McCart (HNTB); Hunter Praska (Iowa DOT); Eric Rodenberg (Esri)
# Contact:     kgerrow@esri.com; mmccart@hntb.com; hunter.praska@iowa.dot.gov; erodenberg@esri.com
#
# Created:     11/18/2015
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
    
#Enter Username and Password
user= "AGOL_USERNAME" #raw_input('What is the ArcGIS Online Username?')
pw = "AGOL_PASSWORD" #raw_input('What is the ArcGIS Online Password?')

#get account information
token= getToken(user, pw)
if token[1] == False:
           pref='http://'
else:
           pref='https://'
#Create Portal URL
t=GetAccount(pref,token[0])
portalUrl=pref+t


restURL='http://services.arcgis.com/8lRhdTsQyJpO52F1/arcgis/rest/admin/services/SERVICE_NAME/FeatureServer/updateDefinition' #modify URL for Service Name, Organization ID, and ArcGIS Online Server URL
defCapabilities= '{"capabilities":"Create,Delete,Query,Update,Editing,Extract"}' #editing enabled
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
