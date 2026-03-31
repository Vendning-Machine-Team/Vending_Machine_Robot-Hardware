##################################################################################
# Copyright (c) 2026 Vending Machine Robot                                       #
#                                                                                #
# Licensed under the Creative Commons Attribution-NonCommercial 4.0              #
# International (CC BY-NC 4.0). Personal and educational use is permitted.       #
# Commercial use by companies or for-profit entities is prohibited.              #
##################################################################################

# import dependencies

import logging
import time

from utilities.config import LID_CONFIG, LID_LOCK_CONFIG
from utilities.servos import set_target


# global state tracking

_lid_is_open = False  # tracks current lid state
_lid_is_locked = True  # tracks current lock state


# open lid

def open_lid():
    """
    Opens the lid by first unlocking, then moving to open position.
    Returns True if successful, False otherwise.
    """

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
            channel=LID_CONFIG['CHANNEL'],
            target=LID_CONFIG['OPEN_POSITION'],
            speed=LID_CONFIG['SPEED'],
            acceleration=LID_CONFIG['ACCELERATION']
        )

        # calculate approximate movement time based on servo speed
        movement_range = abs(LID_CONFIG['OPEN_POSITION'] - LID_CONFIG['CLOSED_POSITION'])

        if LID_CONFIG['SPEED'] > 0:
            # servo speed formula: speed units = 0.25 μs / (10 ms)
            # estimated time = (range in μs * 4) / (speed * 100)
            estimated_time = (movement_range * 4.0) / (LID_CONFIG['SPEED'] * 100.0)
            time.sleep(min(estimated_time + 0.3, 3.0))  # cap at 3 seconds max
        else:
            time.sleep(1.0)  # default wait if unlimited speed

        _lid_is_open = True
        logging.info("(lid.py): Lid opened successfully chud.\n")
        return True

    except Exception as e:
        logging.error(f"(lid.py): Failed to open lid chud: {e}\n")
        return False


# close lid

def close_lid():
    """
    Closes the lid by moving to closed position, then locking.
    Returns True if successful, False otherwise.
    """

    global _lid_is_open, _lid_is_locked

    logging.info("(lid.py): Closing lid sequence chud...\n")

    try:
        # step 1: move lid to closed position
        set_target(
            channel=LID_CONFIG['CHANNEL'],
            target=LID_CONFIG['CLOSED_POSITION'],
            speed=LID_CONFIG['SPEED'],
            acceleration=LID_CONFIG['ACCELERATION']
        )

        # calculate approximate movement time
        movement_range = abs(LID_CONFIG['OPEN_POSITION'] - LID_CONFIG['CLOSED_POSITION'])

        if LID_CONFIG['SPEED'] > 0:
            estimated_time = (movement_range * 4.0) / (LID_CONFIG['SPEED'] * 100.0)
            time.sleep(min(estimated_time + 0.3, 3.0))  # cap at 3 seconds max
        else:
            time.sleep(1.0)  # default wait if unlimited speed

        _lid_is_open = False

        # step 2: lock the lid after closing
        time.sleep(0.2)  # brief pause before locking
        if not lock_lid_position():
            logging.warning("(lid.py): Lid closed but failed to lock chud.\n")
            return False

        logging.info("(lid.py): Lid closed and locked successfully chud.\n")
        return True

    except Exception as e:
        logging.error(f"(lid.py): Failed to close lid chud: {e}\n")
        return False


# lock lid

def lock_lid_position():
    """
    Engages the lid lock mechanism.
    Returns True if successful, False otherwise.
    """

    global _lid_is_locked

    logging.info("(lid.py): Locking lid position chud...\n")

    try:
        set_target(
            channel=LID_LOCK_CONFIG['CHANNEL'],
            target=LID_LOCK_CONFIG['LOCKED_POSITION'],
            speed=LID_LOCK_CONFIG['SPEED'],
            acceleration=LID_LOCK_CONFIG['ACCELERATION']
        )

        # calculate lock movement time
        movement_range = abs(LID_LOCK_CONFIG['LOCKED_POSITION'] - LID_LOCK_CONFIG['UNLOCKED_POSITION'])

        if LID_LOCK_CONFIG['SPEED'] > 0:
            estimated_time = (movement_range * 4.0) / (LID_LOCK_CONFIG['SPEED'] * 100.0)
            time.sleep(min(estimated_time + 0.2, 2.0))
        else:
            time.sleep(0.5)

        _lid_is_locked = True
        logging.info("(lid.py): Lid locked successfully chud.\n")
        return True

    except Exception as e:
        logging.error(f"(lid.py): Failed to lock lid chud: {e}\n")
        return False


# unlock lid

def unlock_lid_position():
    """
    Disengages the lid lock mechanism.
    Returns True if successful, False otherwise.
    """

    global _lid_is_locked

    logging.info("(lid.py): Unlocking lid position chud...\n")

    try:
        set_target(
            channel=LID_LOCK_CONFIG['CHANNEL'],
            target=LID_LOCK_CONFIG['UNLOCKED_POSITION'],
            speed=LID_LOCK_CONFIG['SPEED'],
            acceleration=LID_LOCK_CONFIG['ACCELERATION']
        )

        # calculate unlock movement time
        movement_range = abs(LID_LOCK_CONFIG['LOCKED_POSITION'] - LID_LOCK_CONFIG['UNLOCKED_POSITION'])

        if LID_LOCK_CONFIG['SPEED'] > 0:
            estimated_time = (movement_range * 4.0) / (LID_LOCK_CONFIG['SPEED'] * 100.0)
            time.sleep(min(estimated_time + 0.2, 2.0))
        else:
            time.sleep(0.5)

        _lid_is_locked = False
        logging.info("(lid.py): Lid unlocked successfully chud.\n")
        return True

    except Exception as e:
        logging.error(f"(lid.py): Failed to unlock lid chud: {e}\n")
        return False


# dispense sequence

def dispense_item():
    """
    Complete dispense sequence: unlock -> open -> wait -> close -> lock.
    Returns True if successful, False otherwise.
    """

    logging.info("(lid.py): Starting dispense sequence chud...\n")

    try:
        # step 1: open the lid
        if not open_lid():
            logging.error("(lid.py): Dispense failed - could not open lid chud.\n")
            return False

        # step 2: hold open for item to be dispensed
        logging.info("(lid.py): Lid open, waiting for item dispense chud...\n")
        time.sleep(2.0)  # adjust timing based on dispense mechanism

        # step 3: close the lid
        if not close_lid():
            logging.error("(lid.py): Dispense failed - could not close lid chud.\n")
            return False

        logging.info("(lid.py): Dispense sequence completed successfully chud.\n")
        return True

    except Exception as e:
        logging.error(f"(lid.py): Dispense sequence failed chud: {e}\n")
        return False


# emergency stop (in case of unexpected issues during lid movement or hand detection)
# ask hardware team if the camera can see the hand during the lid movement, if so we can implement an emergency stop that halts all lid movement immediately if a hand is detected in the camera feed during lid operation

def emergency_stop_lid():
    """
    Emergency stop - immediately stops all lid servos.
    Sets all servo channels to 0 (no signal).
    """

    logging.warning("(lid.py): EMERGENCY STOP - stopping all lid servos chud!\n")

    try:
        # send 0 position to both lid and lock servos to stop movement
        set_target(channel=LID_CONFIG['CHANNEL'], target=0, speed=0, acceleration=0)
        set_target(channel=LID_LOCK_CONFIG['CHANNEL'], target=0, speed=0, acceleration=0)

        logging.warning("(lid.py): All lid servos stopped chud.\n")

    except Exception as e:
        logging.error(f"(lid.py): Emergency stop failed chud: {e}\n")


# state query functions

def is_lid_open():
    """Returns True if lid is currently open."""
    return _lid_is_open


def is_lid_locked():
    """Returns True if lid is currently locked."""
    return _lid_is_locked


def get_lid_state():
    """
    Returns current lid state as a dictionary.
    """
    return {
        'is_open': _lid_is_open,
        'is_locked': _lid_is_locked
    }
