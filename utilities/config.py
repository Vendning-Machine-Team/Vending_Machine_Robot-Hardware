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





############################################################
############### ROBOT BEHAVIOR CONFIGURATION ###############
############################################################


########## PERSON DETECTION BEHAVIOR ##########

##### debounce and motion gating for person-follow behavior #####

PERSON_DETECTION_CONFIG = {
    'DETECTED_FRAMES_TO_START': 1,   # require N consecutive "person detected" frames
    'ABSENT_FRAMES_TO_STOP': 24,     # require M consecutive "person not detected" frames
    'MIN_MOVE_SECONDS': 0.60,        # minimum time to keep moving once started
    'ABSENT_HOLD_SECONDS': 0.50,     # keep moving this long after last positive detection
}


########## PERSON APPROACH BEHAVIOR ##########

##### steering and stopping thresholds for approach logic #####

PERSON_APPROACH_CONFIG = {
    'FRAME_WIDTH': 640,         # must match CAMERA_CONFIG['WIDTH']
    'STOP_AREA': 45000,         # stop when person's box area reaches this threshold
    'DEADBAND': 92,             # horizontal pixel deadband around frame center
    'INTENSITY': 10,            # default motor intensity during approach
    'SLOWDOWN_AREA': 30000,     # start slowing down when box area reaches this threshold
    'SLOW_INTENSITY': 10,       # reduced intensity while inside slowdown zone
}


########## FORCE SALE BEHAVIOR ##########

##### rotation scan intensity for re-acquiring a lost person #####

FORCE_SALE_CONFIG = {
    'ROTATE_INTENSITY': 10,         # low intensity for in-place rotation scan when person exits frame (maps to ~20% PWM)
    'MAX_ENGAGEMENT_SECONDS': 300,  # total seconds allowed with one person before robot gives up and finds someone else; change to e.g. 10 for quick testing
    'HOLD_DEADBAND': 150,           # pixel deadband for sighted re-centering inside State 1 HOLD; wider than PERSON_APPROACH_CONFIG DEADBAND (92px) intentionally — robot is stationary so more drift is tolerated before nudging; smaller = tighter centering, larger = more tolerance
}


########## FIND CUSTOMER BEHAVIOR ##########

##### spin duration and intensity for 180 degree turn when searching for a new customer #####

FIND_CUSTOMER_CONFIG = {
    'SPIN_INTENSITY': 10,   # PWM intensity for the 180° turn — needs hardware tuning on real floor surface; higher = faster spin, lower = slower; range 1-10
    'SPIN_DURATION': 1.5,   # seconds to spin at SPIN_INTENSITY to achieve approximately 180° turn — needs hardware tuning; increase if robot undershoots, decrease if overshoots
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
    'WIDTH': 640, # width of the camera image (input for CNN)
    'HEIGHT': 480, # height of the camera image (input for CNN)
    'FRAME_RATE': 30, # frame rate of the camera in frames per second
    'CROP_FRACTION': 1.0, # fraction of the image to crop from each side (0.0 to 1.0)
    'OUTPUT_WIDTH': 640, # width of the ML image (output for CNN)
    'OUTPUT_HEIGHT': 480, # height of the ML image (output for CNN)
}


########## INFERENCE CONFIGURATIONS ##########

##### set ML configurations #####

INFERENCE_CONFIG = {
    'TPU_NAME': "MYRIAD",  # literal device name in code
    'CNN_PATH': "/home/matthewthomasbeck/Projects/Vending_Machine_Robot-Hardware/model/person-detection-0200.xml",  # person detection
    'SHOW_SCREEN': False
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

##### sale configuration #####

SALE_CONFIG = {
    'SALE_TIMEOUT_SECONDS': 120, # max time to wait for customer to complete a sale (prevents infinite hang)
    'MAX_CODE_ATTEMPTS': 3, # max number of times a user can try to enter the code before the sale is considered failed
}

########## GPS CONFIGURATION ##########

##### set GPS configuration #####

# UART4 (dtoverlay=uart4, GPIO 8/9) — not /dev/serial0. Enumeration varies; confirm with `ls /dev/ttyAMA*`.
# UART3 on GPIO 4/5 conflicts with RIGHT_DCMC A_IN1 (GPIO 5); prefer uart4 or rewire that motor.
GPS_CONFIG = {
    'SERIAL_PATH': "/dev/ttyAMA4",
    'SERIAL_BAUD_RATE': 9600,
    'SERIAL_TIMEOUT': 1,
    'CHECK_INTERVAL_SECONDS': 10, # interval to check for lat and lon coordinates (in seconds)
}

##### set robot boundaries configuration #####

LOCATION_CONFIG = { #TODO add VERY ACCURATE coordinates to the sombrilla enterance
    'HOME_LAT': 29.0,
    'HOME_LON': 29.0,
    'ACCEPTABLE_RANGE': 30.0, # acceptable range away from lat/lon in meters
    'LAST_DISTANCE_FROM_HOME': 0.0, # last distance from home in meters
    'LAST_LAT': 0.0,
    'LAST_LON': 0.0,
    'LAST_FACING': 0.0, # last N/S/E/W course from home
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
    'LOCKED_POSITION': 1000, # PWM microseconds for locked position
    'UNLOCKED_POSITION': 2000, # PWM microseconds for unlocked position
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