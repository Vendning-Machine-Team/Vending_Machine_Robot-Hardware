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

##### dc motor controller configuration #####

MOTOR_CONFIG = {
    
    'FRONT_DCMC': {
        'A_IN1': 17, # channel A direction (physical pin 11)
        'A_IN2': 27, # channel A direction (physical pin 13)
        'B_IN1': 22, # channel B direction (physical pin 15)
        'B_IN2': 23, # channel B direction (physical pin 16)
        'PWM_FREQ_HZ': 1000,
    },
    'BACK_DCMC': { # reserved for future second controller
        'A_IN1': 5,
        'A_IN2': 6,
        'B_IN1': 20,
        'B_IN2': 21,
        'PWM_FREQ_HZ': 1000,
        # optional hardware PWM/EN pins when board has dedicated EN: GPIO 12, 13, 18, 19
    },
}

##### set internet connectivity configuration #####

INTERNET_CONFIG = {
    'BACKEND_API_URL': "https://api.somewebsite.com", # URL of the backend API endpoint
    'BACKEND_PUBLIC_IP': "0.0.0.0", # public IP address of backend
    'BACKEND_PORT': 3000, # port number for backend (fixed typo from 'BACKED_PORT')
    'SSH_SOCKET_PATH': "/tmp/robot.sock" # path to unix socket for SSH communication
}
