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

import time # import time library for gait timing
import logging # import logging library for debugging





#####################################################
############### CREATE CONFIGURATIONS ###############
#####################################################


########## UTILITY CONFIGURATIONS ##########

##### set global fps to be used by all modules #####

LOOP_RATE_HZ = 30 # global loop rate in Hz for all modules TODO DEPRECATED/LEGACY
CONTROL_MODE = 'web' # current control mode of the robot (web or radio)
RL_NOT_CNN = False # boolean to switch between testing and RL models (true is RL, false is cnn)
DEFAULT_INTENSITY = 10 # default intensity for keyboard commands (1 to 10)

##### set logging configuration #####

LOG_CONFIG = {
    'LOG_PATH': "/home/matthewthomasbeck/Projects/Vending_Machine_Robot-Hardware/vending_machine.log", # path to log file DO NOT CHANGE
    'LOG_LEVEL': logging.INFO # set log level to logging.<DEBUG, INFO, WARNING, ERROR, or CRITICAL>
}

########## CAMERA CONFIGURATION ##########

##### set camera configuration #####

CAMERA_CONFIG = {
    'FOV': 75, # degrees
    'CAMERA_WIDTH': 4608,
    'CAMERA_HEIGHT': 2592,
    'FOV_HORIZONTAL': 66,  # degrees
    'FOV_VERTICAL': 41,  # degrees
    'PIXEL_SIZE_UM': 1.4,  # pixel size in micrometers
    'DEPTH_OF_FIELD': 0.1,  # depth of field distance in meters
    'APERTURE_RATIO': 1.8,
    'WIDTH': 1152, # width of the camera image (input for CNN)
    'HEIGHT': 648, # height of the camera image (input for CNN)
    'FRAME_RATE': 30, # frame rate of the camera in frames per second
    'CROP_FRACTION': 1.0, # fraction of the image to crop from each side (0.0 to 1.0)
    'OUTPUT_WIDTH': 1152, # width of the ML image (output for CNN)
    'OUTPUT_HEIGHT': 648, # height of the ML image (output for CNN)
}


########## INTERNET CONFIGURATIONS ##########

##### set internet connectivity configuration #####

INTERNET_CONFIG = {
    'BACKEND_API_URL': "https://api.somewebsite.com", # URL of the backend API endpoint
    'BACKEND_PUBLIC_IP': "50.16.116.170", # public IP address of backend
    'BACKEND_PORT': 3000, # port number for backend (fixed typo from 'BACKED_PORT')
    'SSH_SOCKET_PATH': "/tmp/robot.sock" # path to unix socket for SSH communication
}


########## INFERENCE CONFIGURATIONS ##########

##### set ML configurations #####

INFERENCE_CONFIG = {
    'TPU_NAME': "MYRIAD",  # literal device name in code
    'CNN_PATH': "/home/matthewthomasbeck/Projects/Vending_Machine_Robot-Hardware/model/person-detection-0200.xml",  # person detection
}


########## ROBOT CONTROL CONFIGURATIONS (internet and radio) ##########

##### declare movement channel GPIO pins #####

SIGNAL_TUNING_CONFIG = { # dictionary of signal tuning configuration for sensitivity
    'JOYSTICK_THRESHOLD': 40, # number of times condition must be met to trigger a request on a joystick channel
    'TOGGLE_THRESHOLD': 40, # number of times condition must be met to trigger a request on a button channel
    'TIME_FRAME': 0.10017, # time frame for condition to be met, default: 0.100158
    'DEADBAND_HIGH': 1600, # deadband high for PWM signal
    'DEADBAND_LOW': 1400 # deadband low for PWM signal
}

##### set receiver configuration #####

MAESTRO_CONFIG = {
    'SERIAL_PATH': "/dev/serial0", # set serial port name to first available
    'SERIAL_BAUD_RATE': 9600, # set baud rate for serial connection
    'SERIAL_TIMEOUT': 1 # set timeout for serial connection
}

##### set GPS configuration #####

# GPS uses a *second* UART from dtoverlay (not /dev/serial0 — that is Maestro on GPIO 14/15).
# UART3 -> GPIO 4/5 conflicts with RIGHT_DCMC 'A_IN1' (GPIO 5). Prefer uart4 -> GPIO 8/9, or
# rewire BR A_IN1 to a free GPIO and change MOTOR_CONFIG if you use uart3.
# After uart4: run `ls /dev/ttyAMA*` — the GPS UART is usually ttyAMA1 (not ttyAMA0; that may be primary).
# If only ttyAMA0 exists, uart4 is not enabled (check dtoverlay=uart4 in /boot/firmware/config.txt).
GPS_CONFIG = {
    'SERIAL_PATH': "/dev/ttyAMA1",
    'SERIAL_BAUD_RATE': 9600,
    'SERIAL_TIMEOUT': 1
}

##### lid servo configuration #####

# Maestro servo speed units: (0.25 μs)/(10 ms)
# Speed = 200 means: 200 * 0.25 μs per 10ms = 50 μs per 10ms = 5,000 μs per second
# Example: moving 1000 μs at speed 200 takes ~200ms (plus acceleration time)
# Max speed = 16383 means: 16383 * 0.25 μs per 10ms = 4095.75 μs per 10ms = 409,575 μs per second (limited by physical servo)

LID_CONFIG = {
    'LEFT_HINGE_CHANNEL': 0, # maestro channel for lid servo (change as needed)
    'RIGHT_HINGE_CHANNEL': 1, # maestro channel for lid servo (change as needed)
    'CLOSED_POSITION_LEFT': 1000, # PWM microseconds for closed position
    'OPEN_POSITION_LEFT': 2000, # PWM microseconds for open position
    'CLOSED_POSITION_RIGHT': 1000, # PWM microseconds for closed position
    'OPEN_POSITION_RIGHT': 2000, # PWM microseconds for open position
    'SPEED': 16383, # servo speed: 5,000 μs/s max rate (0-16383, 0 = unlimited)
    'ACCELERATION': 255 # servo acceleration: max = 250 (0-255, 0 = unlimited)
}

##### lid lock servo configuration #####

LID_LOCK_CONFIG = {
    'LOCK_CHANNEL': 2, # maestro channel for lid lock servo (change as needed)
    'LOCKED_POSITION': 1500, # PWM microseconds for locked position
    'UNLOCKED_POSITION': 1000, # PWM microseconds for unlocked position
    'SPEED': 200, # servo speed: 5,000 μs/s max rate
    'ACCELERATION': 250 # servo acceleration: max = 250
}

##### dc motor controller configuration #####

# pin mapping (BCM):
# 11     GPIO 17  FRONT LEFT     A_IN1   (LEFT_DCMC motor A -> FL)
# 13     GPIO 27  FRONT LEFT     A_IN2   (LEFT_DCMC motor A -> FL)
# 15     GPIO 22  BACK LEFT      B_IN1   (LEFT_DCMC motor B -> BL)
# 16     GPIO 23  BACK LEFT      B_IN2   (LEFT_DCMC motor B -> BL)
# 29     GPIO 5   BACK RIGHT     A_IN1   (RIGHT_DCMC motor A -> BR)
# 31     GPIO 6   BACK RIGHT     A_IN2   (RIGHT_DCMC motor A -> BR)
# 38     GPIO 20  FRONT RIGHT    B_IN1   (RIGHT_DCMC motor B -> FR)
# 40     GPIO 21  FRONT RIGHT    B_IN2   (RIGHT_DCMC motor B -> FR)
#
# each controller also defines a MOTORS map that assigns logical wheel
# names (FL, FR, BL, BR) to a DCMC channel and an orientation flag;
# ORIENTATION maps clockwise/counterclockwise requests to
# correct electrical direction for that motor

MOTOR_CONFIG = {

    # LEFT side DCMC controller
    'LEFT_DCMC': {
        'A_IN1': 17,  # channel A direction (physical pin 11)  -> FL
        'A_IN2': 27,  # channel A direction (physical pin 13)  -> FL
        'B_IN1': 22,  # channel B direction (physical pin 15)  -> BL
        'B_IN2': 23,  # channel B direction (physical pin 16)  -> BL
        'PWM_FREQ_HZ': 1000,
        'MOTORS': {
            'FL': {
                'CHANNEL': 'A',
                'ORIENTATION': 1,  # 1 = clockwise->forward, -1 = clockwise->reverse
            },
            'BL': {
                'CHANNEL': 'B',
                'ORIENTATION': 1,
            },
        },
    },
    # RIGHT side DCMC controller
    'RIGHT_DCMC': {
        'A_IN1': 5,   # physical pin 29  -> BR
        'A_IN2': 6,   # physical pin 31  -> BR
        'B_IN1': 20,  # channel B direction (physical pin 38)  -> FR
        'B_IN2': 21,  # channel B direction (physical pin 40)  -> FR
        'PWM_FREQ_HZ': 1000,
        'MOTORS': {
            'FR': {
                'CHANNEL': 'B',
                'ORIENTATION': 1,
            },
            'BR': {
                'CHANNEL': 'A',
                'ORIENTATION': 1,
            },
        },
        # optional hardware PWM/EN pins when board has dedicated EN: GPIO 12, 13, 18, 19
    },
}

##### servo configuration #####

SERVO_CONFIG = { # dictionary of servo configurations TODO calibrate servo positions

    'LID': {'left_hinge': {'servo': 0, 'FULL_FRONT': 0.0, 'FULL_BACK': 0.0, 'FULL_FRONT_ANGLE': 0.0, 'FULL_BACK_ANGLE': 0.0},
            'right_hinge': {'servo': 1, 'FULL_FRONT': 0.0, 'FULL_BACK': 0.0, 'FULL_FRONT_ANGLE': 0.0, 'FULL_BACK_ANGLE': 0.0}},

    'LOCK': {'lock': {'servo': 3, 'FULL_FRONT': 0.0, 'FULL_BACK': 0.0, 'FULL_FRONT_ANGLE': 0.0, 'FULL_BACK_ANGLE': 0.0}}
}
