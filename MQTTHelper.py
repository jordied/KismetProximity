__author__ = 'Jordi'

import paho.mqtt.publish as publish
import json

class MQTTHelper:
    def __init__(self, host='winter.ceit.uq.edu.au', base_topic='proximity', location='rpi1'):
        self.host = host
        self.full_topic = base_topic + '/' + location

    def send(self, message, is_json=False):
        if not is_json:
            message = json.dumps(message, ensure_ascii=False)
        print message
        print self.full_topic
        publish.single(self.full_topic, message, hostname=self.host)