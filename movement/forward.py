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

from utilities.motors import initialize_motor_controllers, move_motor





#########################################################
############### FORWARD TESTING FUNCTIONS ###############
#########################################################


########## INTERNAL STATE ##########

_MOTORS_INITIALIZED = False


def _ensure_motors_initialized():
    global _MOTORS_INITIALIZED
    if _MOTORS_INITIALIZED:
        return

    pi = initialize_motor_controllers()
    if pi is not None:
        _MOTORS_INITIALIZED = True


########## PUBLIC TEST FUNCTION ##########

def person_detected_simple_forward():
    """
    Simple example movement when a person is detected:
    - Front Left (FL): counterclockwise at intensity 5
    - Front Right (FR): clockwise at intensity 5
    """
    _ensure_motors_initialized()

    # If initialization failed, do nothing
    if not _MOTORS_INITIALIZED:
        return

    move_motor('FL', 'counterclockwise', 5)
    move_motor('FR', 'clockwise', 5)


def person_no_longer_detected():
    """
    Stop the motors used by person_detected_simple_forward when no person is detected.
    """
    move_motor('FL', 'stop', 0)
    move_motor('FR', 'stop', 0)
