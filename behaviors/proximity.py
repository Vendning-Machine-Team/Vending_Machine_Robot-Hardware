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

import time # import time for servo movement
import logging # import logging for debugging
import math # import math for coordinate distance calculations

##### import config #####

import utilities.config as config

##### import necessary movement functions #####

from behaviors.mecanum import *
from utilities.motors import stop_all
from utilities.gps import initialize_gps, read_nmea_line, parse_gprmc, get_current_coordinates





###############################################################
############### MOVE ROBOT BASED ON COORDINATES ###############
###############################################################


########## COORDINATE CHECK ##########

def check_distance_from_home(): # function to check distance from home coordinates

    ##### ensure GPS connection exists #####

    global _GPS

    try: # try to get GPS connection
        _GPS

    except NameError: # if GPS connection is not found, set _GPS to None
        _GPS = None

    if _GPS in (None, 1): # if GPS connection is not found, return None and False
        logging.warning("(proximity.py): GPS unavailable; cannot compute distance from home.\n")
        return False

    ##### get latest fix (lat/lon + course if available) #####

    lat, lon = None, None
    course_deg = None

    # prefer a full RMC fix so we can also update LAST_FACING.
    deadline = time.time() + config.GPS_CONFIG['CHECK_INTERVAL_SECONDS']

    while time.time() < deadline:
        line = read_nmea_line(_GPS)
        if not line:
            continue
        fix = parse_gprmc(line)
        if not fix or not fix.get('valid'):
            continue
        lat = fix.get('latitude')
        lon = fix.get('longitude')
        course_deg = fix.get('course_deg')
        break

    # best-effort fallback: at least lat/lon.
    if lat is None or lon is None:
        lat, lon = get_current_coordinates(_GPS, max_seconds=2)

    if lat is None or lon is None:
        logging.warning("(proximity.py): No usable GPS fix; cannot compute distance from home.\n")
        return False

    ##### compute haversine distance (meters) to home #####

    home_lat = float(config.LOCATION_CONFIG.get('HOME_LAT', 0.0))
    home_lon = float(config.LOCATION_CONFIG.get('HOME_LON', 0.0))
    acceptable_range_m = float(config.LOCATION_CONFIG.get('ACCEPTABLE_RANGE', 0.0))

    # radius of earth in meters
    R = 6371000.0
    phi1 = math.radians(home_lat)
    phi2 = math.radians(float(lat))
    dphi = math.radians(float(lat) - home_lat)
    dlambda = math.radians(float(lon) - home_lon)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (math.sin(dlambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance_m = R * c

    ##### update config with latest values #####

    config.LOCATION_CONFIG['LAST_DISTANCE_FROM_HOME'] = float(distance_m)
    config.LOCATION_CONFIG['LAST_LAT'] = float(lat)
    config.LOCATION_CONFIG['LAST_LON'] = float(lon)
    if course_deg is not None:
        try:
            config.LOCATION_CONFIG['LAST_FACING'] = float(course_deg)
        except (TypeError, ValueError):
            pass

    ##### return out-of-range status #####

    in_range = bool(distance_m <= acceptable_range_m) if acceptable_range_m > 0 else True
    out_of_range = (not in_range)
    logging.info(
        f"(proximity.py): GPS update — "
        f"lat={config.LOCATION_CONFIG['LAST_LAT']:.7f}, "
        f"lon={config.LOCATION_CONFIG['LAST_LON']:.7f}, "
        f"distance_from_home_m={config.LOCATION_CONFIG['LAST_DISTANCE_FROM_HOME']:.2f}, "
        f"facing_deg={config.LOCATION_CONFIG['LAST_FACING']}, "
        f"in_range={in_range}\n"
    )
    return bool(out_of_range)


########## MOVE ROBOT BACK TO COORDINATES ##########

def return_to_home(): # function to take current cardinal direction and then roll back home within range

    ##### compute bearing to home and drive until within range #####

    # This is intentionally simple + time-based: GPS has latency, so we move in small bursts and re-check.
    acceptable_range_m = float(config.LOCATION_CONFIG.get('ACCEPTABLE_RANGE', 0.0))
    if acceptable_range_m <= 0:
        logging.warning("(proximity.py): ACCEPTABLE_RANGE <= 0; skipping return_to_home.\n")
        return

    # aim to get well within range so we don't oscillate on the boundary
    target_range_m = max(0.0, acceptable_range_m * 0.8)

    # safety timeout so we don't spin forever if GPS is bad
    start_time = time.monotonic()
    max_seconds = 90

    while True:

        # timeout guard
        if (time.monotonic() - start_time) >= max_seconds:
            logging.warning("(proximity.py): return_to_home timed out; stopping motors.\n")
            stop_all()
            return

        # read current state from config (must be kept fresh by check_distance_from_home calls)
        lat = float(config.LOCATION_CONFIG.get('LAST_LAT', 0.0))
        lon = float(config.LOCATION_CONFIG.get('LAST_LON', 0.0))
        home_lat = float(config.LOCATION_CONFIG.get('HOME_LAT', 0.0))
        home_lon = float(config.LOCATION_CONFIG.get('HOME_LON', 0.0))
        distance_m = float(config.LOCATION_CONFIG.get('LAST_DISTANCE_FROM_HOME', 0.0))

        if distance_m <= target_range_m:
            logging.info(
                f"(proximity.py): Back within range (distance_from_home_m={distance_m:.2f} <= {target_range_m:.2f}).\n"
            )
            stop_all()
            return

        # bearing to home (0=North, 90=East)
        lat1 = math.radians(lat)
        lat2 = math.radians(home_lat)
        dlon = math.radians(home_lon - lon)
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        bearing_deg = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0

        # current facing from GPS course (may be 0.0 default if unknown)
        facing_deg = float(config.LOCATION_CONFIG.get('LAST_FACING', 0.0))
        delta = ((bearing_deg - facing_deg + 540.0) % 360.0) - 180.0  # shortest signed angle [-180, 180]

        logging.info(
            f"(proximity.py): Returning home — distance_m={distance_m:.2f}, "
            f"bearing_to_home_deg={bearing_deg:.1f}, facing_deg={facing_deg:.1f}, delta_deg={delta:.1f}\n"
        )

        # rotate roughly toward home (time-based, conservative)
        if abs(delta) > 15.0:
            if delta < 0:
                rotate_left(6)
            else:
                rotate_right(6)
            time.sleep(0.5)
            stop_all()

        # drive forward a short burst, then re-check
        forward(6)
        time.sleep(1.0)
        stop_all()

        # wait for GPS to update before the next loop (uses configured check interval)
        time.sleep(max(0.2, float(config.GPS_CONFIG.get('CHECK_INTERVAL_SECONDS', 1)) / 2.0))
    