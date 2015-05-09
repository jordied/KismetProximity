import sys

from WiFiSniffer import WiFiSniffer

### My Class


if __name__ == "__main__":
    sniffer = WiFiSniffer(sys.argv)
    print sniffer.run_scan()
