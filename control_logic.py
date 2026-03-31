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


########## MANDATORY DEPENDENCIES ##########

##### mandatory libraries #####

import threading
import queue
import time
import os
import atexit
import socket
import logging
from collections import deque
import numpy as np
import cv2

##### mandatory dependencies #####

from utilities.log import initialize_logging
import utilities.config as config
import utilities.internet as internet  # dynamically import internet utilities to be constantly updated

##### (pre)initialize all utilities #####

LOGGER = initialize_logging()
CAMERA_PROCESS = None
CHANNEL_DATA = {}
SOCK = None
COMMAND_QUEUE = None
ROBOT_ID = None
JOINT_MAP = {}
DETECTION_MODEL = None
DETECTION_INPUT_LAYER = None
DETECTION_OUTPUT_LAYER = None


##### movement functions #####

from movement.mecanum import *
from utilities.motors import initialize_motor_controllers, stop_all, run_back_motors

atexit.register(stop_all)


########## PREPARE ROBOT ##########

##### prepare real robot #####

def set_real_robot_dependencies():  # function to initialize real robot dependencies

    ##### import necessary functions #####

    from utilities.camera import initialize_camera  # import to start camera logic
    import utilities.internet as internet  # dynamically import internet utilities to be constantly updated

    ##### initialize global variables #####

    global CAMERA_PROCESS, SOCK, COMMAND_QUEUE, ROBOT_ID, JOINT_MAP, internet
    global DETECTION_MODEL, DETECTION_INPUT_LAYER, DETECTION_OUTPUT_LAYER

    ##### initialize camera process #####

    CAMERA_PROCESS = initialize_camera()  # create camera process
    if CAMERA_PROCESS is None:
        logging.error("(control_logic.py): Failed to initialize CAMERA_PROCESS for robot!\n")

    ##### initialize socket and codes queue #####

    if config.CONTROL_MODE == 'web':  # if web control mode and robot needs a socket connection for controls and video...
         SOCK = internet.initialize_backend_socket()  # initialize EC2 socket connection
         COMMAND_QUEUE = internet.initialize_command_queue(SOCK)  # initialize codes queue for socket communication
         if SOCK is None:
             logging.error("(control_logic.py): Failed to initialize SOCK for robot!\n")
         if COMMAND_QUEUE is None:
             logging.error("(control_logic.py): Failed to initialize COMMAND_QUEUE for robot!\n")
    if config.CONTROL_MODE == 'web':
        COMMAND_QUEUE = queue.Queue()  # empty queue for testing; no backend connection

    ##### initialize SSDLite person detection model #####

    from utilities import inference
    model_path = config.INFERENCE_CONFIG.get('CNN_PATH') or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'model', 'ssdlite_mobilenet_v2.xml'
    )
    if os.path.isfile(model_path):
        DETECTION_MODEL, DETECTION_INPUT_LAYER, DETECTION_OUTPUT_LAYER = inference.load_and_compile_model(model_path)
        if DETECTION_MODEL is None:
            logging.warning("(control_logic.py): SSDLite model failed to load; person detection disabled.\n")
    else:
        logging.warning(f"(control_logic.py): SSDLite model not found at {model_path}; person detection disabled.\n")

    ##### initialize motors #####

    initialize_motor_controllers()


########## PREPARE ROBOT ##########

##### prepare robot with correct dependencies #####

set_real_robot_dependencies()

##### post-initialization dependencies #####

# from movement.movement_coordinator import * TODO import vending machine robot equivalent package here
from utilities.camera import decode_real_frame
from utilities import inference





#########################################
############### RUN ROBOT ###############
#########################################


########## STATE MACHINE LOOPS ##########

##### set global variables #####

IMAGELESS_GAIT = True  # set global variable for imageless gait
IS_COMPLETE = True  # boolean that tracks if the robot is done moving, independent of it being neutral or not
IS_NEUTRAL = False  # set global neutral standing boolean
CURRENT_LEG = 'FL'  # set global current leg

##### person detection variables #####

# person detection smoothing (debounce) to prevent start/stop chattering
PERSON_DETECTED_FRAMES_TO_START = 1  # require N consecutive "person detected" frames
PERSON_ABSENT_FRAMES_TO_STOP = 24  # require M consecutive "person not detected" frames
PERSON_MIN_MOVE_SECONDS = 0.60  # minimum time to keep moving once started
PERSON_ABSENT_HOLD_SECONDS = 0.50  # keep moving this long after last positive detection
PERSON_DETECTED_STREAK = 0  # consecutive frames with person_detected == True
PERSON_ABSENT_STREAK = 0  # consecutive frames with person_detected == False
PERSON_STATE_MOVING = False  # whether motors are currently commanded to move
PERSON_LAST_STATE_CHANGE_TIME = 0.0  # used to enforce minimum move time
PERSON_LAST_DETECTED_TIME = 0.0  # tracks when a person was last positively detected


##### physical loop #####

def _physical_loop():  # central function that runs robot in real life

    ##### set/initialize variables #####

    global IS_COMPLETE, IS_NEUTRAL, CURRENT_LEG  # declare as global as these will be edited by function
    global PERSON_DETECTED_STREAK, PERSON_ABSENT_STREAK
    global PERSON_STATE_MOVING, PERSON_LAST_STATE_CHANGE_TIME, PERSON_LAST_DETECTED_TIME
    mjpeg_buffer = b''  # initialize buffer for MJPEG frames

    ##### run robotic logic #####

    try:  # try to run robot startup sequence
        # neutral_position(1) # TODO set vending machine idle equivalent here
        time.sleep(3)
        IS_NEUTRAL = True  # set is_neutral to True

    except Exception as e:  # if there is an error, log error
        logging.error(f"(control_logic.py): Failed to move to neutral standing position in runRobot: {e}\n")

    ##### stream video, run inference, and control the robot #####

    try:  # try to run main robotic process

        while True:  # central loop to entire process, commenting out of importance

            mjpeg_buffer, _, inference_frame = decode_real_frame(  # run camera and decode frame (no video stream to backend)
                CAMERA_PROCESS,
                mjpeg_buffer
            )

            person_detected = inference.run_person_detection( # check if person detected
                DETECTION_MODEL, DETECTION_INPUT_LAYER, DETECTION_OUTPUT_LAYER,
                inference_frame, run_inference=True
            )

            # TODO AI/Pathfinding team can create behaviors here
            now = time.time()

            if person_detected:
                PERSON_DETECTED_STREAK += 1
                PERSON_ABSENT_STREAK = 0
                PERSON_LAST_DETECTED_TIME = now
            else:
                PERSON_ABSENT_STREAK += 1
                PERSON_DETECTED_STREAK = 0

            # transition STOP -> MOVE
            if (not PERSON_STATE_MOVING) and (PERSON_DETECTED_STREAK >= PERSON_DETECTED_FRAMES_TO_START):
                #run_back_motors(10)  # test rear motors on person detection
                forward(10)
                PERSON_STATE_MOVING = True
                PERSON_LAST_STATE_CHANGE_TIME = now

            # transition MOVE -> STOP (with a minimum move hold time)
            elif PERSON_STATE_MOVING and (PERSON_ABSENT_STREAK >= PERSON_ABSENT_FRAMES_TO_STOP):
                enough_move_time = (now - PERSON_LAST_STATE_CHANGE_TIME) >= PERSON_MIN_MOVE_SECONDS
                absent_hold_elapsed = (now - PERSON_LAST_DETECTED_TIME) >= PERSON_ABSENT_HOLD_SECONDS
                if enough_move_time and absent_hold_elapsed:
                    stop_all()
                    PERSON_STATE_MOVING = False
                    PERSON_LAST_STATE_CHANGE_TIME = now

            if inference_frame is not None:
                cv2.imshow("SSDLite detection", inference_frame)
                cv2.waitKey(1)

            codes = None  # initially no codes

            if config.CONTROL_MODE == 'web':  # if web control enabled...
                if COMMAND_QUEUE is not None and not COMMAND_QUEUE.empty():  # if codes queue is not empty...
                    codes = COMMAND_QUEUE.get()  # get codes from queue
                    if codes is not None:
                        if IS_COMPLETE:  # if movement is complete, run codes
                            logging.info(f"(control_logic.py): Received codes '{codes}' from queue (WILL RUN).\n")
                        else:
                            logging.info(f"(control_logic.py): Received codes '{codes}' from queue (BLOCKED).\n")

            if codes and IS_COMPLETE:  # if codes present and movement complete...
                # logging.debug(f"(control_logic.py): Running codes: {codes}...\n")
                threading.Thread(target=_handle_command, args=(codes), daemon=True).start()

            elif not codes and IS_COMPLETE and not IS_NEUTRAL:  # if no codes and move complete and not neutral...
                logging.debug(f"(control_logic.py): No codes received.\n")
                threading.Thread(target=_handle_command, args=('n'), daemon=True).start()

    except KeyboardInterrupt:  # if user ends program...
        logging.info("(control_logic.py): KeyboardInterrupt received, exiting.\n")
        stop_all()

    except Exception as e:  # if something breaks and only God knows what it is...
        logging.error(f"(control_logic.py): Unexpected exception in main loop: {e}\n")
        stop_all()
        exit(1)

    finally:
        stop_all()


########## HANDLE COMMANDS ##########

def _handle_command(codes):
    # logging.debug(f"(control_logic.py): Threading codes: {codes}...\n")

    global IS_COMPLETE, IS_NEUTRAL
    IS_COMPLETE = False  # block new commands until movement is complete

    if isinstance(codes, str):
        if '+' in codes:
            commands = codes.split('+')
        elif codes == 'n':
            commands = []
        else:
            commands = [codes]
    elif isinstance(codes, (list, tuple)):
        commands = list(codes)
    elif isinstance(codes, dict):
        commands = []  # not used for radio mode
    else:
        commands = []

    if config.CONTROL_MODE == 'web':
        try:
            IS_NEUTRAL = _execute_commands(
                commands,
                IS_NEUTRAL
            )
            # logging.info(f"(control_logic.py): Executed keyboard codes: {commands}\n")
            IS_COMPLETE = True
        except Exception as e:
            logging.error(f"(control_logic.py): Failed to execute keyboard command: {e}\n")
            IS_NEUTRAL = False
            IS_COMPLETE = True


########## EXECUTE COMMANDS ##########

def _convert_direction_parts_to_fixed_list(direction_parts):

    fixed_direction = [None, None, None, None] # initialize fixed-length list with None values
    
    for part in direction_parts:
        if part in ['w', 's']:
            fixed_direction[0] = part
        elif part in ['a', 'd']:
            fixed_direction[1] = part
        elif part in ['arrowleft', 'arrowright']:
            fixed_direction[2] = part
        elif part in ['arrowup', 'arrowdown']:
            fixed_direction[3] = part
        elif part in ['w+a', 'w+d', 's+a', 's+d']:
            if 'w' in part:
                fixed_direction[0] = 'w'
            elif 's' in part:
                fixed_direction[0] = 's'
            if 'a' in part:
                fixed_direction[1] = 'a'
            elif 'd' in part:
                fixed_direction[1] = 'd'
    
    return fixed_direction


########## COMMANDS FROM BACKEND ##########

def _execute_commands(commands, is_neutral):

    ##### set variables #####

    global IMAGELESS_GAIT # set IMAGELESS_GAIT as global to switch between modes via button press
    direction_parts = [] # diretion part list

    ##### handle special toggle commands #####

    if 'i' in commands:  # if user wishes to enable/disable imageless gait...
        IMAGELESS_GAIT = not IMAGELESS_GAIT  # toggle imageless gait mode
        logging.warning(f"(control_logic.py): Toggled IMAGELESS_GAIT to {IMAGELESS_GAIT}\n")
        commands = [k for k in commands if k != 'i']  # remove 'i' from the commands list

    ##### handle lid control commands #####

    if 'o' in commands:  # 'o' for open lid
        from movement.lid import open_lid
        open_lid()
        commands = [k for k in commands if k != 'o']

    if 'c' in commands:  # 'c' for close lid
        from movement.lid import close_lid
        close_lid()
        commands = [k for k in commands if k != 'c']

    if 'locklid' in commands:  # 'lockid' to manually lock
        from movement.lid import lock_lid_position
        lock_lid_position()
        commands = [k for k in commands if k != 'lockid']

    if 'unlockid' in commands:  # 'unlockid' to manually unlock
        from movement.lid import unlock_lid_position
        unlock_lid_position()
        commands = [k for k in commands if k != 'unlockid']

    ##### cancel out contradictory commands #####

    if 'w' in commands and 's' in commands:
        commands = [k for k in commands if k not in ['w', 's']]
    if 'a' in commands and 'd' in commands:
        commands = [k for k in commands if k not in ['a', 'd']]
    if 'arrowleft' in commands and 'arrowright' in commands:
        commands = [k for k in commands if k not in ['arrowleft', 'arrowright']]
    if 'arrowup' in commands and 'arrowdown' in commands:
        commands = [k for k in commands if k not in ['arrowup', 'arrowdown']]

    ##### WASD and diagonals #####

    move_forward = 'w' in commands
    move_backward = 's' in commands
    shift_left = 'a' in commands
    shift_right = 'd' in commands

    ##### rotation #####

    rotate_left = 'arrowleft' in commands
    rotate_right = 'arrowright' in commands

    ##### tilt #####

    tilt_up = 'arrowup' in commands
    tilt_down = 'arrowdown' in commands

    ##### handle diagonals #####

    if move_forward and shift_left:
        direction_parts.append('w+a')
    elif move_forward and shift_right:
        direction_parts.append('w+d')
    elif move_backward and shift_left:
        direction_parts.append('s+a')
    elif move_backward and shift_right:
        direction_parts.append('s+d')

    ##### handle single directions #####

    elif move_forward:
        direction_parts.append('w')
    elif move_backward:
        direction_parts.append('s')
    elif shift_left:
        direction_parts.append('a')
    elif shift_right:
        direction_parts.append('d')

    ##### handle rotation #####

    if rotate_left:
        direction_parts.append('arrowleft')
    elif rotate_right:
        direction_parts.append('arrowright')

    ##### handle tilt #####

    if tilt_up:
        direction_parts.append('arrowup')
    elif tilt_down:
        direction_parts.append('arrowdown')

    ##### combine all direction parts into fixed-length list #####

    direction = None
    if direction_parts:
        direction = _convert_direction_parts_to_fixed_list(direction_parts)
    if 'n' in commands or not commands:
        # neutral_position(10) # TODO set vending machine idle equivalent here
        is_neutral = True
    elif direction:
        # move_direction(direction, camera_frames, intensity, IMAGELESS_GAIT) # TODO set vending machine movement equivalent here
        is_neutral = False
    else:
        logging.warning(f"(control_logic.py): Invalid command: {commands}.\n")

    return is_neutral


########## MISCELLANEOUS CONTROL FUNCTIONS ##########

def restart_process():  # start background thread to restart robot_dog.service every 30 minutes by checking elapsed time
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed >= 1800:  # 30 minutes = 1800 seconds
            os.system('sudo systemctl restart robot_dog.service')
            start_time = time.time()  # reset timer after restart
        time.sleep(1)  # check every second


def send_voltage_to_backend(voltage):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', 3000))  # Use backend's IP if remote
        msg = f'VOLTAGE:{voltage:.4f}'
        s.sendall(msg.encode())
        s.close()
    except Exception as e:
        logging.error(f"(control_logic.py) Failed to send voltage: {e}\n")


def voltage_monitor():
    while True:
        voltage_output = os.popen('vcgencmd measure_voltage').read()
        voltage_str = voltage_output.strip().replace('volt=', '').replace('V', '')
        try:
            voltage = float(voltage_str)
            if voltage < 0.8600:
                logging.warning(f"(control_logic.py) Low voltage ({voltage:.4f}V) detected!\n")
            send_voltage_to_backend(voltage)
        except ValueError:
            logging.error(f"(control_logic.py) Failed to parse voltage: {voltage_output}\n")
        time.sleep(10)  # check every 10 seconds


########## RUN ROBOTIC PROCESS ##########

restart_thread = threading.Thread(target=restart_process, daemon=True)
restart_thread.start()
# voltage_thread = threading.Thread(target=voltage_monitor, daemon=True)
# voltage_thread.start()
_physical_loop()  # run robot process
