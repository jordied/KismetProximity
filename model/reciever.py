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
import cmd
import multiprocessing
from multiprocessing import Process
from threading import Thread
from datetime import datetime, timedelta
from Queue import Empty
import time
import itertools
import csv
import signal

import dicttoxml
from lxml import etree
from netaddr import *
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
import numpy as np


# Process list

processes = []


class UserInputMonitor(cmd.Cmd):
    """
    Class which monitors and interprets user input.
    """
    def cmdloop(self, queue):
        self.id = 0
        self.person_count = 0
        self.ui_queue = queue
        return cmd.Cmd.cmdloop(self)

    def put_value(self):
        """
        Put the user's input into a queue so it can be handled by another process.
        :return:
        """
        self.ui_queue.put_nowait(self.person_count)

    def _print_people(self):
        print "{0} People".format(self.person_count)
        self.put_value()

    #Add
    def do_add(self, input):
        if input:
            print input
            try:
                self.person_count += int(input)
            except:
                print '{0} is not valid'.format(input)
            self._print_people()


    def help_add(self):
        print '\n'.join(['add [num]', 'Add the number to the current total', ])
    # Subtract
    def do_sub(self, input):
        if input:
            print input
            try:
                self.person_count -= int(input)
            except:
                print '{0} is not valid'.format(input)
            self._print_people()

    def help_sub(self):
        print '\n'.join(['sub [num]', 'Subtract the number to the current total', ])
    # Total
    def do_tot(self, input):
        if input:
            print input
            try:
                self.person_count = int(input)
            except:
                print '{0} is not valid'.format(input)
            self._print_people()

    def help_tot(self):
        print '\n'.join(['tot [num]', 'Subtract the number to the current total', ])
    # Exit
    def do_quit(self, input):
        print 'Exiting...'
        for p in processes:
            p.terminate()
        exit(0)

    def help_quit(self):
        print '\n'.join(['quit', 'Quit the application', ])
    # Exit
    def do_save(self, input):
        if input:
            if '.' not in input:
                # No file extension provided, add the default
                input.append('.csv')
        else:
            filename = 'logs/log_{0}_{1}.csv'.format(datetime.now().strftime("%H_%M_%S_%B_%d_%Y"), self.id)
        print 'Saving to ' + filename
        self.ui_queue.put_nowait(filename)

    def help_save(self):
        print '\n'.join(['save [filename]', 'Save the current graph to filename', ])


class Receiver:
    """
    Class which handles aspects of the MQTT
    """
    def __init__(self, timeout, file, send_queue, logger):
        """
        :param timeout: The timeout for the connection
        :param file: The filename which will save all teh data in XML format.
        :param send_queue: The queue to place the data in so it can be graphed.
        :param logger: The Python Logger instance which will log information.
        :return:
        """
        self.logger = logger
        self.timeout = timeout
        self.current_time = datetime.now()
        self.devices = []
        self.time_strings = ['time', 'rssi', 'pi_id']
        self.pp = pprint.PrettyPrinter(indent=4)
        self.file = file
        self.send_queue = send_queue

    def _print_device(self, adding, device):
        """
        :param adding: Boolean to determine whether a device is being added or removed.
        :param device: The Dictionary which hodls the information about the device.
        :return:
        """
        if adding:
            status = "Adding"
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

    def on_connect(self, mqttc, obj, flags, rc):
        """
        :param mqttc: Used by Paho MQTT
        :param obj: Used by Paho MQTT
        :param flags: Used by Paho MQTT
        :param rc: Used by Paho MQTT
        :return:
        """
        self.logger.debug("Connected! - " + str(rc))

    def on_message(self, mqttc, obj, msg):
        """
        Callback which is used when a message is recieved.
        :param mqttc: Used by Paho MQTT
        :param obj: Used by Paho MQTT
        :param msg: Used by Paho MQTT (The String which is the message which was received)
        :return:
        """
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
                    # self._print_device(adding=False, device=exi)
                    self.devices.remove(exi)
            if not already_stored:
                try:
                    mac = EUI(val['MAC'])
                    oui = mac.oui
                    val['man'] = oui.registration().org
                except NotRegisteredError:
                    val['man'] = 'UNKNOWN'
                # self._print_device(adding=True, device=val)
                self.devices.append(val)
        # Now save as XML
        tmp_xml = dicttoxml.dicttoxml(self.devices, attr_type=False)
        tree = etree.fromstring(tmp_xml, etree.XMLParser())
        tree.set('id', datetime.now().strftime(format))
        self.file.write(etree.tostring(tree, pretty_print=True))
        self.send_queue.put_nowait(self.devices)

    def on_publish(self, mqttc, obj, mid):
        """
        Callback for when something is published.
        :param mqttc: Used by Paho MQTT
        :param obj: Used by Paho MQTT
        :param mid: Used by Paho MQTT
        :return:
        """
        self.logger.debug("Published! " + str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        """
        :param mqttc: Used by Paho MQTT
        :param obj: Used by Paho MQTT
        :param mid: Used by Paho MQTT
        :param granted_qos: Used by Paho MQTT
        :return:
        """
        self.logger.debug("Subscribed! - " + str(mid) + " " + str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        """
        :param mqttc: Used by Paho MQTT
        :param obj: Used by Paho MQTT
        :param level: Used by Paho MQTT
        :param string: Used by Paho MQTT
        :return:
        """
        self.logger.info(string)

def listener_process(send_queue, args, logger):
    """

    :param send_queue: The queue to send the MQTT received information upon.
    :param args: The arguement list passed to the program.
    :param logger: The Python Logger which handles the logging.
    :return:
    """
    with open((args.logfile + '.xml'), "wb") as file:
        receiver = Receiver(timeout=args.timeout, file=file, send_queue=send_queue, logger=logger)
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

def listener(send_queue, args, logger):
    """
    Function which starts a process for the MQTT
    :param send_queue: Queue which handles passing teh data.
    :param args: The programs argument list.
    :param logger: The Python Logger instance.
    :return:
    """
    process = Process(target=listener_process, args=(send_queue, args, logger))
    process.daemon = True
    process.start()
    processes.append(process)



class Manufacterer:
    def __init__(self, logger, ax, name, color, marker, line_style='-'):
        """
        This class is a manufacter which is used to contain the details of the line. i.e. x,y values.
        :param logger: The Python Logger which will log data.
        :param ax: The pyplot axis.
        :param name: The name of teh manufacturer as a String.
        :param color: The colour of the marker
        :param marker: The marker's style.
        :param line_style: The linestyle for the manufacterer.
        :return:
        """
        self.name = name
        self.count = 0
        self.x_values = [0]
        self.y_values = [0]
        self.line, = ax.plot(self.x_values, self.y_values, marker=marker, c=color, ms=5, ls=line_style, label=name)
        self.logger = logger
        self.logger.debug('New manufacturer ({0}{1}): {2}'.format(color, marker, name))


    def increment_count(self):
        """
        Increments the count.
        :return:
        """
        self.count += 1

    def reset_count(self):
        """
        Resets the current count and saves the previous.
        :return:
        """
        self.previous_val = self.count
        self.count = 0

    def set_data(self, t):
        """
        Sets the x and y as parts of the numpy array.
        :param t: The current time passed in seconds (int)
        :return:
        """
        self.x_values.append(t)
        self.y_values.append(self.count)
        # Update the graph
        self.line.set_xdata(np.array(self.x_values))
        self.line.set_ydata(np.array(self.y_values))


class Grapher:
    def __init__(self, MQTT_queue, ui_queue, logger, period, filename):
        self.file_id = 0
        self.filename = filename
        self.logger = logger
        self.MQTT_queue = MQTT_queue
        self.ui_queue = ui_queue
        self.markers = itertools.cycle(('x', '+', '.', 'o', '*'))
        self.colors = itertools.cycle(('b', 'g', 'r', 'm', 'y', 'k', 'Aqua', 'Chocolate', 'DeepPink', 'Lime', 'Purple'))
        self.lines = itertools.cycle((':', '-.', '--'))
        self.period = period
        self.devs = []
        # Process
        self.process = Process(target=self.plot_a_graph)
        self.process.daemon = True
        self.process.start()
        processes.append(self.process)

    def _set_man_style(self, ax, device):
        already_in = False
        for val in self.devs:
            if device['man'] == val.name:
                val.increment_count()
                already_in = True
        if not already_in:
            new_dev = Manufacterer(logger=logging.getLogger('Manufacturer'), ax=ax, name=device['man'],
                                   color=self.colors.next(), marker=self.markers.next(),
                                   line_style=self.lines.next())
            self.devs.append(new_dev)

    def _draw_device_points(self, ax, tdiff, devices):
        y_max = 1
        for y, dev in enumerate(devices):
            self._set_man_style(ax, dev)
        for val in self.devs:
            if val.count > y_max:
                y_max = val.count + 1
            val.set_data(tdiff.seconds)
            # print "Found {0} {1} devices".format(val.count, val.name)
        return y_max

    def _draw_ui_point(self, ax, tdiff, count, man_count):
        y_max = 1
        if man_count.count > y_max:
            y_max = man_count.count + 1
        man_count.count = count
        man_count.set_data(tdiff.seconds)
        # print "Found {0} {1} devices".format(val.count, val.name)
        return y_max

    def _draw_legend(self, ax):
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        leg = plt.gca().get_legend()
        plt.setp(leg.get_texts(), fontsize='small')

    def save_data(self, fname):
        print '\n' \
              '---------------------------------------\n' \
              'SAVING DATA INTO {0}\n'.format(fname)
        with open(fname, 'wb') as f:
            writer = csv.writer(f, delimiter=',')
            for line in plt.gca().get_lines():
                xd = ['Time']
                xd.extend(line.get_xdata().tolist())
                yd = [line.get_label()]
                yd.extend(line.get_ydata().tolist())
                writer.writerow(xd)
                writer.writerow(yd)
        self.file_id += 1
        print 'DONE!!!\n' \
              '---------------------------------------\n'

    def _dump_data(self, signal, frame):
        self.save_data(self.filename + '_' + str(self.file_id) + '.csv')
        plt.close('all')
        exit(0)




    def plot_a_graph(self):
        # Dump data to file in case of exit
        signal.signal(signal.SIGTERM, self._dump_data)
        start_time = datetime.now()
        # Set initial values
        fig = plt.figure(num=None, figsize=(16, 8), dpi=80)
        ax = plt.subplot(111)
        y = 0
        z = 0
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
        # Create UI Manufacterer
        man_count = Manufacterer(logger=logging.getLogger('UI'), ax=ax, name='Manual_Count', color='r', marker='x',
                                 line_style='-')
        while True:
            # Get data from MQTT
            try:
                msg = self.MQTT_queue.get(False)
                y = self._draw_device_points(ax, tdiff, msg)
                for x in self.devs:
                    x.reset_count()
            except Empty:
                pass
            # Try and get from UI
            try:
                ui = self.ui_queue.get(False)
                if isinstance(ui, str):
                    self.save_data(fname=ui)
                else:
                    z = self._draw_ui_point(ax, tdiff, ui, man_count)

            except Empty:
                pass
            self._draw_legend(ax)
            # Get ready to plot
            tdiff = datetime.now() - start_time
            # Increase height if necessary
            if y > y_max:
                y_max = y + 1
            if z > y_max:
                y_max = z + 1
            # Update the graph and show
            ax.axis([0, tdiff.seconds + self.period, 0, y_max])
            plt.draw()
            time.sleep(self.period)

# Register the Control+C event to be ignored
def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

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
    parser.add_argument('--logfile', metavar='filename', type=str, nargs='?',
                        help='Save the logfile generated by this program',
                        default='logs/log_{0}'.format(datetime.now().strftime("%H_%M_%S_%B_%d_%Y")))
    parser.add_argument('--loglevel', metavar='N', type=int, nargs='?', help='Log level as 0, 10 , 20, 30, 40 or 50',
                        default=0)
    args = parser.parse_args()
    logging.basicConfig(filename=(args.logfile + '.log'), format='%(asctime)-15s::%(levelname)s:: %(message)s',
                        level=args.loglevel)
    # Create a Multi Process Queue
    MQTT_to_Graph = multiprocessing.Queue()
    UI_to_Graph = multiprocessing.Queue()
    # This program uses multiprocessing so I will create the following pool
    # Create a graphing process
    listener(MQTT_to_Graph, args, logging.getLogger('MQTT_Listener'))
    if args.graph:
        grapher = Grapher(MQTT_to_Graph, UI_to_Graph, logging.getLogger('Graph'), (1 / float(args.freq)),
                          filename=(args.logfile))
    thread = Thread(target=UserInputMonitor().cmdloop, args=(UI_to_Graph,))
    thread.start()
    thread.join()
    for process in processes:
        process.join()


