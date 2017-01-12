"""
-------------------------------------------------------------------------------
 | Copyright 2016 Esri
 |
 | Licensed under the Apache License, Version 2.0 (the "License");
 | you may not use this file except in compliance with the License.
 | You may obtain a copy of the License at
 |
 |    http://www.apache.org/licenses/LICENSE-2.0
 |
 | Unless required by applicable law or agreed to in writing, software
 | distributed under the License is distributed on an "AS IS" BASIS,
 | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 | See the License for the specific language governing permissions and
 | limitations under the License.
 ------------------------------------------------------------------------------
 """
import datetime, time, os, sys, traceback, gzip, json, email.generator, mimetypes, shutil, io

try:
    from urllib.request import urlopen as urlopen
    from urllib.request import Request as request
    from urllib.parse import urlencode as encode
    import configparser as configparser
    from io import StringIO
# py2
except ImportError:
    from urllib2 import urlopen as urlopen
    from urllib2 import Request as request
    from urllib import urlencode as encode
    import ConfigParser as configparser
    from cStringIO import StringIO

class _MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""
    PY2 = sys.version_info[0] == 2
    PY3 = sys.version_info[0] == 3
    files = []
    form_fields = []
    boundary = None
    form_data = ""
    #----------------------------------------------------------------------
    def __init__(self, param_dict, files):
        self.boundary = None
        self.files = []
        self.form_data = ""
        if len(self.form_fields) > 0:
            self.form_fields = []

        if len(param_dict) == 0:
            self.form_fields = []
        else:
            for key, value in param_dict.items():
                self.form_fields.append((key, value))
                del key, value
        if len(files) == 0:
            self.files = []
        else:
            for key, value in files.items():
                self.add_file(fieldname=key,
                              filename=os.path.basename(value),
                              filepath=value,
                              mimetype=None)
        self.boundary = email.generator._make_boundary()
    #----------------------------------------------------------------------
    def get_content_type(self):
        """Gets the content type."""
        return 'multipart/form-data; boundary=%s' % self.boundary
    #----------------------------------------------------------------------
    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
    #----------------------------------------------------------------------
    def add_file(self, fieldname, filename, filepath, mimetype=None):
        """Add a file to be uploaded.
        Inputs:
           fieldname - name of the POST value
           fieldname - name of the file to pass to the server
           filePath - path to the local file on disk
           mimetype - MIME stands for Multipurpose Internet Mail Extensions.
             It's a way of identifying files on the Internet according to
             their nature and format. Default is None.
        """
        body = filepath
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
    #----------------------------------------------------------------------
    @property
    def make_result(self):
        """Returns the data for the request."""
        if self.PY2:
            self._py2()
        elif self.PY3:
            self._py3()
        return self.form_data
    #----------------------------------------------------------------------
    def _py2(self):
        """python 2.x version of formatting body data"""
        boundary = self.boundary
        buf = StringIO()
        for (key, value) in self.form_fields:
            buf.write('--%s\r\n' % boundary)
            buf.write('Content-Disposition: form-data; name="%s"' % key)
            buf.write('\r\n\r\n%s\r\n' % value)
        for (key, filename, mimetype, filepath) in self.files:
            if os.path.isfile(filepath):
                buf.write('--{boundary}\r\n'
                          'Content-Disposition: form-data; name="{key}"; '
                          'filename="{filename}"\r\n'
                          'Content-Type: {content_type}\r\n\r\n'.format(
                              boundary=boundary,
                              key=key,
                              filename=filename,
                              content_type=mimetype))
                with open(filepath, "rb") as local_file:
                    shutil.copyfileobj(local_file, buf)
                buf.write('\r\n')
        buf.write('--' + boundary + '--\r\n\r\n')
        buf = buf.getvalue()
        self.form_data = buf
    #----------------------------------------------------------------------
    def _py3(self):
        """ python 3 method"""
        boundary = self.boundary
        buf = io.BytesIO()
        textwriter = io.TextIOWrapper(
            buf, 'utf8', newline='', write_through=True)

        for (key, value) in self.form_fields:
            textwriter.write(
                '--{boundary}\r\n'
                'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                '{value}\r\n'.format(
                    boundary=boundary, key=key, value=value))
        for(key, filename, mimetype, filepath) in self.files:
            if os.path.isfile(filepath):
                textwriter.write(
                    '--{boundary}\r\n'
                    'Content-Disposition: form-data; name="{key}"; '
                    'filename="{filename}"\r\n'
                    'Content-Type: {content_type}\r\n\r\n'.format(
                        boundary=boundary, key=key, filename=filename,
                        content_type=mimetype))
                with open(filepath, "rb") as local_file:
                    shutil.copyfileobj(local_file, buf)
                textwriter.write('\r\n')
        textwriter.write('--{}--\r\n\r\n'.format(boundary))
        self.form_data = buf.getvalue()

class _OverwriteHostedFeatures(object):

    def __init__(self):
        self._config_options = {}

    def _read_config(self, config_file):
        """Read the config and set global variables used in the script.
        
        Keyword arguments:
        config_file - Path to the configuration file. 
        If None it will look for a file called overwrite_hosted_features.cfg in the same directory as the executing script.
        """

        config = configparser.ConfigParser()
        if config_file is None:
            config_file = os.path.join(os.path.dirname(__file__), 'overwrite_DB.cfg')
        config.readfp(open(config_file))

        log_path = _validate_input(config, 'Log File', 'path', 'path', False)
        if log_path is not None:
            self._config_options['log_path'] = log_path

        is_verbose = _validate_input(config, 'Log File', 'isVerbose', 'bool', False)
        if is_verbose is not None:
            self._config_options['is_verbose'] = is_verbose

        self._start_logging()

        self._config_options['feature_service_id'] = _validate_input(config, 'Existing ItemIDs', 'featureServiceItemID', 'id', True)

        feature_collection_id = _validate_input(config, 'Existing ItemIDs', 'featureCollectionItemID', 'id', False)
        if feature_collection_id is not None:
            self._config_options['feature_collection_id'] = feature_collection_id
        
        fgdb = _validate_input(config, 'Data Sources', 'fgdb', 'path', False)
        if fgdb is not None:
            self._config_options['fgdb'] = fgdb
        
        self._config_options['org_url'] = _validate_input(config, 'Portal Sharing URL', 'baseURL', 'url', True)
        self._config_options['username'] = _validate_input(config, 'Portal Credentials', 'username', 'string', True)
        self._config_options['pw'] = _validate_input(config, 'Portal Credentials', 'pw', 'string', True)

        token_url = _validate_input(config, 'Portal Sharing URL', 'tokenURL', 'url', False)
        if token_url is not None:
            self._config_options['token_url'] = token_url

        max_allowable_offset = _validate_input(config, 'Generalization', 'maxAllowableOffset', 'int', False)
        if max_allowable_offset is not None:
            self._config_options['max_allowable_offset'] = max_allowable_offset

        layer_mapping = _validate_input(config, 'Layers', 'nameMapping', 'mapping', False)
        if layer_mapping is not None:
            self._config_options['layer_mapping'] = layer_mapping

    def _start_logging(self):
        """If a log file is specified in the config,
        create it if it doesn't exist and write the start time of the run."""
        self._config_options['start_time'] = datetime.datetime.now()

        if 'log_path' in self._config_options:
            log_path = self._config_options['log_path']
            is_file = os.path.isfile(log_path)

            logfile_location = os.path.abspath(os.path.dirname(log_path))
            if not os.path.exists(logfile_location):
                os.makedirs(logfile_location)

            if is_file:
                path = log_path
            else:
                path = os.path.join(logfile_location, "DB_OverwriteLog.txt")

            log_path = path
            log = open(path, "a")
            date = self._config_options['start_time'].strftime('%Y-%m-%d %H:%M:%S')
            log.write("----------------------------" + "\n")
            log.write("Begin Data Overwrite: " + str(date) + "\n")
            log.close()

    def _log_message(self, my_message, is_error=False):
        """Log a new message and print to the python output.

        Keyword arguments:
        my_message - the message to log
        is_error - indicates if the message is an error, used to log even when verbose logging is disabled
        """
        date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if 'log_path' in self._config_options and (('is_verbose' in self._config_options and self._config_options['is_verbose']) or is_error):
            log = open(self._config_options['log_path'], "a")
            log.write("     " + str(date) + " - " +my_message + "\n")
            log.close()
        print("     " + str(date) + " - " +my_message + "\n")

    def _end_logging(self):
        """If a log file is specified in the config write the elapsed time."""
        if 'log_path' in self._config_options:
            log = open(self._config_options['log_path'], "a")
            endtime = datetime.datetime.now()

            log.write("Elapsed Time: " + str(endtime - self._config_options['start_time']) + "\n")
            log.close()

    def _log_error(self):
        """Log an error message."""
        pymsg = "PYTHON ERRORS:\nTraceback info:\n{1}\nError Info:\n{0}".format(str(sys.exc_info()[1]), "".join(traceback.format_tb(sys.exc_info()[2])))
        self._log_message(pymsg, True)

    def _url_request(self, url, request_parameters, request_type='GET', files=None, repeat=0, error_text="Error", raise_on_failure=True):
        """Send a new request and format the json response.
        Keyword arguments:
        url - the url of the request
        request_parameters - a dictionay containing the name of the parameter and its correspoinsding value
        request_type - the type of request: 'GET', 'POST'
        files - the files to be uploaded
        repeat - the nuber of times to repeat the request in the case of a failure
        error_text - the message to log if an error is returned
        raise_on_failure - indicates if an exception should be raised if an error is returned and repeat is 0"""
        if files is not None:
            mpf = _MultiPartForm(param_dict=request_parameters, files=files)
            req = request(url)
            body = mpf.make_result
            req.add_header('Content-type', mpf.get_content_type())
            req.add_header('Content-length', len(body))
            req.data = body
        elif request_type == 'GET':
            req = request('?'.join((url, encode(request_parameters))))
        else:
            headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',}
            req = request(url, encode(request_parameters).encode('UTF-8'), headers)

        req.add_header('Accept-encoding', 'gzip')

        response = urlopen(req)

        if response.info().get('Content-Encoding') == 'gzip':
            buf = io.BytesIO(response.read())
            with gzip.GzipFile(fileobj=buf) as gzip_file:
                response_bytes = gzip_file.read()
        else:
            response_bytes = response.read()

        response_text = response_bytes.decode('UTF-8')
        response_json = json.loads(response_text)

        if "error" in response_json:
            if repeat == 0:
                if raise_on_failure:
                    raise Exception("{0}: {1}".format(error_text, response_json))
                return response_json

            repeat -= 1
            time.sleep(2)
            response_json = self._url_request(
                url, request_parameters, request_type, files, repeat, error_text)

        return response_json

    def _get_token(self):
        """Returns a token for the given user and organization."""
        query_dict = {'username': self._config_options['username'],
                      'password': self._config_options['pw'],
                      'expiration': '60',
                      'referer': self._config_options['org_url'],
                      'f': 'json'}

        token_url = "https://www.arcgis.com/sharing/rest/generateToken"
        if 'token_url' in self._config_options:
            token_url = self._config_options['token_url']

        token_response = self._url_request(token_url, query_dict, 'POST', repeat=2, raise_on_failure=False)

        if "token" not in token_response:
            raise Exception("Unable to connect to specified portal. Please verify you are passing in your correct portal url, token url, username and password.")
        else:
            return token_response['token']

    def _wait_on_job(self, item_id, job_type, job_id, error_text):
        """Waits for a job to complete, if it fails an exception is raised.

        Keyword arguments:
        item_id - the id of the item to get the status for
        job_type - the type of job currently processing
        job_id - the id of the pending job
        error_text - the error to raise if the job fails"""
        url = '{0}sharing/rest/content/users/{1}/items/{2}/status'.format(self._config_options['org_url'], self._config_options['username'], item_id)
        parameters = {'token': self._config_options['token'], 'f': 'json', 'jobType' : job_type, 'jobId' : job_id}

        status = "processing"
        while status != "completed":
            response = self._url_request(url, parameters, repeat=2, error_text=error_text)
            status = response['status'].lower()
            if status == 'failed':
                raise Exception("{0}: {1}".format(error_text, str(response['statusMessage'])))
            elif status == "completed":
                break
            time.sleep(2)

    def _get_published_items(self):
        """Validates the feature service and feature collection exist and sets global variables."""
        url = '{0}sharing/rest/content/items/{1}'.format(self._config_options['org_url'], self._config_options['feature_service_id'])
        request_parameters = {'f' : 'json', 'token' : self._config_options['token']}
        item = self._url_request(url, request_parameters, error_text='Unable to find feature service with ID: {}'.format(self._config_options['feature_service_id']))

        if not item['type'] == 'Feature Service':
            raise Exception("Item {} is not a feature service".format(self._config_options['feature_service_id'])) 

        self._config_options['basename'] = item['title']

        if 'feature_collection_id' in self._config_options:
            url = '{0}sharing/rest/content/items/{1}'.format(self._config_options['org_url'], self._config_options['feature_collection_id'])
            item = self._url_request(url, request_parameters, error_text='Unable to find feature collection with ID: {}'.format(self._config_options['feature_collection_id']))

            if not item['type'] == 'Feature Collection':
                raise Exception("Item {} is not a feature collection".format(self._config_options['feature_collection_id'])) 

            self._config_options['temp_fc_name'] = item['title'] + "_temp"
            self._config_options['owner_folder'] = item['ownerFolder']

    def _delete_item(self, item_id):
        """Delete an item from the portal with a given id.

        Keyword arguments:
        item_id - the id of the item to delete"""
        url = '{0}sharing/rest/content/users/{1}/items/{2}/delete'.format(self._config_options['org_url'], self._config_options['username'], item_id)
        request_parameters = {'f' : 'json', 'token' : self._config_options['token']}
        return self._url_request(url, request_parameters, 'POST', repeat=2, raise_on_failure=False)

    def _find_and_delete_gdb(self, gdb_name):
        """Search the portal for a geodatabase with a given name owned by the owner specified and if found delete the item.

        Keyword arguments:
        gdb_name - the name of the geodatabase"""
        url = '{0}sharing/rest/search'.format(self._config_options['org_url'])
        request_parameters = {'f' : 'json', 'q' : 'OverwriteHostedFeatures owner:{0} type:"File Geodatabase"'.format(self._config_options['username']), 
                              'token' : self._config_options['token']}
        response = self._url_request(url, request_parameters, error_text='Failed to upload file geodatabase')
        results = response['results']
        existing_gdb = next((r['id'] for r in results if r['name'] == gdb_name and "OverwriteHostedFeatures" in r['tags']), None)
        if existing_gdb is None:
            self._log_message("Failed to find file geodatabase on the portal named {0}: {1}".format(gdb_name, response))
            return

        self._log_message("File geodatabase {} found on the portal, deleting the item".format(gdb_name))
        response = self._delete_item(existing_gdb)
        if 'success' in response and response['success']:
            self._log_message("File geodatabase deleted")
        else:
            self._log_message("Failed to delete file geodatabase: {0}".format(response))

    def _upload_fgdb(self):
        """Uploads the file geodatabase to the portal."""
        fgdb = self._config_options['fgdb']

        if not os.path.exists(fgdb):
            raise Exception("File geodatabase {} could not be found".format(fgdb))
        gdb_name = os.path.basename(fgdb)
        self._log_message("Uploading file geodatabase {}".format(fgdb))
    
        try:
            request_parameters = {'f' : 'json', 'token' : self._config_options['token'], 'tags' : 'OverwriteHostedFeatures',
                                  'itemType' : 'file', 'async' : False,
                                  'type' : 'File Geodatabase', 'descriptipion' : 'GDB',
                                  'filename' : os.path.basename(fgdb), 'title' : self._config_options['basename']}

            url = '{0}sharing/rest/content/users/{1}/addItem'.format(self._config_options['org_url'], self._config_options['username'])
            files = {}
            files['file'] = fgdb
            response = self._url_request(url, request_parameters, files=files, error_text='Failed to upload file geodatabase')
        except Exception:
            self._log_message("Failed to upload file geodatabase. Searching the portal for a file geodatabase with the same name")
            self._find_and_delete_gdb(gdb_name)
            response = self._url_request(url, request_parameters, files=files, error_text='Failed to upload file geodatabase')
    
        self._config_options['gdb_item_id'] = response['id']
        self._log_message("File geodatabase upload complete")

    def _update_feature_service(self):
        """Overwrites the feature service using the uploaded file geodatabase."""
        basename = self._config_options['basename']
        org_url = self._config_options['org_url']
        feature_service_id = self._config_options['feature_service_id']

        self._log_message("Updating {} feature service".format(basename))

        url = '{0}sharing/rest/content/items/{1}'.format(org_url, feature_service_id)
        request_parameters = {'f' : 'json', 'token' : self._config_options['token']}
        response = self._url_request(url, request_parameters, error_text='Unable to find feature service with ID: {}'.format(feature_service_id))

        fs_url = response['url']
        feature_service = self._url_request(fs_url, request_parameters, repeat=2, error_text='Unable to get JSON definition of feature service')
        publish_params = feature_service
        publish_params['name'] = os.path.basename(os.path.dirname(fs_url))
        
        layers = self._url_request(fs_url + "/layers", request_parameters, repeat=2, error_text='Unable to get JSON definition of feature service layers')                           
        publish_params['layers'] = layers['layers']
        publish_params['tables'] = layers['tables']

        if 'layer_mapping' in self._config_options: #The name of the layer needs to match the name of the feature class for it to be succesfully overwritten
            for mapping in self._config_options['layer_mapping']:
                lyr = next((i for i in publish_params['layers'] if i['name'] == mapping[0]), None)
                if lyr is not None:
                    lyr['name'] = mapping[1]

        #Need to pass the C encoding for '<' and '>', otherwise publish fails.        
        publish_params_json = json.dumps(publish_params).replace('<', '\\u003c').replace('>', '\\u003e')
        
        attempt_count = 2
        for i in range(attempt_count):
            try:         
                url = '{0}sharing/rest/content/users/{1}/publish'.format(org_url, self._config_options['username'])
                request_parameters = {'f' : 'json', 'token' : self._config_options['token'],
                                      'publishParameters' : publish_params_json, 'itemID' : self._config_options['gdb_item_id'],
                                      'overwrite' : True, 'fileType' : 'fileGeodatabase'}
                response = self._url_request(url, request_parameters, "POST", error_text='Failed to update {} feature service'.format(basename))
                if 'services' not in response:
                    raise Exception("Failed to update {0} feature service: {1}".format(basename, response))      
                service = response['services'][0]
                if 'jobId' not in service:
                    raise Exception("Failed to update {0} feature service: {1}".format(basename, response))
                self._wait_on_job(feature_service_id, "publish", service['jobId'], "Failed to update {0} feature service, job id: {1}".format(basename, service['jobId']))
                break
            except Exception as ex:
                ex.args = ("Attempt {0}: {1}".format(i+1, str(ex)),)
                if i+1 == attempt_count:              
                    raise ex
                self._log_message(str(ex))
                    
        self._log_message("{} feature service updated".format(basename))

    def _update_feature_collection(self):
        """Overwrite the feature collection using the feature service."""
        org_url = self._config_options['org_url']
        feature_service_id = self._config_options['feature_service_id']
        feature_collection_id = self._config_options['feature_collection_id']

        self._log_message("Updating feature collection")

        exp_params = {}
        if 'max_allowable_offset' in self._config_options:
            exp_params.update({"maxAllowableOffset":self._config_options['max_allowable_offset']})

        attempt_count = 2
        for i in range(attempt_count):
            try:
                url = '{0}sharing/rest/content/users/{1}/export'.format(org_url, self._config_options['username'])
                request_parameters = {'f' : 'json', 'token' : self._config_options['token'],
                                      'itemID' : feature_service_id, 'exportFormat' : 'feature collection',
                                      'exportParameters' : json.dumps(exp_params),
                                      'overwrite' : True, 'resultItemId' : feature_collection_id}

                response = self._url_request(url, request_parameters, "POST", raise_on_failure=False)
    
                if 'jobId' not in response:
                    raise Exception("Failed to export temporary feature collection: {0}".format(response))

                self._wait_on_job(feature_collection_id, "export", response['jobId'], "Failed to update feature collection, job id: {0}".format(response['jobId']))
                break
            except Exception as ex:
                ex.args = ("Attempt {0}: {1}".format(i+1, str(ex)),)
                if i+1 == attempt_count:              
                    raise ex
                self._log_message(str(ex))

        date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        user_folder = self._config_options['username']
        owner_folder = self._config_options['owner_folder']
        if owner_folder is not None:
            user_folder = user_folder + "/" + str(owner_folder)

        url = '{0}sharing/rest/content/users/{1}/items/{2}/update'.format(org_url, user_folder, self._config_options['feature_collection_id'])
        request_parameters = {'f' : 'json', 'token' : self._config_options['token'], 'snippet' : str(date)}
        self._url_request(url, request_parameters, "POST", repeat=2, error_text='Failed to update feature collection')
        
        self._log_message("Feature collection updated")

    def _remove_temp_content(self):
        """Remove the temporary file geodatabase if it exists."""
        if 'gdb_item_id' in self._config_options:
            response = self._delete_item(self._config_options['gdb_item_id'])
            if 'success' in response and response['success']:
                self._log_message("File geodatabase deleted")
            else:
                self._log_message("Failed to delete file geodatabase: {0}".format(response))

    def run(self, config_file):
        """Overwrite hosted features."""
        try:         
            self._read_config(config_file)
            self._config_options['token'] = self._get_token()
            self._get_published_items()
            if 'fgdb' in self._config_options:
                self._upload_fgdb()
                self._update_feature_service()
            if 'feature_collection_id' in self._config_options:
                self._update_feature_collection()
        except Exception:
            self._log_error()
        finally:
            self._remove_temp_content()
            self._end_logging()

def _validate_input(config, group, name, variable_type, required):
    """Validates and returns the correspoinding value defined in the config.

    Keyword arguments:
    config - the instance of the configparser
    group - the name of the group containing the property
    name - the name of the property to get that value for
    variable_type - the type of property, 'path', 'mapping' 'bool', otherwise return the raw string
    required - if the option is required and none is found than raise an exception
    """
    try:
        value = config.get(group, name)
        if value == '':
            raise configparser.NoOptionError(name, group)

        if variable_type == 'path':
            return os.path.normpath(value)
        elif variable_type == 'mapping':
            return list(v.split(',') for v in value.split(';'))
        elif variable_type == 'bool':
            return value.lower() == 'true'
        else:
            return value
    except (configparser.NoSectionError, configparser.NoOptionError):
        if required:
            raise
        elif variable_type == 'bool':
            return False
        else:
            return None

def run(config_file=None):
    """Overwrite hosted features."""
    overwrite = _OverwriteHostedFeatures()
    overwrite.run(config_file)

if __name__ == "__main__":
    CONFIG_FILE = None
    if len(sys.argv) > 1:
        CONFIG_FILE = sys.argv[1]
    run(CONFIG_FILE)


