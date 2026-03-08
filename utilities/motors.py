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





#######################################################
############### MOTOR CONTROL FUNCTIONS ###############
#######################################################


########## INITIALIZE MOTOR CONTROLLER ##########

def initialize_motors():
    """
    Initialize pigpio and all DCMC pins from MOTOR_CONFIG.
    Sets each IN pin as OUTPUT, PWM frequency, and duty 0 (stop).
    Ensure pigpio daemon is running: sudo pigpiod
    """
    global PI

    logging.debug("(motors.py): Initializing motor controllers...\n")

    try:
        PI = pigpio.pi()
        if not PI.connected:
            logging.error("(motors.py): Failed to connect to pigpio daemon. Is pigpiod running?\n")
            return None

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


########## INTENSITY TO SPEED ##########

def intensity_to_speed(intensity):
    """
    Map joystick intensity 1-10 (e.g. from interpret_commands) to motor speed 0.0-1.0.
    """
    if intensity is None or intensity <= 0:
        return 0.0
    return max(0.0, min(1.0, intensity / 10.0))


########## SET MOTOR ##########

def set_motor(controller_key, channel, direction, speed=0.0):
    """
    Set one motor on a DCMC controller.
    controller_key: 'FRONT_DCMC' or 'BACK_DCMC'
    channel: 'A' or 'B'
    direction: 'forward' | 'reverse' | 'stop'
    speed: 0.0 to 1.0 (ignored for 'stop')
    """
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


########## STOP ALL MOTORS ##########

def stop_all(controller_key=None):
    """
    Stop motors. If controller_key is None, stop all controllers; else stop only that one.
    """
    if PI is None or not PI.connected:
        return

    keys = [controller_key] if controller_key else MOTOR_CONFIG.keys()
    for key in keys:
        cfg = MOTOR_CONFIG.get(key)
        if cfg is None:
            continue
        for pin_key in ('A_IN1', 'A_IN2', 'B_IN1', 'B_IN2'):
            try:
                PI.set_PWM_dutycycle(cfg[pin_key], 0)
            except Exception as e:
                logging.warning(f"(motors.py): stop_all failed on {key} {pin_key}: {e}\n")
    logging.debug(f"(motors.py): stop_all controller_key={controller_key}\n")
