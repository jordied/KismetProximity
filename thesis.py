import sys

from MessageFormatter import MessageFormatter
from KismetInstance import KismetInstance
from MQTTHelper import MQTTHelper
import time

### My Class


if __name__ == "__main__":
    kismet_instance = KismetInstance()
    formatter = MessageFormatter()
    MQTTHelper = MQTTHelper()
    client_list = formatter.format_kismet_response(kismet_instance.run_scan())
    list_dict = formatter.get_client_list(client_list)
    MQTTHelper.send(list_dict)

