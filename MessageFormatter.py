__author__ = 'Jordi'
import string
import logging
import time
from datetime import datetime

class MessageFormatter:
    """This Class is essentially the main class"""

    def __init__(self, id = 1):
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
                t = datetime.now()
                list_of_client_dict.append({'pi_id': self.id, 'year': t.date().year, 'month':t.date().month, 'date': t.date().day, 'hour': t.hour, 'minute': t.minute, 'second': t.second, 'MAC': mac, 'rssi': dbm})
                print '{0}\t{1}\t{2}'.format(time.strftime('%X %x %Z'), mac, dbm)
        return list_of_client_dict

