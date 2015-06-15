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
from datetime import timedelta
import matplotlib

# matplotlib.use("qt4agg")
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import multiprocessing
import time


def plot_a_graph():
    f, a = plt.subplots(1)
    line = plt.plot(range(10))
    print multiprocessing.current_process().name, "starting plot show process"  # print statement preceded by true process name
    plt.show()  # I think the code in the child will stop here until the graph is closed
    print multiprocessing.current_process().name, "plotted graph"  # print statement preceded by true process name
    time.sleep(4)


def keep_data_up_to_date():
    FMT = '%H:%M:%S'
    tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)


class Receiver:
    def __init__(self, graph, timeout, filename):
        self.graph = graph
        self.timeout = timeout
        self.current_time = datetime.datetime.now()
        self.devices = []
        self.time_strings = ['time', 'rssi', 'pi_id']
        self.pp = pprint.PrettyPrinter(indent=4)
        self.xml = ''
        self.file = open(filename, "wb")

    def __print_device__(self, adding, mac):
        if adding:
            status = "Adding\t"
        else:
            status = "Removing"
        print "{0}\t{1}".format(status, mac)


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

    def on_publish(self, mqttc, obj, mid):
        print("Published! " + str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed! - " + str(mid) + " " + str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        print(string)

### Helper functions
if __name__ == "__main__":
    # Handle args
    parser = argparse.ArgumentParser(
        description='This is to be usedin conjunction with the WifiScanner on a Raspberry Pi')
    parser.add_argument('--topic', metavar='base/sub', type=str, nargs='?',
                        help='Full topic to listen to. (Example "proximity/sensor")', default="proximity/#")
    parser.add_argument('--host', metavar='url', type=str, nargs='?',
                        help='UQL of MQTT server (default is CEIT winter).', default='winter.ceit.uq.edu.au')
    parser.add_argument('--graph', metavar='True/False', type=bool, nargs='?', help='Whether to print the data.',
                        default=True)
    parser.add_argument('--timeout', metavar='sec', type=int, nargs='?', help='How long the device will be remembered',
                        default=10)
    parser.add_argument('--file', metavar='filename', type=str, nargs='?',
                        help='Filename to save XML data', default='log.xml')
    args = parser.parse_args()
    # Create  a receiver instance
    receiver = Receiver(graph=args.graph, timeout=args.timeout, filename=args.file)
    # Create a graphing process
    # MQTT
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


