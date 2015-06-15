__author__ = 'Jordi'
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
import string
import logging
import time
from datetime import datetime


class MessageFormatter:
    """This Class is essentially the main class"""

    def __init__(self, id=1):
        logging.basicConfig(format='%(asctime)-15s::: %(message)s')
        self.logger = logging.getLogger('WiFiSniffer')
        self.id = id

    def __remove_control_chars__(self, s):
        return filter(lambda x: x in string.printable, s)  # control_char_re.sub('', s)

    def format_kismet_response(self, in_text):
        output = []
        # print "Original Text:\n", repr(intext)
        try:
            in_text.rstrip.split('\n')
        except AttributeError:
            pass
        for line in in_text:
            text = self.__remove_control_chars__(line)
            output.append(text)
        return ''.join(output)


    def get_client_list(self, text, interface_addr):
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
            except ValueError:
                dbm = 0
            if not interface_addr.lower() == mac.lower():
                format = "%H:%M:%S_%B_%d_%Y"
                list_of_client_dict.append(
                    {'pi_id': self.id, 'time':datetime.now().strftime(format), 'MAC': mac, 'rssi': dbm})
                print '{0}\t{1}\t{2}'.format(time.strftime('%X %x %Z'), mac, dbm)
        return list_of_client_dict

