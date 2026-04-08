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

import logging # import logging library for debugging





#####################################################
############### LOGGING CONFIGURATION ###############
#####################################################

########## LOGGING ##########

##### set logging configuration #####

LOG_CONFIG = {
    'LOG_PATH': "/home/matthewthomasbeck/Projects/Vending_Machine_Robot-Hardware/vending_machine.log", # path to log file DO NOT CHANGE
    'LOG_LEVEL': logging.INFO # set log level to logging.<DEBUG, INFO, WARNING, ERROR, or CRITICAL>
}





###########################################################
############### CAMERA AND AI CONFIGURATION ###############
###########################################################


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




###########################################################################
############### INTERNET AND GPS CONNECTIVITY CONFIGURATION ###############
###########################################################################


########## INTERNET/FRONTEND CONFIGURATIONS ##########

##### internet config (to connect to backend) #####

INTERNET_CONFIG = {
    'BACKEND_API_URL': "https://api.somewebsite.com", # URL of the backend API endpoint
    'BACKEND_PUBLIC_IP': "50.16.116.170", # public IP address of backend
    'BACKEND_PORT': 3000, # port number for backend (fixed typo from 'BACKED_PORT')
    'SSH_SOCKET_PATH': "/tmp/robot.sock" # path to unix socket for SSH communication
}

##### used to display what was sent from the backend #####

SCREEN_CONFIG = {
    'WIDTH': 800, # width of the screen in pixels
    'HEIGHT': 480, # height of the screen in pixels
    'FPS': 30, # frames per second for screen updates
}


########## GPS CONFIGURATION ##########

##### set GPS configuration #####

# UART4 (dtoverlay=uart4, GPIO 8/9) — not /dev/serial0. Enumeration varies; confirm with `ls /dev/ttyAMA*`.
# UART3 on GPIO 4/5 conflicts with RIGHT_DCMC A_IN1 (GPIO 5); prefer uart4 or rewire that motor.
GPS_CONFIG = {
    'SERIAL_PATH': "/dev/ttyAMA4",
    'SERIAL_BAUD_RATE': 9600,
    'SERIAL_TIMEOUT': 1
}





############################################################
############### PHYSICAL ROBOT CONFIGURATION ###############
############################################################


########## SERVOS COMMUNICATION CONFIGURATION ##########

##### servo configuration #####

SERVO_CONFIG = { # dictionary of servo configurations TODO calibrate servo positions

    'LID': {'left_hinge': {'servo': 0, 'FULL_FRONT': 0.0, 'FULL_BACK': 0.0, 'FULL_FRONT_ANGLE': 0.0, 'FULL_BACK_ANGLE': 0.0},
            'right_hinge': {'servo': 1, 'FULL_FRONT': 0.0, 'FULL_BACK': 0.0, 'FULL_FRONT_ANGLE': 0.0, 'FULL_BACK_ANGLE': 0.0}},

    'LOCK': {'lock': {'servo': 3, 'FULL_FRONT': 0.0, 'FULL_BACK': 0.0, 'FULL_FRONT_ANGLE': 0.0, 'FULL_BACK_ANGLE': 0.0}}
}

##### maestro config #####

MAESTRO_CONFIG = { # on Pi OS, /dev/serial0 often symlinks to ttyS0 (mini UART on GPIO 14/15) for maestro
    'SERIAL_PATH': "/dev/serial0",
    'SERIAL_BAUD_RATE': 9600,
    'SERIAL_TIMEOUT': 1
}


########## LID CONFIGURATION ##########

##### lid servo configuration #####

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


########## DC MOTOR CONTROLLER CONFIGURATION ##########

##### dc motor controller configuration #####

MOTOR_CONFIG = {

    'LEFT_DCMC': {
        'A_IN1': 17,  # pin 11, GPIO 17, FRONT LEFT, A_IN1 (LEFT_DCMC motor A -> FL)
        'A_IN2': 27,  # pin 13, GPIO 27, FRONT LEFT, A_IN2 (LEFT_DCMC motor A -> FL)
        'B_IN1': 22,  # pin 15, GPIO 22, BACK LEFT, B_IN1 (LEFT_DCMC motor B -> BL)
        'B_IN2': 23,  # pin 16, GPIO 23, BACK LEFT, B_IN2 (LEFT_DCMC motor B -> BL)
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
    'RIGHT_DCMC': {
        'A_IN1': 5,  # pin 29, GPIO 5, BACK RIGHT, A_IN1 (RIGHT_DCMC motor A -> BR)
        'A_IN2': 6,  # pin 31, GPIO 6, BACK RIGHT, A_IN2 (RIGHT_DCMC motor A -> BR)
        'B_IN1': 20,  # pin 38, GPIO 20, FRONT RIGHT, B_IN1 (RIGHT_DCMC motor B -> FR)
        'B_IN2': 21,  # pin 40, GPIO 21, FRONT RIGHT, B_IN2 (RIGHT_DCMC motor B -> FR)
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
    },
}