__author__ = 'Jordi'

import logging
import signal
import os
from subprocess import Popen, PIPE
import time
import subprocess



class KismetInstance:
    """This Class is essentially the main class"""

    def __init__(self, value=False):
        logging.basicConfig(format='%(asctime)-15s::: %(message)s')
        self.logger = logging.getLogger('kismet_instance')
        self.logger.debug('Setting log level to warning')
        self.example = value

    def __create_kismet_instance__(self):
        """
        Create a kismet_server subprocess.
        :return:
        """
        shell = ['sudo', '/usr/local/bin/kismet_server']
        self.logger.debug('Attempting to run: %s', " ".join(shell))
        self.kismet = Popen(shell, stdin=PIPE, stdout=PIPE, stderr=PIPE, cwd=r'./logs', preexec_fn=os.setsid, shell=False)

    def __destroy_kismet_instance__(self):
        """
        Kill the subprocess
        :return:
        """
        sig = signal.SIGKILL
        os.killpg(os.getpgid(self.kismet.pid), sig) # Kill one of them
        p_list = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
        out, err = p_list.communicate()
        for line in out.splitlines():
            if 'kismet' in line:
                pid = int(line.split(None, 1)[0])
                self.logger.debug("Found: %d", pid)
                os.killpg(os.getpgid(pid), sig)



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

    def run_scan(self):
        self.__create_kismet_instance__()
        time.sleep(2)
        text = self.__get_raw_kismet_response__()
        self.__destroy_kismet_instance__()
        return text
