import sys

from MessageFormatter import MessageFormatter
from KismetInstance import KismetInstance

### My Class


if __name__ == "__main__":
    kismet_instance = KismetInstance()
    formatter = MessageFormatter()
    print formatter.format_kismet_response(kismet_instance.run_scan())
