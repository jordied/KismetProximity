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

from MessageFormatter import MessageFormatter
from KismetInstance import KismetInstance
from MQTTHelper import MQTTHelper
import subprocess
import os
import signal

### My Class
class ProximityDetector:

    def __init__(self, scan_length=2, wait_between=1):
        self.scan = scan_length
        self.wait = wait_between

    def handle_argv(self, argv):
        i = 0
        self.hostname = 'winter.ceit.uq.edu.au'
        self.id = 1
        while i < len(argv):
            if argv[i] == '-s':
                try:
                    self.scan = argv[i+1]
                    i += 1
                except:
                    pass
            if argv[i] == '-w':
                try:
                    self.wait = argv[i + 1]
                    i += 1
                except:
                    pass
            if argv[i] == '-i':
                try:
                    self.id = argv[i + 1]
                    i += 1
                except:
                    pass
            if argv[i] == '-h':
                try:
                    self.hostname = argv[i + 1]
                    i += 1
                except:
                    pass
            i += 1

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
    ProximityDetector = ProximityDetector()
    ProximityDetector.handle_argv(sys.argv)
    MQTTHelper = MQTTHelper(host=ProximityDetector.hostname)
    formatter = MessageFormatter(id=ProximityDetector.id)
    while True:
        client_list = formatter.format_kismet_response(kismet_instance.run_scan(scan=ProximityDetector.scan, wait=ProximityDetector.wait))
        list_dict = formatter.get_client_list(client_list, kismet_instance.get_hw_Addr('wlan0'))
        MQTTHelper.send(list_dict)

