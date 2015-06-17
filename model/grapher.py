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
import numpy as np
from multiprocessing import Process
from datetime import datetime
from Queue import Empty
import time
import itertools
import sys

class Manufacterer:

    def __init__(self, name, color, marker, line_style='-'):
        self.name = name
        self.color = color
        self.marker = marker
        self.line_style = line_style
        self.previous_val = 0
        self.count = 0
        self.ctime = 0
        self.ptime = 0


    def increment_count(self):
        self.count += 1

    def reset_count(self):
        self.previous_val = self.count
        self.count = 0

    def set_time(self, time):
        self.ptime = self.ctime
        self.ctime = time

class Grapher:

    def __init__(self, queue, man):
        self.man = man
        self.queue = queue
        self.markers = itertools.cycle(('x', '+', '.', 'o', '*'))
        self.colors = itertools.cycle(('b', 'g', 'r', 'm', 'y', 'k', 'Aqua', 'Chocolate', 'DeepPink', 'Lime', 'Purple'))
        self.lines = itertools.cycle((':', '-.', '--'))
        self.devs = []
        # Process
        self.process = Process(target=self.plot_a_graph)
        self.process.daemon = True
        self.process.start()

    def __set_man_style__(self, device):
        already_in = False
        for val in self.devs:
            if device['man'] == val.name:
                val.increment_count()
                already_in = True
        if not already_in:
            new_dev = Manufacterer(name=device['man'], color=self.colors.next(), marker=self.markers.next(), line_style=self.lines.next())
            print 'New manufacturer ({0}{1}): {2}'.format(new_dev.color, new_dev.marker, new_dev.name)
            self.devs.append(new_dev)

    def __draw_a_line__(self):
        for x in range(1, 80):
            sys.stdout.write('-')
        sys.stdout.write('\n')

    def __draw_points__(self, tdiff, devices):
        y_max = 1
        self.__draw_a_line__()
        for y, dev in enumerate(devices):
            self.__set_man_style__(dev)
        for val in self.devs:
            if val.count > y_max:
                y_max = val.count + 1
            val.set_time(tdiff.seconds)
            print "Found {0} {1} devices".format(val.count, val.name)
            x = np.array([val.ptime, val.ctime])
            y = np.array([val.previous_val, val.count])
            plt.plot(x, y, marker=val.marker, c=val.color, ms=5, ls=val.line_style)
        return y_max

    def plot_a_graph(self):
        start_time = datetime.now()
        # Set initial values
        y = 0
        y_max = 5
        # Setup Plot
        plt.axis([0, 2, 0, y_max])
        plt.ion()
        plt.show()
        while True:
            try:
                msg = self.queue.get(False)
                y = self.__draw_points__(tdiff, msg)
                for x in self.devs:
                    x.reset_count()
            except Empty:
                msg = None
            tdiff = datetime.now() - start_time
            # Increase height if necessary
            if y > y_max:
                y_max = y + 1
            plt.axis([0, tdiff.seconds, 0, y_max])
            plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=2, mode="expand", borderaxespad=0.)
            plt.draw()
            time.sleep(0.5)