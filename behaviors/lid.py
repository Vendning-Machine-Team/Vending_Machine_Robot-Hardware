##################################################################################
# Copyright (c) 2026 Vending Machine Robot                                       #
#                                                                                #
# Licensed under the Creative Commons Attribution-NonCommercial 4.0              #
# International (CC BY-NC 4.0). Personal and educational use is permitted.       #
# Commercial use by companies or for-profit entities is prohibited.              #
##################################################################################





##########################################################
############### IMPORT/CREATE DEPENDENCIES ###############
##########################################################


########## IMPORT DEPENDENCIES ##########

##### import necessary libraries #####

import logging
import time

##### import necessary functions #####

from utilities.config import LID_CONFIG, LID_LOCK_CONFIG
from utilities.servos import set_target

_lid_is_open = False
_lid_is_locked = True


def _resolve_hinge_target(side, state):
    """
    Resolve hinge target using direction-based mirroring when direction
    keys are configured; otherwise fallback to legacy explicit per-side values.
    """
    direction_key = f"{side}_HINGE_DIRECTION"
    if direction_key not in LID_CONFIG:
        explicit_key = f"{state}_POSITION_{side}"
        if explicit_key in LID_CONFIG:
            return LID_CONFIG[explicit_key]

    min_pos = LID_CONFIG.get('MIN_POSITION', 1000)
    max_pos = LID_CONFIG.get('MAX_POSITION', 2000)
    if state == 'OPEN':
        base_target = LID_CONFIG.get('BASE_OPEN_POSITION', LID_CONFIG.get('OPEN_POSITION_LEFT', max_pos))
    else:
        base_target = LID_CONFIG.get('BASE_CLOSED_POSITION', LID_CONFIG.get('CLOSED_POSITION_LEFT', min_pos))

    direction = LID_CONFIG.get(direction_key, 1)
    if direction >= 0:
        return base_target

    return (min_pos + max_pos) - base_target





##################################################
############### MOVE LID FUNCTIONS ###############
##################################################


########## HIGH LEVEL LID MOVEMENT FUNCTIONS ##########

##### open close cycle #####

def open_close_cycle(): # unlock lid, wait 2 seconds, open, wait 15 seconds, close, wait 2 seconds, lock lid

    unlock_lid_position()
    time.sleep(2)
    open_lid()
    time.sleep(15)
    close_lid()
    time.sleep(2)
    lock_lid_position()


########## FUNDAMENTAL LID MOVEMENT FUNCTIONS ##########

##### open lid #####

def open_lid():

    global _lid_is_open, _lid_is_locked

    logging.info("(lid.py): Opening lid sequence chud...\n")

    try:
        # step 1: unlock the lid first
        if _lid_is_locked:
            if not unlock_lid_position():
                logging.error("(lid.py): Failed to unlock lid before opening chud.\n")
                return False
            time.sleep(0.3)  # brief pause after unlocking

        # step 2: move lid to open position
        set_target(
            channel=LID_CONFIG['LEFT_HINGE_CHANNEL'],
            target=_resolve_hinge_target('LEFT', 'OPEN'),
            speed=LID_CONFIG['SPEED'],
            acceleration=LID_CONFIG['ACCELERATION']
        )

        set_target(
            channel=LID_CONFIG['RIGHT_HINGE_CHANNEL'],
            target=_resolve_hinge_target('RIGHT', 'OPEN'),
            speed=LID_CONFIG['SPEED'],
            acceleration=LID_CONFIG['ACCELERATION']
        )

        _lid_is_open = True
        logging.info("(lid.py): Lid opened successfully chud.\n")
        return True

    except Exception as e:
        logging.error(f"(lid.py): Failed to open lid chud: {e}\n")
        return False

##### close lid #####

def close_lid():

    global _lid_is_open

    logging.info("(lid.py): Closing lid sequence chud...\n")

    try:
        # step 1: move lid to closed position
        set_target(
            channel=LID_CONFIG['LEFT_HINGE_CHANNEL'],
            target=_resolve_hinge_target('LEFT', 'CLOSED'),
            speed=LID_CONFIG['SPEED'],
            acceleration=LID_CONFIG['ACCELERATION']
        )

        set_target(
            channel=LID_CONFIG['RIGHT_HINGE_CHANNEL'],
            target=_resolve_hinge_target('RIGHT', 'CLOSED'),
            speed=LID_CONFIG['SPEED'],
            acceleration=LID_CONFIG['ACCELERATION']
        )

        _lid_is_open = False
        logging.info("(lid.py): Lid closed successfully chud.\n")
        return True

    except Exception as e:
        logging.error(f"(lid.py): Failed to close lid chud: {e}\n")
        return False

##### lock lid #####

def lock_lid_position():

    global _lid_is_locked

    logging.info("(lid.py): Locking lid position chud...\n")

    try:
        set_target(
            channel=LID_LOCK_CONFIG['LOCK_CHANNEL'],
            target=LID_LOCK_CONFIG['LOCKED_POSITION'],
            speed=LID_LOCK_CONFIG['SPEED'],
            acceleration=LID_LOCK_CONFIG['ACCELERATION']
        )

        _lid_is_locked = True
        logging.info("(lid.py): Lid locked successfully chud.\n")
        return True

    except Exception as e:
        logging.error(f"(lid.py): Failed to lock lid chud: {e}\n")
        return False

##### unlock lid #####

def unlock_lid_position():

    global _lid_is_locked

    logging.info("(lid.py): Unlocking lid position chud...\n")

    try:
        set_target(
            channel=LID_LOCK_CONFIG['LOCK_CHANNEL'],
            target=LID_LOCK_CONFIG['UNLOCKED_POSITION'],
            speed=LID_LOCK_CONFIG['SPEED'],
            acceleration=LID_LOCK_CONFIG['ACCELERATION']
        )

        _lid_is_locked = False
        logging.info("(lid.py): Lid unlocked successfully chud.\n")
        return True

    except Exception as e:
        logging.error(f"(lid.py): Failed to unlock lid chud: {e}\n")
        return False
    