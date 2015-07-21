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

import csv
import os
from itertools import izip

filename = raw_input('filename: ')
with open(os.path.splitext(filename)[0] + '_t.csv', 'wb') as outfile, open(filename, 'rb') as infile:
    a = izip(*csv.reader(infile))
    csv.writer(outfile).writerows(a)