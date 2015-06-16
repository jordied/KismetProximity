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
import matplotlib.pyplot as plt
#let's try using multiprocessing instead of threading module:
from multiprocessing import Queue, Process
from datetime import datetime
from Queue import Empty
import time

class Grapher:

    def __init__(self, queue):
        self.queue = queue
        self.process = Process(target=self.plot_a_graph)
        self.process.daemon = True
        self.process.start()

    def plot_a_graph(self):
        start_time = datetime.now()
        i = 1
        y_max = 20
        plt.axis([0, 2, 0, y_max])
        plt.ion()
        plt.show()
        while True:
            try:
                msg = self.queue.get(False)
                y = int(msg)  # Might not be necessary but to be safe.
                tdiff = datetime.now() - start_time
                if y_max < y:
                    y_max = y + 1
                plt.axis([0, tdiff.seconds, 0, y_max])
                plt.scatter(tdiff.seconds, y)
                print "Total: " + str(y)
                plt.draw()
                i += 1
            except Empty:
                msg = None

            time.sleep(0.5)