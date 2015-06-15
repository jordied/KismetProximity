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
import subprocess
import os
import signal
import argparse

from MessageFormatter import MessageFormatter
from KismetInstance import KismetInstance
from MQTTHelper import MQTTHelper


def signal_handler(signal, frame):
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


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    kismet_instance = KismetInstance()
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
    args = parser.parse_args()
    # Begin
    MQTTHelper = MQTTHelper(host=args.host)
    formatter = MessageFormatter(id=args.id)
    while True:
        client_list = formatter.format_kismet_response(kismet_instance.run_scan(scan=args.scan, wait=args.wait))
        list_dict = formatter.get_client_list(client_list, kismet_instance.get_hw_Addr('wlan0'))
        MQTTHelper.send(list_dict)

