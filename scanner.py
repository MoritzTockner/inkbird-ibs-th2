from bluepy.btle import Scanner, DefaultDelegate, BTLEManagementError

from logger import log
from time import sleep

class ScanDelegate(DefaultDelegate):
    # 1 - flags, 2 - Incomplete 16b Services, 255 - Manufacturer, 22 - 16b Service Data, 9 - Complete Local Name
    MANUFACTURER_DATA = 255  # [1d18828809e4070310112302]

    def __init__(self, mac_addresses, callback):
        DefaultDelegate.__init__(self)
        self.mac_addresses = mac_addresses
        self.last_raw_data = None
        self.callback = callback

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if dev.addr.upper() in self.mac_addresses:
            self.parse_data(dev)

    def parse_data(self, dev):
        log.debug("device %s is %s, rssi: %d dBm, connectable: %s",
                  dev.addr, dev.addrType, dev.rssi, dev.connectable)

        for (tag, desc, value) in dev.getScanData():
            if tag == self.MANUFACTURER_DATA:
                log.debug("tag with MANUFACTURER_DATA found")
                raw_data = bytes.fromhex(value)
                if raw_data == self.last_raw_data:
                    log.debug("skip duplicate data")
                    return
                else:
                    log.debug("tag: %s", tag)
                    log.debug("desc: %s", desc)
                    log.debug("value: %s", value)

                data = {}
                data["temperature"] = int.from_bytes(raw_data[0:2], byteorder="little") / 100
                data["humidity"] = int.from_bytes(raw_data[2:4], byteorder="little") / 100
                data["battery"] = raw_data[7]
                self.callback(dev.addr.upper(), data)
        log.debug('======================================')


def start(mac_addresses, timeout, sampling_time, callback):
    log.info("scanner is starting...")
    scanner = Scanner().withDelegate(ScanDelegate(mac_addresses, callback))

    while True:
        try:
            scanner.start()
            scanner.process(timeout)
            scanner.stop()
        except BTLEManagementError as e:
            handle_scan_error(scanner, timeout)

        sleep(sampling_time)

def handle_scan_error(scanner, timeout):
    btle_error_cnt = 1
    btle_error_cnt_max = 10
    btle_error = True
    error_msg = "Caught BTLE error. Retry {:d}"
    log.error(error_msg.format(btle_error_cnt))
    while btle_error is True and btle_error_cnt < btle_error_cnt_max:
        try:
            scanner.start()
            scanner.process(timeout)
            scanner.stop()
            btle_error = False
        except BTLEManagementError as e:
            btle_error_cnt += 1
            log.error(error_msg.format(btle_error_cnt))
            sleep(1)
