#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import tweepy

import datetime
import time

# Get these values from your application settings

CONSUMER_KEY = ''
CONSUMER_SECRET = ''

# Get these values from the "My Access Token" link located in the
# margin of your application details, or perform the full OAuth
# dance

ACCESS_TOKEN = ''
ACCESS_TOKEN_SECRET = ''

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# Note: Had you wanted to perform the full OAuth dance instead of using
# an access key and access secret, you could have uses the following 
# four lines of code instead of the previous line that manually set the
# access token via auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
# 
# import webbrowser
# auth_url = auth.get_authorization_url(signin_with_twitter=True)
# webbrowser.open(auth_url)
# verifier = raw_input('PIN: ').strip()
# auth.get_access_token(verifier)


# list of soma.fm stations to follow
stations=("groovesalad", "doomed", "somaelectropop", "indiepoprocks", "spacestationsma", "digitalis", "noisepopradio", "somalush", "secretagentsoma", "dronezone", "sonicuniverse", "xmissioncontrol", "suburbsofgoa", "beatblender", "justcovers")
stationids = []

#sadly we need to convert that list to user_id
userinfo = tweepy.api.lookup_users(screen_names=stations)
for ids in userinfo:
    stationids.append(ids.id)

# open a mqtt publisher
import mosquitto
mqttc = mosquitto.Mosquitto('pubclient_somastreamer')
mqttc.username_pw_set("XXXX","XXXX")
mqttc.connect("nowplaying.elwell.org.uk", 1883, 60, True)

class CustomStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        
        # We'll simply print some values in a tab-delimited format
        # suitable for capturing to a flat file but you could opt 
        # store them elsewhere, retweet select statuses, etc.

        try:
            # unicode u266C = ♬
            NP = status.text.split(u'\u266C')[1]
            arttrack = NP.split(' - ')
            artist = arttrack[0].strip()
            track = arttrack[1].strip()
            ts = int(time.mktime(status.created_at.timetuple())) # twitter already uses UTC
            print "%s\t%s (%s) |%s|%s|%s" % (status.author.screen_name, NP, status.created_at, artist,track,ts)
            # do the MQTT thing
            mqttc.publish("somafm/%s/nowplaying/artist" % status.author.screen_name, str(artist))
            mqttc.publish("somafm/%s/nowplaying/track" % status.author.screen_name, str(track))
            mqttc.publish("somafm/%s/nowplaying/started" % status.author.screen_name, status.created_at.isoformat())
      

        except Exception, e:
            print >> sys.stderr, 'Encountered Exception:', e
            pass

    def on_error(self, status_code):
        print >> sys.stderr, 'Encountered error with status code:', status_code
        return True # Don't kill the stream

    def on_timeout(self):
        print >> sys.stderr, 'Timeout...'
        return True # Don't kill the stream

# Create a streaming API and set a timeout value of 60 seconds

streaming_api = tweepy.streaming.Stream(auth, CustomStreamListener(), timeout=60)

# Optionally filter the statuses you want to track by providing a list
# of users to "follow"
streaming_api.filter(follow=stationids)
