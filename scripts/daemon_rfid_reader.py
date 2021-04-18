#!/usr/bin/env python3
"""
This script kicks off the daemon rfid reader

This file is copy of the actual daemon rfid reader file in the rfid_reader module with 
- addition to sys.path to find the entire rfid_reader package
- adjusted path to default configuration

This file exists for legacy reasons, not to break existing Phoniebox installations when doing an 'update' by git pull

The original files locations is: components/rfid_reader/daemon_rfid_reader.py
"""
import sys
import os
import argparse
import logging

# Get absolute path of this script
script_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
# Add the path for the reader modules to Python's search path
# such the reader directory is searched after local dir, but before all others
reader_path = script_path + '/../components/rfid_reader'
sys.path.insert(1, reader_path)

# Now import the reader
from base import readerdaemon


if __name__ == '__main__':
    # Parse the arguments and get the script started :-)

    # The default config file relative to this files location and independent of working directory
    default_reader_cfg_file = os.path.abspath(script_path + '/../settings') + '/rfid_reader.ini'

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity",
                        help="Increase verbosity to 'DEBUG'",
                        action="store_const", const=logging.DEBUG, default=None)
    parser.add_argument("-c", "--conffile",
                        help=f"Reader configuration file [default: '{default_reader_cfg_file}']",
                        metavar="FILE", default=default_reader_cfg_file)
    args = parser.parse_args()

    readerdaemon.create_read_card_workers(args.conffile, args.verbosity)
