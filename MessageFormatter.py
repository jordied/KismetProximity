__author__ = 'Jordi'
import string
import logging
from datetime import datetime
class MessageFormatter:
    """This Class is essentially the main class"""

    def __init__(self):
        logging.basicConfig(format='%(asctime)-15s::: %(message)s')
        self.logger = logging.getLogger('WiFiSniffer')

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

    def get_client_list(self, text):
        list_of_clients = []
        list_of_client_dict = []
        for item in text.split("\n"):
            if "*CLIENT:" in item:
                list_of_clients.append(item)
        for x in list_of_clients:
            z = x.split()
            mac = z[1]
            t = datetime.now()
            list_of_client_dict.append({'year': t.date().year, 'month':t.date().month, 'date': t.date().day, 'hour': t.hour, 'minute': t.minute, 'second': t.second, 'MAC': mac})
        return list_of_client_dict

