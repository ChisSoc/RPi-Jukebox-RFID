import evdev
import select
import os
import logging


# Create logger
logger = logging.getLogger(os.path.basename(__file__).ljust(20))
logger.setLevel(logging.DEBUG)
# Create console handler and set default level
logconsole = logging.StreamHandler()
logconsole.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)-8s: %(message)s', datefmt='%d.%m.%Y %H:%M:%S'))
logconsole.setLevel(logging.INFO)
logger.addHandler(logconsole)


DESCRIPTION = 'Generic USB Reader'


def get_devices():
    return [evdev.InputDevice(fn) for fn in evdev.list_devices()]


def query_customization():
    print("\nChoose USB device from list:")
    devices = get_devices()
    logger.debug(f"USB devices: {[x.name for x in devices]}")
    if len(devices) == 0:
        logger.error("USB device list is empty. Make sure USB RFID reader is connected. Then re-run register_reader.py")
        return {'device_name': '__error_empty_device_list__'}
    for idx, val in enumerate(devices):
        print(f" {idx:2d}: {val.name}")
    dev_id = int(input('\nDevice Number: '))
    return {'device_name': devices[dev_id].name}


class Reader:
    def __init__(self, params: dict):
        logger.debug("Initializing reader {DESCRIPTION} from {__file_}}")
        self.keys = "X^1234567890XXXXqwertzuiopXXXXasdfghjklXXXXXyxcvbnmXXXXXXXXXXXXXXXXXXXXXXX"
        if not params:
            logger.error("Params dictionary may not be empty! Mandatory key 'device_name' not given!")
            raise KeyError("Params dictionary may not be empty! Mandatory key 'device_name' not given!")
        if 'device_name' not in params:
            logger.error(f"Mandatory key 'device_name' not given in dictionary params!")
        device_name = params['device_name']

        devices = get_devices()
        for device in devices:
            if device.name == device_name:
                logger.debug(f"Inspecting device {device.name} at {device}")
                self.dev = device
                break
        else:
            logger.error(f"Could not find the device '{device_name}'. Make sure is connected.")
            raise FileNotFoundError(f"Could not find the device '{device_name}'. Make sure is connected.")

    def read_card(self) -> str:
        stri = ''
        key = ''
        while key != 'KEY_ENTER':
            r, w, x = select.select([self.dev], [], [])
            for event in self.dev.read():
                if event.type == 1 and event.value == 1:
                    stri += self.keys[event.code]
                    # print( keys[ event.code ] )
                    key = evdev.ecodes.KEY[event.code]
        return stri[:-1]