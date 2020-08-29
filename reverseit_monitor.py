#!/usr/bin/env python

''' Used to monitor reverseIT / Hybrid Analysis feed. Won't catch everything but gets a major sampling.
Used it to monitor some general stats about what was being uploaded. It works as needed, plenty to clean up and further process
if you want.'''


import requests
import json
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
import dateutil.parser
from dateutil.relativedelta import *
import hashlib
import os
import re

# Setup elasticsearch
es = Elasticsearch("ELASTIC_URL:9200")


# Get the current feed
def getfeed():
    url = 'https://www.reverse.it/feed?json'
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/61.0.3163.100 Safari/537.36'}
    r = requests.get(url, headers=headers)
    rawjson = json.loads(r.text)
    return rawjson


# Clean hash list from anything over a day old or something.
def cleanhashlist():
    with open('feed_history.tmp', 'r') as f:
        lines = f.readlines()
    with open('feed_history.tmp', 'w') as f:
        for line in lines:
            hashtime = line.split(',')[1].strip('\n')
            hashtime = dateutil.parser.parse(hashtime)
            if datetime.utcnow() - hashtime < timedelta(1):
                f.write(line)



# Load previous hash's to make sure we don't duplicate anything
def previousfeedhash():
    if os.path.exists('feed_history.tmp'):
        with open('feed_history.tmp', 'r')as old:
            old_feed = old.read()  # .split(',')
            # print old_feed
            return old_feed
    else:
        old_feed = []
        return old_feed


# Get all the new feed items hashed
def newfeedhash(feeditem):
    sha1 = (hashlib.sha1(str(feeditem)).hexdigest())
    return sha1


# Write the completed items that have been uploaded to ES so we can track going forward
def completedfeed(completedhash):
    new = open('feed_history.tmp', 'a')
    datenow = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    new.write(completedhash + "," + datenow + "\n")
    new.close()


# For what ever reason all the timestamps from the feed are not the same format. This is a quick
# and dirty way to make them match. Exact time isn't important and this is close enough
def matchtime(time):
    if re.match('\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-\d{2}:\d{2}', time) is not None:
        newtime = dateutil.parser.parse(time)
        newtime = newtime + relativedelta(hours=+6)  # Adj to make UTC
        newtime = newtime.strftime("%Y-%m-%dT%H:%M:%S")
        return newtime
    elif re.match('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', time) is not None:
        newtime = dateutil.parser.parse(time)
        newtime = newtime + relativedelta(hours=-1)  # Adj to make UTC from CEST
        newtime = newtime.strftime("%Y-%m-%dT%H:%M:%S")
        return newtime
    else:
        print("Unknown Time Format %s" % time)
        pass


def main():
    feed = getfeed()
    previousfeed = previousfeedhash()
    indexdate = datetime.utcnow().strftime('%Y.%m.%d')
    # Lets go through each object in the feed and put it in ES
    for i in feed['data']:
        feedhash = newfeedhash(i)
        if feedhash in previousfeed:
            print("Skipping " + datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'))

        # Check if timestamp is blank, if so use the current time
        if i["analysis_start_time"] != "":
            i["@timestamp"] = matchtime(i["analysis_start_time"])
        else:
            i["@timestamp"] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        del i["analysis_start_time"]
        
        try:
            # Remove any dictionaries from compromised hosts field
            if "compromised_hosts" in i:
                if type(i['compromised_hosts']) is dict:
                    i['compromised_hosts'] = str(i['compromised_hosts'])
            es.index(index='reverseit-' + indexdate, doc_type='threat_feed', id=i['sha256'], body=i)
        except (RuntimeError, TypeError, NameError) as e:
            errorfile = open("errors.txt", 'a')
            errorfile.write("Error sending to elastic: %s -- \n" % i)
            errorfile.write("Error({0}): {1}".format(e.errno, e.strerror))
            errorfile.close()
            pass

        # Lets add our completed item to the old hash list so we don't copy it
        completedfeed(feedhash)
    print("Complete")


if __name__ == '__main__':
    main()
    cleanhashlist()
