__author__ = 'Jordi'
import sys
import string
from subprocess import Popen, PIPE
import logging

import NoKismetError

### My Class

class WiFiSniffer:
    """This Class is essentially the main class"""

    def __init__(self, argv):
        logging.basicConfig(format='%(asctime)-15s::: %(message)s')
        self.logger = logging.getLogger('WiFiSniffer')
        self.__double_check_argv(argv)

    def __double_check_argv(self, argv):
        """
        Set parameters for class.
        :param argv:
        :return:
        """
        for x in range(1, len(argv)):
            if (argv[x] == "-nokismet"):
                self.example = True;
                self.logger.debug('Running with no kismet.')
            elif argv[x] == "-d":
                self.logger.setLevel(10)
                self.logger.debug('Setting log level to debug')
            elif argv[x] == "-i":
                self.logger.setLevel(20)
                self.logger.debug('Setting log level to info')
            elif argv[x] == "-w":
                self.logger.setLevel(30)
                self.logger.debug('Setting log level to warning')

    def __remove_control_chars(self, s):
        return filter(lambda x: x in string.printable, s)  # control_char_re.sub('', s)


    def __run_kismet(self):
        """
        :return:
        """
        shell = ['/bin/bash', 'sudo', 'kismet_server']
        self.logger.debug('Attempting to run: %s', " ".join(shell))
        kismet = Popen(shell, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = kismet.communicate()
        if kismet.returncode != 0:
            raise NoKismetError("No kismet install was found on this computer.\nPlease install kismet.")
        return kismet

    def __get_kismet_response(self):
        """
        Get a list of clients from kismet if -d was specifided.
        Otherwise will return some dummy data as an example.
        :return:
        """
        if (self.example == True):
            f = open('resources/kismet_example.txt', 'r')
            output = f.read()
        else:
            p = Popen(
                ['/bin/bash', '-i', '-c',
                 'echo -e \'!0 enable client MAC,manuf,signal_dbm,signal_rssi\' | nc localhost 2501'],
                stdin=PIPE, stdout=PIPE, stderr=PIPE)
            kisout, err = p.communicate()
            rc = p.returncode
            if rc != 0:
                sys.exit("Something bad happened when fetching client list from kismet.")
            output = self.format_kismet_response(kisout)
        return output

    def __format_kismet_response(self, inText):
        output = []
        # print "Original Text:\n", repr(intext)
        try:
            inText.rstrip.split('\n')
        except AttributeError:
            pass
        for line in inText:
            text = self.__remove_control_chars(line)
            output.append(text)
        return ''.join(output)

    def run_scan(self):
        return self.__format_kismet_response(self.__get_kismet_response());
