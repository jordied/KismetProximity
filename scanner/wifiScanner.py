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
# along with KismetProximity.  If not, see <http://www.gnu.org/licenses/>.

import sys
import argparse
import string
import json
import logging
import signal
import os
import time
import subprocess
import socket
import fcntl
import struct
from datetime import datetime
from subprocess import Popen, PIPE

import paho.mqtt.publish as publish


def signal_handler(signal, frame):
    """
    This function handles the event of a control-c event.
    :param signal: The signal that will be handled
    :param frame:
    :return: Exit's the system
    """
    print '\nExiting! Killing all Kismet Instances...'
    p_list = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p_list.communicate()
    for line in out.splitlines():
        if 'kismet' in line:
            print 'Found: ' + line + ' ...',
            pid = int(line.split(None, 1)[0])
            os.killpg(os.getpgid(pid), 9)
            print 'DONE'
    sys.exit(0)


class KismetInstance:
    """This Class contains an instance of kismet"""

    def __init__(self, logger, value=False):
        self.logger = logger
        self.logger.debug('Setting log level to warning')
        self.example = value

    def __create_kismet_instance__(self):
        """
        Create a kismet_server subprocess.
        :return:
        """
        shell = ['sudo', '/usr/local/bin/kismet_server']
        self.logger.debug('Attempting to run: %s', " ".join(shell))
        self.kismet = Popen(shell, stdin=PIPE, stdout=PIPE, stderr=PIPE, cwd=r'./logs', preexec_fn=os.setsid,
                            shell=False)

    def __destroy_kismet_instance__(self):
        """
        Kill the subprocess
        :return:
        """
        sig = signal.SIGKILL
        os.killpg(os.getpgid(self.kismet.pid), sig)  # Kill one of them
        p_list = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
        out, err = p_list.communicate()
        for line in out.splitlines():
            if 'kismet' in line:
                pid = int(line.split(None, 1)[0])
                self.logger.warning("Found: %d", pid)
                try:
                    os.killpg(os.getpgid(pid), sig)
                except:
                    msg = 'Failed to kill a kismet instance! PID:{0} '.format(pid)
                    self.logger.error(msg)
                    print msg


    def __get_raw_kismet_response__(self):
        """
        Get a list of clients from kismet.
        Or if usign example, will return some dummy data as an example.
        :return:
        """
        if self.example:
            f = open('resources/kismet_example.txt', 'r')
            output = f.read()
        else:
            p = Popen(
                ['/bin/bash', '-i', '-c',
                 'echo -e \'!0 enable client MAC,manuf,signal_dbm,signal_rssi\' | nc localhost 2501'],
                stdin=PIPE, stdout=PIPE, stderr=PIPE)
            output, err = p.communicate()
            rc = p.returncode
            if rc != 0:
                self.logger.warning("Something bad happened when fetching client list from kismet.")
        return output

    def get_hw_Addr(self, ifname='wlan0'):
        """
        This gets the Mac Address of the current network interface. So it can be removed from the list of devices that were detected.
        :param ifname:
        :return: the Mac address of the interface name
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        info = fcntl.ioctl(s.fileno(), 0x8927, struct.pack('256s', ifname[:15]))
        return ':'.join(['%02x' % ord(char) for char in info[18:24]])


    def run_scan(self, scan=2, wait=1):
        """
        Runs a kismet WiFi scan for nearby active WiFi devices
        :param scan: The time in seconds (can be a float) to hold a scan.
        :param wait: The time in seconds(can be float) to wait between each scan.
        :return:
        """
        self.__create_kismet_instance__()
        time.sleep(float(scan))
        text = self.__get_raw_kismet_response__()
        self.__destroy_kismet_instance__()
        time.sleep(float(wait))
        return text


class MessageFormatter:
    """
    This class formats strings returned from kismet and gets a list of clients.
    """

    def __init__(self, logger, id=1, findDevice=None):
        """
        Initialise the class
        :param logger: The logger object to use.
        :param id: The scanner's ID. Allows you to have multiple scanners
        :return:
        """
        self.logger = logger
        self.id = id
        self.findDevice = findDevice

    def __remove_control_chars__(self, s):
        """
        Removes the unnecessary, unprintable characters from the kismet response.
        :param s: The string with unprintable characters in it
        :return: the string with the characters removed.
        """
        return filter(lambda x: x in string.printable, s)  # control_char_re.sub('', s)

    def format_kismet_response(self, in_text):
        """

        :param in_text: The raw kismet input
        :return: A better formatted response with unprintable characters removed.
        """
        output = []
        try:
            in_text.rstrip.split('\n')
        except AttributeError:
            pass
        for line in in_text:
            text = self.__remove_control_chars__(line)
            output.append(text)
        return ''.join(output)

    def get_client_list(self, text, interface_addr):
        """
        Takes the text of the kismet response and transforms it into a list of dictionaries of devices.
        :param text: The text that has had the unnecessary characters removed.
        :param interface_addr: The interfaces mac address so it won't be added to the list.
        :return: A list of dictionaries containing all the devices that were detected.
        """
        list_of_clients = []
        list_of_client_dict = []
        for item in text.split("\n"):
            if "*CLIENT:" in item:
                list_of_clients.append(item)
        for x in list_of_clients:
            z = x.split()
            mac = z[1]
            try:
                dbm = int(z[3])
            except:
                dbm = 0
            if not interface_addr.lower() == mac.lower():
                format = "%H:%M:%S_%B_%d_%Y"
                list_of_client_dict.append(
                    {'pi_id': self.id, 'time': datetime.now().strftime(format), 'MAC': mac, 'rssi': dbm})
                msg = '{0}\t{1}\t{2}'.format(time.strftime('%X %x %Z'), mac, dbm)
                print type(mac)
                self.logger.debug(msg)
                if self.findDevice is None:
                    print msg
                elif self.findDevice == mac:
                    msg += '*********'
                    print msg
        return list_of_client_dict


class MQTTHelper:
    """
    This class handles sending over MQTT to the server.
    """

    def __init__(self, logger, host='winter.ceit.uq.edu.au', base_topic='proximity', sub_topic='sensor'):
        """

        :param logger: The logging class to help log information
        :param host: The URL of the MQTT server
        :param base_topic: The base topic to use
        :param sub_topic: The sub_topic to use
        :return:
        """
        self.host = host
        self.full_topic = base_topic + '/' + sub_topic
        self.logger = logger
    def send(self, message, is_json=False):
        """
        Takes a message and sends it over MQTT
        :param message: Send this message over MQTT
        :param is_json: let the function know if it is already formatted as json.
        :return:
        """
        if not is_json:
            message = json.dumps(message, ensure_ascii=True, )
        self.logger.debug("Sending MQTT message: " + message + ", to " + self.host)
        try:
            publish.single(self.full_topic, message, hostname=self.host)
        except:
            # Failed to send over MQTT
            e_message = 'Failed publishing to {0}'.format(self.host)
            self.logger.error(e_message)
            print e_message


if __name__ == "__main__":
    if os.getuid() != 0:
        print(
            "***** ERROR! *****\nThis program" +
            " requires root privileges, re-run with sudo. Use the flag '-h' for more help.")
        sys.exit(1)
    signal.signal(signal.SIGINT, signal_handler)
    # Handle Arguements
    parser = argparse.ArgumentParser(
        description='Using a Raspberry Pi, scan the nearby environemnt for active WiFi devices and post on MQTT')
    parser.add_argument('--scan', metavar='sec', type=int, nargs='?', help='Scan duration in seconds (default of 3).',
                        default=3)
    parser.add_argument('--wait', metavar='sec', type=int, nargs='?', help='Wait duration in seconds (default of 1).',
                        default=1)
    parser.add_argument('--id', metavar='N', type=int, nargs='?', help='ID of scanner (default of 1).', default=1)
    parser.add_argument('--host', metavar='url', type=str, nargs='?',
                        help='UQL of MQTT server (default is CEIT winter).', default='winter.ceit.uq.edu.au')
    parser.add_argument('--logfile', metavar='filename', type=str, nargs='?',
                        help='Save the logfile generated by this program', default='log.txt')
    parser.add_argument('--loglevel', metavar='N', type=int, nargs='?', help='Log level as 0, 10 , 20, 30, 40 or 50',
                        default=30)
    parser.add_argument('--findDevice', metavar='N', type=int, nargs='?', help='Look for a particular MAC',
                        default=None)
    args = parser.parse_args()
    # Begin
    logging.basicConfig(filename=args.logfile, format='%(asctime)-15s::%(levelname)s:: %(message)s',
                        level=args.loglevel)
    root_logger = logging.getLogger('WiFiScanner')
    kismet_instance = KismetInstance(logger=logging.getLogger('kismet'))
    MQTTHelper = MQTTHelper(logger=logging.getLogger('MQTT_Helper'), host=args.host)
    formatter = MessageFormatter(logger=logging.getLogger('Message_Formatter'), id=args.id, findDevice=args.findDevice)
    wlan_addr = kismet_instance.get_hw_Addr('wlan0')
    root_logger.warning("Program Starting!")
    while True:
        client_list = formatter.format_kismet_response(kismet_instance.run_scan(scan=args.scan, wait=args.wait))
        list_dict = formatter.get_client_list(client_list, wlan_addr)
        MQTTHelper.send(list_dict)

