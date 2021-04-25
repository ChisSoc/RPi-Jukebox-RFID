"""
The RDM6300 / RDM630 connected via serial UART port

The Rdm6300Reader supports 3 number formats for the card ID. See NUMBER_FORMAT below for details.

"""
import os
import logging
import configparser
import serial

import base.inputminus as pyil
from base.simplecolors import colors
from base.readerbase import *

from .description import DESCRIPTION


# Create logger
logger = logging.getLogger(os.path.basename(__file__).ljust(25))
logger.setLevel(logging.DEBUG)
# Create console handler and set default level (may be overwritten by readersupport module)
logconsole = logging.StreamHandler()
logconsole.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)-8s: %(message)s', datefmt='%d.%m.%Y %H:%M:%S'))
logconsole.setLevel(logging.INFO)
logger.addHandler(logconsole)

NUMBER_FORMAT = ['card_id_dec',
                 'card_id_raw',
                 'card_id_float']
NUMBER_FORMAT_HELP = ['A 10 digit card ID e.g. 0006762840 (default)',
                      'The raw (original) card ID e.g. 070067315809',
                      'The card ID as fraction e.g. 103,12632']
NUMBER_FORMAT_HINT = ['This number is often printed on the back of the card and identical to the read-out from an USB reader',
                      'Previously the only option of the RDM6300 reader. Choose this if you want to use an existing database',
                      '']


def query_customization() -> dict:
    prompt_color = colors.lightgreen
    print("Select number format:")
    for idx, val in enumerate(NUMBER_FORMAT):
        print(f" {colors.lightgreen}{idx:2d}{colors.reset}: {colors.lightcyan}{colors.bold}{val:15}{colors.reset}: {NUMBER_FORMAT_HELP[idx]}")
        print(f"                      {colors.lightgrey}{NUMBER_FORMAT_HINT[idx]}{colors.reset}")
    dev_id = pyil.input_int("Number format?", blank=0, min=0, max=len(NUMBER_FORMAT)-1, prompt_color=prompt_color, prompt_hint=True)
    return {'number_format': NUMBER_FORMAT[dev_id],
            'device': '/dev/ttyS0',
            'baudrate': 9600,
            'serial_timeout': 0.1,
            'log_all_cards': 'false'}


def convert_to_weigand26_when_checksum_ok(raw_card_id):
    weigand26 = []
    xor = 0
    val = 0
    chk = None
    for i in range(0, len(raw_card_id) >> 1):
        val = int(raw_card_id[i * 2:i * 2 + 2], 16)
        if i < 5:
            xor = xor ^ val
            weigand26.append(val)
        else:
            chk = val
    if chk == val:
        return weigand26
    else:
        return None


class ReaderClass(ReaderBaseClass):
    def __init__(self, params: dict):
        super().__init__(description=DESCRIPTION, params=params, logger=logger)

        config = configparser.ConfigParser()
        if params is None:
            config.read_dict({'params': {}})
        else:
            config.read_dict({'params': params})
        self.number_format = config['params'].get('number_format', fallback='card_id_dec')
        self.device = config['params'].get('device', fallback='/dev/ttyS0')
        self.baudrate = config['params'].getint('baudrate', fallback=9600)
        self.serial_timeout = config['params'].getfloat('serial_timeout', fallback=0.1)
        self.log_all_cards = config['params'].getboolean('log_all_cards', fallback=False)

        if 'number_format' not in config['params']:
            logger.warning(f"Parameter 'number_format' not found in dictionary. Defaulting to '{self.number_format}'")
        if self.number_format not in NUMBER_FORMAT:
            logger.error(f"Unknown value in option: 'number_format={self.number_format}'. Defaulting to {NUMBER_FORMAT[0]}!")
            self.number_format = NUMBER_FORMAT[0]

        try:
            self.rfid_serial = serial.Serial(self.device, self.baudrate, timeout=self.serial_timeout)
        except serial.SerialException as e:
            logger.error(e)
            raise e

    def cleanup(self):
        self.rfid_serial.close()

    def read_card(self) -> str:
        byte_card_id = bytearray()

        try:
            while True:
                try:
                    wait_for_start_byte = True
                    while True:
                        read_byte = self.rfid_serial.read()

                        if wait_for_start_byte:
                            if read_byte == b'\x02':
                                wait_for_start_byte = False
                        else:
                            if read_byte != b'\x03':     # could get stuck here, check len? check timeout by len == 0?
                                byte_card_id.extend(read_byte)
                            else:
                                break

                    raw_card_id = byte_card_id.decode('ascii')
                    byte_card_id.clear()
                    self.rfid_serial.reset_input_buffer()

                    if len(raw_card_id) == 12:
                        w26 = convert_to_weigand26_when_checksum_ok(raw_card_id)
                        if w26 is not None:

                            if self.number_format == 'card_id_dec':
                                # this will return a 10 Digit card ID e.g. 0006762840
                                card_id = '{0:010d}'.format((w26[1] << 24) + (w26[2] << 16) + (w26[3] << 8) + w26[4])
                            elif self.number_format == 'card_id_float':
                                # this will return card ID as fraction e.g. 103,12632
                                card_id = '{0:d},{1:05d}'.format(((w26[1] << 8) + w26[2]), ((w26[3] << 8) + w26[4]))
                            else:
                                # this will return the raw (original) card ID e.g. 070067315809
                                card_id = raw_card_id

                            if self.log_all_cards:
                                logger.debug(f"Card detected with ID = '{card_id}'")
                            return card_id

                except ValueError as ve:
                    logger.error(ve)

        except serial.SerialException as se:
            logger.error(se)
