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
from Queue import Empty
import time

class Grapher:

    def __init__(self, queue):
        self.queue = queue
        self.process = Process(target=self.plot_a_graph)
        self.process.daemon = True
        self.process.start()

    def plot_a_graph(self):
        i = 1
        max = 20
        plt.axis([0, 2, 0, max])
        plt.ion()
        plt.show()
        while True:
            try:
                msg = self.queue.get(False)
                # If `False`, the program is not blocked. `Queue.Empty` is thrown if
                # the queue is empty
                y = int(msg)
                if max < y:
                    max = y + 1
                plt.axis([0, i+1, 0, max])
                plt.scatter(i, y)
                print "Total: " + str(y)
                plt.draw()
                i += 1
            except Empty:
                msg = None

            time.sleep(0.5)