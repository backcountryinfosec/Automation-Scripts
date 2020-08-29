'''
Script will upload files that are located in a directory.
Files are uploaded to viper via it's api, please make any necessary changes to the URL's, filepath and extra tags.
The structure for this file came from Paul Melson's github https://github.com/pmelson/viper-scripts
changed what was used for tags, general structure and how data is pulled for tags. Previously the script used
regex and now it uses json pulling only the key we need.

Run with a cron job at what ever frequency you need ie: 0 * * * * /usr/bin/python /path/to/script.py
'''


import requests
import json
import hashlib
import os
from os import listdir
from os.path import isfile, join

#UPDATE THIS IF NEEDED - Viper URLs
url_upload = 'http://localhost:8080/file/add'
url_tag = 'http://localhost:8080/file/tags/add'
url_run = 'http://localhost:8080/file/find'

#Virustotal API key
APIKEY = ''

# Define file upload directory and any additional tags to affix to files
filepath = "/path/to/monitor/directory"
extratags = 'tagname'


def sha256_checksum(filename, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            sha256.update(block)
    return sha256.hexdigest()
def getVirustotalName(filesha,APIKEY):
    # Define VirusTotal API Parameters:
    params = {'apikey': APIKEY,
              'resource': filesha}
    paramsSubmit = {'apikey':APIKEY,}
    headers = {
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0"
    }
    virustotallist = []
    response = requests.get('https://www.virustotal.com/vtapi/v2/file/report',
                            params=params, headers=headers)
    json_response = json.loads(response.text)
    try:
        for i in json_response['scans']:
            virustotallabel = json_response['scans'][i]['result']
            if virustotallabel is not None:
                virustotallist.append(virustotallabel)
        if len(virustotallist) != 0:
            signature = max(virustotallist, key=virustotallist.count)
            return signature
        else:
            signature = "VTClean"
            return signature
    except:
        print("File not yet on VT: Submitting...")
        signature = "NotonVT"
        return signature
def main():
    filelist = [f for f in listdir(filepath) if isfile(join(filepath, f))]
    for file in filelist:
        fullpath = join(filepath, file)
        files = {'file': open(fullpath, 'rb')}
        r = requests.post(url_upload, files=files)
        filesha = sha256_checksum(join(filepath,file))
        #You can always change the params to run a command on the file and use that as a tag as shown in Paul's version
        params = {'sha256': filesha}
        r = requests.post(url_run, params)
        json_data = json.loads(r.text)
        type = json_data['results']['default'][0]['type']
        type = type.replace(',', '')
        VT = getVirustotalName(filesha,APIKEY)
        params = {'sha256': filesha, 'tags': VT + "," + type + "," + extratags }
        r = requests.post(url_tag, params)
        os.remove(join(filepath,file))

if __name__ == '__main__':
    main()
