##################################################################################
# Copyright (c) 2026 Vending Machine Robot                                       #
#                                                                                #
# Licensed under the Creative Commons Attribution-NonCommercial 4.0              #
# International (CC BY-NC 4.0). Personal and educational use is permitted.       #
# Commercial use by companies or for-profit entities is prohibited.              #
##################################################################################





############################################################
############### IMPORT / CREATE DEPENDENCIES ###############
############################################################


########## IMPORT DEPENDENCIES ##########

##### import necessary libraries #####

import logging # import logging library for debugging
import os # import os for process cleanup helpers
import signal # import signal for process termination
import subprocess # import subprocess for lsof cleanup
import time # import time library for time functions

import serial # import serial for GPS NMEA read

##### import config #####

from utilities.config import GPS_CONFIG # import GPS configuration data





##############################################
############### INITIALIZE GPS ###############
##############################################


########## INITIALIZE GPS ##########

def initialize_gps( # function to initialize GPS serial connection
        serial_path=GPS_CONFIG['SERIAL_PATH'],
        serial_baud_rate=GPS_CONFIG['SERIAL_BAUD_RATE'],
        serial_timeout=GPS_CONFIG['SERIAL_TIMEOUT']
):

    ##### cleanup attempt #####

    _attempt_serial_cleanup(serial_path) # attempt to clean up serial port before establishing connection

    ##### establish serial connection to GPS #####

    logging.debug("(gps.py): Attempting to establish connection with GPS...\n")
    gps = _establish_serial_connection(serial_path, serial_baud_rate, serial_timeout) # establish serial connection

    return gps


########## ESTABLISH SERIAL CONNECTION ##########

# function to establish serial connection to GPS receiver
def _establish_serial_connection(serial_port_name, serial_baud_rate, serial_timeout):

    ##### attempt to establish serial connection and return GPS object #####

    logging.debug("(gps.py): Establishing serial connection with GPS...\n")

    try: # try to establish serial connection

        gps = serial.Serial( # set GPS connection object

            serial_port_name, # port to connect to
            baudrate=serial_baud_rate, # baud rate for serial connection
            timeout=serial_timeout # amount of time to wait for response
        )

        logging.info("(gps.py): Successfully established connection with GPS.\n")

        return gps # return GPS connection object

    except:

        logging.error("(gps.py): Failed to establish serial connection to GPS.\n")
        return 1


########## ATTEMPT SERIAL CLEANUP ##########

def _attempt_serial_cleanup(serial_path): # function to attempt cleanup of serial port before establishing connection

    ##### attempt to kill any processes using the serial port #####

    logging.debug(f"(gps.py): Attempting to clean up serial port {serial_path}...\n")

    try: # try to find and kill processes using the serial port

        # run lsof command to find processes using the serial port
        result = subprocess.run(['lsof', '-t', serial_path], stdout=subprocess.PIPE, text=True)
        pids = result.stdout.strip().split('\n') # get list of process IDs using the serial port

        for pid in pids: # iterate through each process ID
            if pid.isdigit(): # if process ID is a digit...
                os.kill(int(pid), signal.SIGTERM) # kill the process
                logging.warning(f"(gps.py): Killed process {pid} holding {serial_path}")

        time.sleep(0.2) # give the operating system some time to release the port

    except Exception as e:
        logging.warning(f"(gps.py): Serial cleanup failed: {e}")


########## READ NMEA LINE ##########

def read_nmea_line(gps): # function to read one NMEA sentence line from GPS serial stream

    ##### attempt to read a line of ASCII NMEA data #####

    try:

        raw = gps.readline() # read until newline or timeout
        if not raw:
            return None # return None on timeout or empty read
        line = raw.decode('ascii', errors='replace').strip() # decode bytes to string
        return line # return stripped NMEA line

    except Exception as e:

        logging.warning(f"(gps.py): Failed to read NMEA line: {e}\n")
        return None


########## PARSE NMEA COORDINATE ##########

def _nmea_coord_to_decimal_degrees(nmea_field, hemisphere): # function to convert ddmm.mmmm or dddmm.mmmm to decimal degrees

    if not nmea_field or not hemisphere:
        return None # return None if missing data

    try:

        value = float(nmea_field) # parse numeric portion
        degrees_whole = int(value // 100) # extract whole degrees
        minutes_frac = value - degrees_whole * 100 # extract minutes and fractional minutes
        decimal = degrees_whole + minutes_frac / 60.0 # convert to decimal degrees

        if hemisphere in ('S', 'W'):
            decimal = -decimal # apply sign for southern and western hemispheres

        return decimal # return signed decimal degrees

    except (ValueError, TypeError):

        return None # return None on parse failure


########## PARSE GPRMC ##########

def parse_gprmc(line): # function to parse a GPRMC or GNRMC sentence into fields

    ##### attempt to parse recommended minimum sentence for position and speed #####

    if not line or line[0] != '$':
        return None # return None if not a sentence start

    parts = line.split(',') # split comma-separated fields
    if len(parts) < 10:
        return None # return None if too few fields

    tag = parts[0].upper() # normalize talker and sentence id
    if not (tag.endswith('RMC') and len(tag) >= 6):
        return None # return None if not RMC variant

    status = parts[2] # A = valid, V = invalid
    if status != 'A':
        return {'valid': False} # return dict indicating no valid fix

    lat = _nmea_coord_to_decimal_degrees(parts[3], parts[4]) # latitude decimal degrees
    lon = _nmea_coord_to_decimal_degrees(parts[5], parts[6]) # longitude decimal degrees

    speed_knots = None # default speed unknown
    course = None # default course unknown

    try:
        if parts[7]:
            speed_knots = float(parts[7]) # speed over ground in knots
    except ValueError:
        pass

    try:
        if parts[8]:
            course = float(parts[8]) # course over ground in degrees
    except ValueError:
        pass

    return { # return parsed RMC data
        'valid': True,
        'latitude': lat,
        'longitude': lon,
        'speed_knots': speed_knots,
        'course_deg': course,
        'utc_time': parts[1], # hhmmss.sss UTC
        'date': parts[9], # ddmmyy UTC date
    }
