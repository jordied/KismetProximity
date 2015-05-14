__author__ = 'Jordi'
import sys
import string
from subprocess import Popen, PIPE
import logging

import NoKismetError


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