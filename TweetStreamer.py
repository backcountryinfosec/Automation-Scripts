#!/usr/bin/env python
import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import json
from elasticsearch import Elasticsearch
import datetime
from watson_developer_cloud import NaturalLanguageUnderstandingV1
import watson_developer_cloud.natural_language_understanding.features.v1 as Features

"""
This twitter code uses a user's numerical ID and will track their tweets live as the come in. Runs through watson's NLU
API and then uploads to ES.
"""

consumer_key="YBFMgErZkiN8MWqBGcHXm2dCp"
consumer_secret="fmuMKwya4XyyjegvSyYAwBalZYI8heom3Ds56hkxVZmBuRNQ6t"

access_token="918660934528155648-InbzRO92y5NFmhGEmiGI7NGc0wxZhAO"
access_token_secret="mn3PehlsuJwJnQ4dlMC3cASwMyqlC0GHPT2uok8KbJltt"

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

#  Setup elasticsearch
es = Elasticsearch("10.0.2.81:9200")

#  Setup watson NLU API
natural_language_understanding = NaturalLanguageUnderstandingV1(
    version='2017-05-19',
    username='3efc3d64-d9ee-43b3-a289-e530bad6347b',
    password='uDs5p3a4CPyd')

def natural_language(tweet):
    response = natural_language_understanding.analyze(
        text=tweet,
        features=[Features.Sentiment(), Features.Emotion()])
    return response


def fix_tstamp(tstamp):
    # Mon Oct 16 12:57:50 +0000 2017
    date = tstamp.replace(" +0000", "")
    date = datetime.datetime.strptime(date, '%a %b %d %H:%M:%S %Y')
    return str(date)

class listener(StreamListener):
    def on_data(self, data):
        data = json.loads(data)
        if data is not None:
            if not data['retweeted'] and '@realDonaldTrump' not in data['text'] and data['in_reply_to_user_id']\
                    is not '25073877' and data['user']['id'] == '25073877':
                data["created_at"] = fix_tstamp(data["created_at"])
                indexdate = data["created_at"][:7]
                print(data)
                try:
                    data["watson_natural_lang"] = (natural_language(data["text"]))
                except:
                    print data["text"]
                    pass
                print data
                #es.index(index='presidentialtweets-' + indexdate, doc_type='twitter', id=data["id"], body=data)
                return(True)
        else:
            pass
    def on_error(self, status):
        print status


while True:
    twitterStream = Stream(auth, listener())
    twitterStream.filter(follow=['25073877'])
