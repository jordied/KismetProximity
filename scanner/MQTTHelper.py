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
__author__ = 'Jordi'

import paho.mqtt.publish as publish
import json
import logging


class MQTTHelper:
    def __init__(self, host='winter.ceit.uq.edu.au', base_topic='proximity', sub_topic='sensor'):
        self.host = host
        self.full_topic = base_topic + '/' + sub_topic
        self.logger = logging.getLogger('MQTTHelper')

    def send(self, message, is_json=False):
        if not is_json:
            message = json.dumps(message, ensure_ascii=True, )
        self.logger.debug("Sending MQTT message: " + message + ", to" + self.host)
        try:
            publish.single(self.full_topic, message, hostname=self.host)
        except:
            print 'Failed publishing to ' + self.host