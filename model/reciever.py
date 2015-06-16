# This file is part of Jordi Estivill-Dredge's Thesis at the University Of Queensland, known as KismetProximity.
#
# KismetProximity is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KismetProximity is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
__author__ = 'Jordi'
import argparse
import datetime
import json
import pprint
import dicttoxml
from lxml import etree
from grapher import Grapher

import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import multiprocessing
import time

class Receiver:
    def __init__(self, timeout, filename, queue):
        self.timeout = timeout
        self.current_time = datetime.datetime.now()
        self.devices = []
        self.time_strings = ['time', 'rssi', 'pi_id']
        self.pp = pprint.PrettyPrinter(indent=4)
        self.xml = ''
        self.file = open(filename, "wb")
        self.queue = queue

    def __print_device__(self, adding, mac):
        if adding:
            status = "Adding\t"
        else:
            status = "Removing"
        print "{0}\t{1}".format(status, mac)

    def __writer__(self, msg):
        ## Write to the queue
        self.queue.put(msg)             # Write 'count' numbers into the queue

    def on_connect(self, mqttc, obj, flags, rc):
        print("Connected! - " + str(rc))

    def on_message(self, mqttc, obj, msg):
        format = "%H:%M:%S_%B_%d_%Y"
        decoded = json.loads(msg.payload)
        for i, val in enumerate(decoded):
            already_stored = False
            for j, exi in enumerate(self.devices):
                if val['MAC'] == exi['MAC']:
                    for x in self.time_strings:
                        # Update the time.
                        self.devices[j][x] = val[x]
                        already_stored = True
                # print datetime.datetime.now()
                # print (datetime.datetime.strptime(exi['time'], format) + datetime.timedelta(seconds=self.timeout))
                if datetime.datetime.now() > (
                    datetime.datetime.strptime(exi['time'], format) + datetime.timedelta(seconds=self.timeout)):
                    # Haven't device in long enough
                    self.__print_device__(adding=False, mac=exi['MAC'])
                    self.devices.remove(exi)
            if not already_stored:
                self.__print_device__(adding=True, mac=val['MAC'])
                self.devices.append(val)
        # Now save as XML
        self.xml = dicttoxml.dicttoxml(self.devices, attr_type=False)
        tree = etree.fromstring(self.xml, etree.XMLParser())
        tree.set('id', datetime.datetime.now().strftime(format))
        self.file.write(etree.tostring(tree, pretty_print=True))
        self.queue.put_nowait(len(self.devices))

    def on_publish(self, mqttc, obj, mid):
        print("Published! " + str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed! - " + str(mid) + " " + str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        print(string)

def listener(queue, args):
    receiver = Receiver(timeout=args.timeout, filename=args.file, queue=queue)
    mqttc = mqtt.Client()
    mqttc.on_message = receiver.on_message
    mqttc.on_connect = receiver.on_connect
    mqttc.on_publish = receiver.on_publish
    mqttc.on_subscribe = receiver.on_subscribe
    # Uncomment to enable debug messages
    # mqttc.on_log = on_log
    mqttc.connect(args.host, 1883, 60)
    mqttc.subscribe(args.topic, 0)
    # Start to listen
    mqttc.loop_forever()

### Helper functions
if __name__ == "__main__":
    # Handle args
    parser = argparse.ArgumentParser(
        description='This is to be usedin conjunction with the WifiScanner on a Raspberry Pi')
    parser.add_argument('--topic', metavar='base/sub', type=str, nargs='?',
                        help='Full topic to listen to. (Example "proximity/sensor")', default="proximity/#")
    parser.add_argument('--host', metavar='url', type=str, nargs='?',
                        help='UQL of MQTT server (default is CEIT winter).', default='winter.ceit.uq.edu.au')
    parser.add_argument('--graph', action='store_true', help='Whether to graph the data.')
    parser.add_argument('--timeout', metavar='sec', type=int, nargs='?', help='How long the device will be remembered',
                        default=10)
    parser.add_argument('--file', metavar='filename', type=str, nargs='?',
                        help='Filename to save XML data', default='log.xml')
    parser.add_argument('--man', action='store_true',
                        help='Make a guess at the manufacturer')
    args = parser.parse_args()
    # Create a Multi Process Queue
    queue = multiprocessing.Queue()
    # Create a graphing process
    grapher = Grapher(queue)
     # MQTT process
    listener(queue, args)



