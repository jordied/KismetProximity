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
import json
import pprint
import logging
import multiprocessing
from multiprocessing import Process
from datetime import datetime, timedelta
from Queue import Empty
import time
import itertools
import sys

import dicttoxml
from lxml import etree
from netaddr import *
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
import numpy as np


class Receiver:
    def __init__(self, timeout, filename, queue, logger):
        self.logger = logger
        self.timeout = timeout
        self.current_time = datetime.now()
        self.devices = []
        self.time_strings = ['time', 'rssi', 'pi_id']
        self.pp = pprint.PrettyPrinter(indent=4)
        self.file = open(filename, "wb")
        self.queue = queue

    def __print_device__(self, adding, device):
        if adding:
            status = "Adding\t"
        else:
            status = "Removing"
        try:
            mac = device['MAC']
        except KeyError:
            mac = 'UNKNOWN-MAC'
        try:
            man = device['man']
        except KeyError:
            man = 'UNKNOWN-MAN'
        self.logger.info("{0}\t{1}\t{2}".format(status, mac, man))

    def __writer__(self, msg):
        ## Write to the queue
        self.queue.put(msg)  # Write 'count' numbers into the queue

    def on_connect(self, mqttc, obj, flags, rc):
        self.logger.debug("Connected! - " + str(rc))

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
                if datetime.now() > (
                            datetime.strptime(exi['time'], format) + timedelta(seconds=self.timeout)):
                    # Haven't seen device in long enough
                    # self.__print_device__(adding=False, device=exi)
                    self.devices.remove(exi)
            if not already_stored:
                try:
                    mac = EUI(val['MAC'])
                    oui = mac.oui
                    val['man'] = oui.registration().org
                except NotRegisteredError:
                    val['man'] = 'UNKNOWN'
                # self.__print_device__(adding=True, device=val)
                self.devices.append(val)

        # Now save as XML
        tmp_xml = dicttoxml.dicttoxml(self.devices, attr_type=False)
        tree = etree.fromstring(tmp_xml, etree.XMLParser())
        tree.set('id', datetime.now().strftime(format))
        self.file.write(etree.tostring(tree, pretty_print=True))
        self.queue.put_nowait(self.devices)

    def on_publish(self, mqttc, obj, mid):
        self.logger.debug("Published! " + str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        self.logger.debug("Subscribed! - " + str(mid) + " " + str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        self.logger.info(string)


def listener(queue, args, logger):
    receiver = Receiver(timeout=args.timeout, filename=args.file, queue=queue, logger=logger)
    mqttc = mqtt.Client()
    mqttc.on_message = receiver.on_message
    mqttc.on_connect = receiver.on_connect
    mqttc.on_publish = receiver.on_publish
    mqttc.on_subscribe = receiver.on_subscribe
    # Uncomment to enable debug messages
    # mqttc.on_log = on_log
    logger.debug("Connecting to {0} on port 1833 with topic as {1}".format(args.host, args.topic))
    mqttc.connect(args.host, 1883, 60)
    mqttc.subscribe(args.topic, 0)
    # Start to listen
    mqttc.loop_forever()


class Manufacterer:
    def __init__(self, logger, ax, name, color, marker, line_style='-'):
        self.name = name
        self.count = 0
        self.x_values = [0]
        self.y_values = [0]
        self.line, = ax.plot(self.x_values, self.y_values, marker=marker, c=color, ms=5, ls=line_style, label=name)
        self.logger = logger
        self.logger.debug('New manufacturer ({0}{1}): {2}'.format(color, marker, name))


    def increment_count(self):
        self.count += 1

    def reset_count(self):
        self.previous_val = self.count
        self.count = 0

    def set_data(self, time):
        self.x_values.append(time)
        self.y_values.append(self.count)
        # Update the graph
        self.line.set_xdata(np.array(self.x_values))
        self.line.set_ydata(np.array(self.y_values))


class Grapher:
    def __init__(self, queue, logger, period):
        self.logger = logger
        self.queue = queue
        self.markers = itertools.cycle(('x', '+', '.', 'o', '*'))
        self.colors = itertools.cycle(('b', 'g', 'r', 'm', 'y', 'k', 'Aqua', 'Chocolate', 'DeepPink', 'Lime', 'Purple'))
        self.lines = itertools.cycle((':', '-.', '--'))
        self.period = period
        self.devs = []
        # Process
        self.process = Process(target=self.plot_a_graph)
        self.process.daemon = True
        self.process.start()

    def __set_man_style__(self, ax, device):
        already_in = False
        for val in self.devs:
            if device['man'] == val.name:
                val.increment_count()
                already_in = True
        if not already_in:
            new_dev = Manufacterer(logger=logging.getLogger('Manufacturer'), ax=ax, name=device['man'], color=self.colors.next(), marker=self.markers.next(),
                                   line_style=self.lines.next())
            self.devs.append(new_dev)

    def __draw_points__(self, ax, tdiff, devices):
        y_max = 1
        for y, dev in enumerate(devices):
            self.__set_man_style__(ax, dev)
        for val in self.devs:
            if val.count > y_max:
                y_max = val.count + 1
            val.set_data(tdiff.seconds)
            # print "Found {0} {1} devices".format(val.count, val.name)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        leg = plt.gca().get_legend()
        plt.setp(leg.get_texts(), fontsize='small')
        return y_max

    def plot_a_graph(self):
        start_time = datetime.now()
        # Set initial values
        fig = plt.figure(num=None, figsize=(16, 8), dpi=80)
        ax = plt.subplot(111)
        y = 0
        y_max = 5
        # Setup Plot
        ax.axis([0, self.period, 0, y_max])
        plt.xlabel('Time (s)')
        plt.ylabel('Device Count')
        plt.title('Number of Active Devices Detected')
        plt.ion()
        plt.show()
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        while True:
            try:
                msg = self.queue.get(False)
                y = self.__draw_points__(ax, tdiff, msg)
                for x in self.devs:
                    x.reset_count()
            except Empty:
                msg = None
            tdiff = datetime.now() - start_time
            # Increase height if necessary
            if y > y_max:
                y_max = y + 1
            ax.axis([0, tdiff.seconds + self.period, 0, y_max])
            plt.draw()
            time.sleep(self.period)

### Helper functions
if __name__ == "__main__":
    # Handle args
    parser = argparse.ArgumentParser(
        description='This is to be used in conjunction with the WifiScanner on a Raspberry Pi')
    parser.add_argument('--topic', metavar='base/sub', type=str, nargs='?',
                        help='Full topic to listen to. (Example "proximity/sensor")', default="proximity/#")
    parser.add_argument('--host', metavar='url', type=str, nargs='?',
                        help='UQL of MQTT server (default is CEIT winter).', default='winter.ceit.uq.edu.au')
    parser.add_argument('--graph', action='store_false', help='Do not graph the data.')
    parser.add_argument('--timeout', metavar='sec', type=int, nargs='?', help='How long the device will be remembered',
                        default=10)
    parser.add_argument('--freq', metavar='Hz', type=int, nargs='?', help='Frequency of graph updating, default 2Hz',
                        default=2.0)
    parser.add_argument('--file', metavar='filename', type=str, nargs='?',
                        help='Filename to save XML data',
                        default='logs/log_{0}.xml'.format(datetime.now().strftime("%H_%M_%S_%B_%d_%Y")))
    parser.add_argument('--logfile', metavar='filename', type=str, nargs='?',
                        help='Save the logfile generated by this program', default='log.txt')
    parser.add_argument('--loglevel', metavar='N', type=int, nargs='?', help='Log level as 0, 10 , 20, 30, 40 or 50', default=30)
    args = parser.parse_args()
    logging.basicConfig(filename=args.logfile, format='%(asctime)-15s::%(levelname)s:: %(message)s', level=args.loglevel)
    # Create a Multi Process Queue
    queue = multiprocessing.Queue()
    # Create a graphing process
    if args.graph:
        grapher = Grapher(queue, logging.getLogger('Graph'), (1/float(args.freq)))
        # MQTT process
    listener(queue, args, logging.getLogger('MQTT_Listener'))

