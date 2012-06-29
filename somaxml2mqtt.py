#!/usr/bin/python

# script to parse out the metadata from soma fm and send to mqtt

xmlurl = 'http://api.somafm.com/channels.xml'
mqtt_broker = 'nowplaying.elwell.org.uk'

import mosquitto
import collections
import time
import signal
from lxml import etree

# Connect to broker
mqttc = mosquitto.Mosquitto('pubclient_somaxml')
mqttc.username_pw_set("XXXX","XXXX")
mqttc.connect(mqtt_broker, 1883, 60, True)

metadata = collections.defaultdict(dict)
persistent = collections.defaultdict(dict)
twitfeeds = {}

DEBUG = True

# Handle ctrl-c gracefully and unpublish
def handler(signum, frame):
    print "Caught SIG, cleaning up"
    for chan in persistent.keys():
        for key in metadata[chan]:
            print chan, key
            mqttc.publish("somafm/%s/%s" % (chan,key), '', retain=True)
            
    exit()
    

signal.signal(signal.SIGINT, handler)



while True:
  tree = etree.parse(xmlurl)
  #interesting = ('title','description','image','twitter','listeners','dj')
  for chan in tree.getiterator('channel'):
    #for thing in interesting:
        #for key in chan.iterchildren(tag=thing):
        for key in chan.iterchildren():
            try:
              if metadata[chan.attrib['id']][key.tag] != key.text:
                # does not match last value - check if we think its persistent
                if persistent[chan.attrib['id']][key.tag] == True:
                    persistent[chan.attrib['id']][key.tag] = False
                    print "CHANGED %s/%s from Persistant -> False" % (chan.attrib['id'], key.tag)
                    mqttc.publish("somafm/%s/%s" % (chan.attrib['id'], key.tag), '', retain=True)
                metadata[chan.attrib['id']][key.tag] = key.text
                print "UPDATE somafm/%s/%s %s" % (chan.attrib['id'], key.tag, key.text)
                # Since this is a dynamic value, remove retention
                persistent[chan]
                mqttc.publish("somafm/%s/%s" % (chan.attrib['id'], key.tag), key.text)
            except KeyError:
                # 1st run through, we assume everything is static
                metadata[chan.attrib['id']][key.tag] = key.text
                persistent[chan.attrib['id']][key.tag] = True
                print "ADDED  somafm/%s/%s %s" % (chan.attrib['id'], key.tag, key.text)
                mqttc.publish("somafm/%s/%s" % (chan.attrib['id'], key.tag), key.text, retain=True)

  if DEBUG:
     break
  time.sleep(60)
