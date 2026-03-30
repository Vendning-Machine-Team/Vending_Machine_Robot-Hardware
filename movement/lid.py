##################################################################################
# Copyright (c) 2026 Vending Machine Robot                                       #
#                                                                                #
# Licensed under the Creative Commons Attribution-NonCommercial 4.0              #
# International (CC BY-NC 4.0). Personal and educational use is permitted.       #
# Commercial use by companies or for-profit entities is prohibited.              #
##################################################################################

########## IMPORT DEPENDENCIES ##########

# libraries with time n shi

import logging
import time

# config

from utilities.config import LID_CONFIG

# servo functions

from utilities.servos import set_target


#OPEN LID

def open_lid():
    logging.info("(lid.py): open lid\n")

    try:
        set_target(
            channel=LID_CONFIG['CHANNEL'],
            target=LID_CONFIG['OPEN_POSITION'],
            speed=LID_CONFIG['SPEED'],
            acceleration=LID_CONFIG['ACCELERATION']
        )

        # calculate approximate movement time for blocking ?
        # this is a rough estimate - adjust based on actual servo behavior
        movement_range = abs(LID_CONFIG['OPEN_POSITION'] - LID_CONFIG['CLOSED_POSITION'])

        if LID_CONFIG['SPEED'] > 0:
            # use time to move from closed to open as a baseline
            pass
        else:
            time.sleep(0.5)  # default wait if unlimited speed

        logging.info("(lid.py): Lid opened successfully.\n")
        return True

    except Exception as e:
        logging.error(f"(lid.py): did work chud: {e}\n")
        return False


# close lid function
def close_lid():
    
    logging.info("(lid.py): close lid\n")

    try:
        set_target(
            channel=LID_CONFIG['CHANNEL'],
            target=LID_CONFIG['CLOSED_POSITION'],
            speed=LID_CONFIG['SPEED'],
            acceleration=LID_CONFIG['ACCELERATION']
        )

        # calculate approximate movement time for blocking ?
        # this is a rough estimate - adjust based on actual servo behavior
        movement_range = abs(LID_CONFIG['CLOSED_POSITION'] - LID_CONFIG['OPEN_POSITION'])

        if LID_CONFIG['SPEED'] > 0:
            # use time to move from closed to open as a baseline
            pass
        else:
            time.sleep(0.5)  # default wait if unlimited speed

        logging.info("(lid.py): Lid closed successfully.\n")
        return True

    except Exception as e:
        logging.error(f"(lid.py): did work chud: {e}\n")
        return False

# lock lid position function (if needed) -> calls servo 3 to lock position, then unlocks when opening lid
def lock_lid_position():
    logging.info("(lid.py): lock lid position\n")

    try:
        # send command to lock lid position (this is a placeholder - implement as needed)
        # e.g., set_target(channel=LOCK_CHANNEL, target=LOCK_POSITION, speed=LOCK_SPEED, acceleration=LOCK_ACCELERATION)

        logging.info("(lid.py): Lid position locked successfully.\n")
        return True

    except Exception as e:
        logging.error(f"(lid.py): did work chud: {e}\n")
        return False
def unlock_lid_position():
    logging.info("(lid.py): unlock lid position\n")

    try:
        # send command to unlock lid position (this is a placeholder - implement as needed)
        # e.g., set_target(channel=LOCK_CHANNEL, target=UNLOCK_POSITION, speed=LOCK_SPEED, acceleration=LOCK_ACCELERATION)

        logging.info("(lid.py): Lid position unlocked successfully.\n")
        return True

    except Exception as e:
        logging.error(f"(lid.py): did work chud: {e}\n")
        return False