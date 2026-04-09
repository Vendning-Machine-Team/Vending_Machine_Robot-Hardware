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

import logging
import pigpio

##### import config #####

from utilities.config import MOTOR_CONFIG


########## CREATE DEPENDENCIES ##########

##### pigpio instance (set by initialize_motors) #####

PI = None


##### motor name index (built from MOTOR_CONFIG['*']['MOTORS']) #####

MOTOR_NAME_INDEX = {}





#######################################################
############### MOTOR CONTROL FUNCTIONS ###############
#######################################################


########## INITIALIZE MOTOR CONTROLLER ##########

# initialize pigpio and all DCMC pins from MOTOR_CONFIG
# sets each IN pin as OUTPUT, PWM frequency, and duty 0 (stop)
# ensure pigpio daemon is running: sudo pigpiod
def initialize_motor_controllers():

    global PI, MOTOR_NAME_INDEX

    logging.debug("(motors.py): Initializing motor controllers...\n")

    try:

        PI = pigpio.pi()

        if not PI.connected:

            logging.error("(motors.py): Failed to connect to pigpio daemon. Is pigpiod running?\n")
            return None

        logging.debug("(motors.py): Building motor name index...\n")

        MOTOR_NAME_INDEX = _build_motor_name_index()

        logging.info("(motors.py): Built motor name index.\n")

        for controller_key, cfg in MOTOR_CONFIG.items():

            freq = cfg.get('PWM_FREQ_HZ', 1000)

            for pin_key in ('A_IN1', 'A_IN2', 'B_IN1', 'B_IN2'):
                gpio = cfg[pin_key]
                PI.set_mode(gpio, pigpio.OUTPUT)
                PI.set_PWM_frequency(gpio, freq)
                PI.set_PWM_dutycycle(gpio, 0)

            logging.debug(f"(motors.py): Initialized {controller_key} on GPIOs {cfg['A_IN1']}, {cfg['A_IN2']}, {cfg['B_IN1']}, {cfg['B_IN2']}\n")

        logging.info("(motors.py): Motor controllers initialized.\n")

        return PI

    except Exception as e:

        logging.error(f"(motors.py): Motor initialization failed: {e}\n")

        if PI is not None:
            try:
                PI.stop()
            except Exception:
                pass
            PI = None

        return None


########## BUILD MOTOR NAME INDEX ##########

def _build_motor_name_index(): # build a lookup from logical motor name (FL, FR, BL, BR) to (controller_key, channel, orientation)

    index = {}

    for controller_key, cfg in MOTOR_CONFIG.items():

        motors = cfg.get('MOTORS', {})

        for name, m_cfg in motors.items():

            key = str(name).upper()

            if key in index:
                
                logging.warning(
                    f"(motors.py): Duplicate motor name '{key}' in MOTOR_CONFIG; "
                    f"overwriting previous mapping.\n"
                )

            index[key] = {
                'controller_key': controller_key,
                'channel': str(m_cfg.get('CHANNEL', 'A')).upper(),
                'orientation': 1 if m_cfg.get('ORIENTATION', 1) >= 0 else -1,
            }

    return index


########## INTENSITY TO SPEED ##########

def intensity_to_speed(intensity): # map joystick intensity 1-10 (e.g. from interpret_commands) to motor speed 0.0-1.0

    if intensity is None or intensity <= 0:
        return 0.0

    return max(0.0, min(1.0, float(intensity) / 10.0))


########## SET MOTOR ##########

# set one motor on a DCMC controller
# controller_key: 'LEFT_DCMC' or 'RIGHT_DCMC'
# channel: 'A' or 'B'
# direction: 'forward' | 'reverse' | 'stop'
# speed: 0.0 to 1.0 (ignored for 'stop')
def set_motor(controller_key, channel, direction, speed=0.0):

    if PI is None or not PI.connected:
        logging.warning("(motors.py): set_motor called but motors not initialized.\n")
        return

    cfg = MOTOR_CONFIG.get(controller_key)
    if cfg is None:
        logging.error(f"(motors.py): Unknown controller_key: {controller_key}\n")
        return

    channel = channel.upper()
    if channel == 'A':
        in1, in2 = cfg['A_IN1'], cfg['A_IN2']
    elif channel == 'B':
        in1, in2 = cfg['B_IN1'], cfg['B_IN2']
    else:
        logging.error(f"(motors.py): channel must be 'A' or 'B', got {channel}\n")
        return

    speed = max(0.0, min(1.0, float(speed)))
    duty = int(round(speed * 255))

    try:
        if direction == 'stop':
            PI.set_PWM_dutycycle(in1, 0)
            PI.set_PWM_dutycycle(in2, 0)
        elif direction == 'forward':
            PI.set_PWM_dutycycle(in1, duty)
            PI.set_PWM_dutycycle(in2, 0)
        elif direction == 'reverse':
            PI.set_PWM_dutycycle(in1, 0)
            PI.set_PWM_dutycycle(in2, duty)
        else:
            logging.error(f"(motors.py): direction must be 'forward', 'reverse', or 'stop', got {direction}\n")
            return
        logging.debug(f"(motors.py): {controller_key} channel {channel} -> {direction} duty {duty}\n")
    except Exception as e:
        logging.error(f"(motors.py): set_motor failed: {e}\n")


########## MOVE MOTOR BY NAME ##########

# high-level helper to move a specific wheel motor by name
# motor_name: 'FL', 'FR', 'BL', 'BR'
# direction: 'clockwise' | 'counterclockwise' | 'cw' | 'ccw' | 'stop'
# intensity: integer 1-10 (mapped to 10%–100% duty); 0 or None = stop
def move_motor(motor_name, direction, intensity):

    if PI is None or not PI.connected:
        logging.warning("(motors.py): move_motor called but motors not initialized.\n")
        return

    if motor_name is None:
        logging.error("(motors.py): move_motor requires a motor_name.\n")
        return

    name_key = str(motor_name).upper()
    motor_cfg = MOTOR_NAME_INDEX.get(name_key)
    if motor_cfg is None:
        logging.error(f"(motors.py): Unknown motor_name '{motor_name}'. Expected one of {list(MOTOR_NAME_INDEX.keys())}\n")
        return

    ##### normalize direction #####

    if not direction:
        logging.error("(motors.py): move_motor requires a direction.\n")
        return

    d = str(direction).lower()

    if d in ('cw', 'clockwise'):
        logical_dir = 'clockwise'
    elif d in ('ccw', 'counterclockwise', 'counter-clockwise'):
        logical_dir = 'counterclockwise'
    elif d == 'stop':
        logical_dir = 'stop'
    else:
        logging.error(f"(motors.py): Invalid direction '{direction}'. Use 'clockwise', 'counterclockwise', or 'stop'.\n")
        return

    ##### normalize intensity #####

    try:
        intensity_val = int(intensity) if intensity is not None else 0
    except (TypeError, ValueError):
        logging.error(f"(motors.py): Invalid intensity '{intensity}'. Expected 0-10.\n")
        return

    if intensity_val < 0:
        intensity_val = 0
    if intensity_val > 10:
        intensity_val = 10

    if logical_dir == 'stop' or intensity_val == 0:
        set_motor(motor_cfg['controller_key'], motor_cfg['channel'], 'stop', 0.0)
        return

    ##### map clockwise/counterclockwise to electrical forward/reverse using ORIENTATION #####

    orientation = motor_cfg.get('orientation', 1)

    if orientation >= 0:
        if logical_dir == 'clockwise':
            electrical_dir = 'forward'
        else:
            electrical_dir = 'reverse'
    else:
        if logical_dir == 'clockwise':
            electrical_dir = 'reverse'
        else:
            electrical_dir = 'forward'

    speed = intensity_to_speed(intensity_val)
    set_motor(motor_cfg['controller_key'], motor_cfg['channel'], electrical_dir, speed)


########## MOTOR GROUP TEST FUNCTIONS ##########

##### test front motors #####

def run_front_motors(intensity): # helper function to run only front motors for wiring/debug tests

    move_motor('FL', 'counterclockwise', intensity)
    move_motor('FR', 'clockwise', intensity)


##### test rear motors #####

def run_back_motors(intensity): # helper function to run only back motors for wiring/debug tests

    move_motor('BL', 'counterclockwise', intensity)
    move_motor('BR', 'clockwise', intensity)


########## STOP ALL MOTORS ##########

def stop_all(controller_key=None): # stop motors; if controller_key is None, stop all controllers; else stop only that one

    if PI is None or not PI.connected:
        logging.warning("(motors.py): stop_all called but pigpio is unavailable.\n")
        return False

    keys = [controller_key] if controller_key else MOTOR_CONFIG.keys()
    any_success = False
    any_failure = False

    for key in keys:

        cfg = MOTOR_CONFIG.get(key)

        if cfg is None:
            any_failure = True
            continue

        for pin_key in ('A_IN1', 'A_IN2', 'B_IN1', 'B_IN2'):

            try:
                PI.set_PWM_dutycycle(cfg[pin_key], 0)
                any_success = True

            except Exception as e:
                logging.warning(f"(motors.py): stop_all failed on {key} {pin_key}: {e}\n")
                any_failure = True

    logging.debug(f"(motors.py): stop_all controller_key={controller_key}\n")
    if any_failure:
        return False # return False if any stop_all failed
    if any_success:
        return True # return True if all attempted stop_all writes were successful
    return False # return False if no pins were actually written