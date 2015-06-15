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