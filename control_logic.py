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
import json
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
from movement.customer_interaction import approach_largest_person

#atexit.register(stop_all)

##### import GPS functions #####

from utilities.gps import *


########## PREPARE ROBOT ##########

##### prepare real robot #####

def set_real_robot_dependencies():  # function to initialize real robot dependencies

    ##### import necessary functions #####

    from utilities.camera import initialize_camera  # import to start camera logic
    import utilities.internet as internet  # dynamically import internet utilities to be constantly updated

    ##### initialize global variables #####

    global CAMERA_PROCESS, SOCK, COMMAND_QUEUE, ROBOT_ID, JOINT_MAP, GPS
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

    ##### initialize GPS #####

    GPS = initialize_gps()  # initialize GPS connection

    if GPS is None:
        logging.warning("(control_logic.py): Failed to initialize GPS for robot!\n")
    else:
        logging.info("(control_logic.py): Successfully initialized GPS for robot.\n")


########## PREPARE ROBOT ##########

##### prepare robot with correct dependencies #####

set_real_robot_dependencies()

##### post-initialization dependencies #####

from utilities.camera import decode_real_frame
from utilities import inference





#########################################
############### RUN ROBOT ###############
#########################################


########## STATE MACHINE LOOPS ##########

##### set global variables #####

IS_COMPLETE = True  # boolean that tracks if the robot is done moving, independent of it being neutral or not
IS_NEUTRAL = False  # set global neutral standing boolean

##### person detection variables #####

PERSON_DETECTED_STREAK = 0  # consecutive frames with person_detected == True
PERSON_ABSENT_STREAK = 0  # consecutive frames with person_detected == False
PERSON_STATE_MOVING = False  # whether motors are currently commanded to move
PERSON_LAST_STATE_CHANGE_TIME = 0.0  # used to enforce minimum move time
PERSON_LAST_DETECTED_TIME = 0.0  # tracks when a person was last positively detected

##### asynchronous worker state #####

MOVEMENT_STATE_LOCK = threading.Lock()
GPS_STATE_LOCK = threading.Lock()

PERSON_MOVEMENT_QUEUE = queue.Queue(maxsize=1)
LAST_MOVEMENT_CMD = {
    'person_detected': False,
    'target_cx': None,
    'largest_box_area': None,
    'timestamp': 0.0
}

LATEST_COORDINATES = {'lat': None, 'lon': None}
LAST_GPS_CHECK_TIME = 0.0
GPS_CHECK_IN_PROGRESS = False

GPS_CHECK_INTERVAL_SECONDS = 2.0


##### physical loop #####

def _physical_loop():  # central function that runs robot in real life

    ##### set/initialize variables #####

    global IS_COMPLETE, IS_NEUTRAL # declare as global as these will be edited by function
    global PERSON_DETECTED_STREAK, PERSON_ABSENT_STREAK
    global PERSON_STATE_MOVING, PERSON_LAST_STATE_CHANGE_TIME, PERSON_LAST_DETECTED_TIME
    mjpeg_buffer = b''  # initialize buffer for MJPEG frames

    ##### run robotic logic #####

    try:  # try to run robot startup sequence
        # neutral_position(1) # TODO set vending machine idle equivalent here
        time.sleep(3)
        IS_NEUTRAL = True  # set is_neutral to True

        ##### start asynchronous worker threads #####

        _handle_command('movement_worker')
        _handle_command('gps_worker')

    except Exception as e:  # if there is an error, log error
        logging.error(f"(control_logic.py): Failed to move to neutral standing position in runRobot: {e}\n")

    ##### stream video, run inference, and control the robot #####

    try:  # try to run main robotic process

        while True:  # central loop to entire process, commenting out of importance

            mjpeg_buffer, _, inference_frame = decode_real_frame(  # run camera and decode frame (no video stream to backend)
                CAMERA_PROCESS,
                mjpeg_buffer
            )

            # run person detection on the current decoded camera frame via OpenVINO + Myriad VPU
            # returns three values:
            #   person_detected  — True if at least one person is above 0.5 confidence
            #   target_cx        — horizontal pixel center of the largest detected person box
            #   largest_box_area — area (px²) of the largest box, used as a distance proxy
            person_detected, target_cx, largest_box_area = inference.run_person_detection(
                DETECTION_MODEL, DETECTION_INPUT_LAYER, DETECTION_OUTPUT_LAYER,
                inference_frame, run_inference=True
            )
            logging.debug(
                f"(control_logic.py): Inference unpacked — "
                f"person_detected={person_detected}, "
                f"target_cx={target_cx}px, "
                f"largest_box_area={largest_box_area}px².\n"
            )

            # TODO AI/Pathfinding team can create behaviors here
            now = time.time()

            if person_detected:
                if _should_check_gps(now):
                    _handle_command('gps_check')
                PERSON_DETECTED_STREAK += 1
                PERSON_ABSENT_STREAK = 0
                PERSON_LAST_DETECTED_TIME = now
            else:
                PERSON_ABSENT_STREAK += 1
                PERSON_DETECTED_STREAK = 0

            # transition STOP -> MOVE
            if (not PERSON_STATE_MOVING) and (
                PERSON_DETECTED_STREAK >= config.PERSON_DETECTION_CONFIG['DETECTED_FRAMES_TO_START']
            ):
                with MOVEMENT_STATE_LOCK:
                    PERSON_STATE_MOVING = True
                    PERSON_LAST_STATE_CHANGE_TIME = now

            # transition MOVE -> STOP (with a minimum move hold time)
            elif PERSON_STATE_MOVING and (
                PERSON_ABSENT_STREAK >= config.PERSON_DETECTION_CONFIG['ABSENT_FRAMES_TO_STOP']
            ):
                enough_move_time = (
                    (now - PERSON_LAST_STATE_CHANGE_TIME) >= config.PERSON_DETECTION_CONFIG['MIN_MOVE_SECONDS']
                )
                absent_hold_elapsed = (
                    (now - PERSON_LAST_DETECTED_TIME) >= config.PERSON_DETECTION_CONFIG['ABSENT_HOLD_SECONDS']
                )
                if enough_move_time and absent_hold_elapsed:
                    stop_all()
                    with MOVEMENT_STATE_LOCK:
                        PERSON_STATE_MOVING = False
                        PERSON_LAST_STATE_CHANGE_TIME = now

            # movement is dispatched to a dedicated worker thread so inference remains real-time
            _handle_command('movement_step', {
                'person_detected': person_detected,
                'target_cx': target_cx,
                'largest_box_area': largest_box_area,
                'timestamp': now
            })

            if inference_frame is not None:
                cv2.imshow("SSDLite detection", inference_frame)
                cv2.waitKey(1)

            request_payload = _request_user_codes()
            if request_payload is not None:
                _handle_command('queue_request', request_payload)

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

def _handle_command(command_type, payload=None):
    # logging.debug(f"(control_logic.py): Threading command type: {command_type}...\n")

    worker_map = {
        'movement_worker': _movement_worker_loop,
        'movement_step': _queue_movement_step,
        'gps_worker': _gps_worker_loop,
        'gps_check': _request_gps_check,
        'queue_request': _process_code_request,
    }

    worker = worker_map.get(command_type)
    if worker is None:
        logging.warning(f"(control_logic.py): Unknown threaded command type '{command_type}'.\n")
        return

    if command_type == 'movement_step':
        worker(payload)
        return

    # fire and forget for every command category (movement/gps/queue processing)
    threading.Thread(target=worker, args=(payload,), daemon=True).start()


########## REQUEST USER CODES FROM QUEUE ##########

def _request_user_codes():
    if config.CONTROL_MODE != 'web':
        return None
    if COMMAND_QUEUE is None or COMMAND_QUEUE.empty():
        return None

    raw_payload = COMMAND_QUEUE.get()
    request = _parse_code_request(raw_payload)
    if request is None:
        logging.warning(f"(control_logic.py): Invalid queue payload received: {raw_payload}\n")
        return None

    logging.info(
        f"(control_logic.py): Pulled queued purchase verification request "
        f"(email='{request['email']}', code='{request['code']}').\n"
    )
    return request


########## QUEUE PAYLOAD PARSING ##########

def _parse_code_request(raw_payload):
    ##### normalize payload to dict #####

    payload_obj = None
    if isinstance(raw_payload, dict):
        payload_obj = raw_payload
    elif isinstance(raw_payload, str):
        stripped = raw_payload.strip()
        if not stripped:
            return None
        try:
            payload_obj = json.loads(stripped)
        except Exception:
            # support plain string fallback: "code+email@example.com"
            if '+' in stripped:
                code_part, email_part = stripped.split('+', 1)
                payload_obj = {'code': code_part.strip(), 'email': email_part.strip()}
            elif ',' in stripped:
                code_part, email_part = stripped.split(',', 1)
                payload_obj = {'code': code_part.strip(), 'email': email_part.strip()}
            else:
                return None
    else:
        return None

    ##### read supported key names from backend payload #####

    code_value = (
        payload_obj.get('code')
        or payload_obj.get('verificationCode')
        or payload_obj.get('userCode')
    )
    email_value = (
        payload_obj.get('email')
        or payload_obj.get('userEmail')
        or payload_obj.get('customerEmail')
    )

    if code_value is None or email_value is None:
        return None

    code_value = str(code_value).strip()
    email_value = str(email_value).strip()
    if not code_value or not email_value:
        return None

    return {'code': code_value, 'email': email_value}


########## QUEUE REQUEST HANDLER ##########

def _process_code_request(request_payload):
    global IS_COMPLETE

    if request_payload is None:
        return

    IS_COMPLETE = False
    try:
        # TODO integrate screen prompt + entered code validation in this function
        logging.info(
            f"(control_logic.py): Ready to display queued user email '{request_payload['email']}' "
            f"and verify entered code against '{request_payload['code']}'.\n"
        )
    except Exception as e:
        logging.error(f"(control_logic.py): Failed while processing queued user code request: {e}\n")
    finally:
        IS_COMPLETE = True


########## MOVEMENT WORKER HELPERS ##########

def _movement_worker_loop(_):
    while True:
        movement_payload = PERSON_MOVEMENT_QUEUE.get()
        try:
            _execute_person_movement_step(movement_payload)
        except Exception as e:
            logging.error(f"(control_logic.py): movement worker failed for payload {movement_payload}: {e}\n")


def _queue_movement_step(movement_payload):
    if movement_payload is None:
        return

    while not PERSON_MOVEMENT_QUEUE.empty():
        try:
            PERSON_MOVEMENT_QUEUE.get_nowait()
        except queue.Empty:
            break

    PERSON_MOVEMENT_QUEUE.put_nowait(movement_payload)


def _execute_person_movement_step(movement_payload):
    global LAST_MOVEMENT_CMD
    person_detected = bool(movement_payload.get('person_detected'))
    target_cx = movement_payload.get('target_cx')
    largest_box_area = movement_payload.get('largest_box_area')
    now = movement_payload.get('timestamp', time.time())

    with MOVEMENT_STATE_LOCK:
        is_moving = PERSON_STATE_MOVING

    if is_moving and person_detected:
        logging.info(
            f"(control_logic.py): Robot is moving and person is visible — "
            f"steering toward person "
            f"(target_cx={target_cx}px, box_area={largest_box_area}px²).\n"
        )
        approach_largest_person(target_cx, largest_box_area)

    LAST_MOVEMENT_CMD = {
        'person_detected': person_detected,
        'target_cx': target_cx,
        'largest_box_area': largest_box_area,
        'timestamp': now
    }


########## GPS WORKER HELPERS ##########

def _gps_worker_loop(_):
    while True:
        time.sleep(1.0)


def _should_check_gps(now):
    with GPS_STATE_LOCK:
        return (now - LAST_GPS_CHECK_TIME) >= GPS_CHECK_INTERVAL_SECONDS and not GPS_CHECK_IN_PROGRESS


def _request_gps_check(_=None):
    global LAST_GPS_CHECK_TIME, GPS_CHECK_IN_PROGRESS, LATEST_COORDINATES

    with GPS_STATE_LOCK:
        if GPS_CHECK_IN_PROGRESS:
            return
        GPS_CHECK_IN_PROGRESS = True

    try:
        if GPS is None:
            return
        lat, lon = get_current_coordinates(GPS)
        LATEST_COORDINATES = {'lat': lat, 'lon': lon}
        logging.info(f"(control_logic.py): Robot at coordinates: {lat}, {lon}\n")
    except Exception as e:
        logging.warning(f"(control_logic.py): GPS check failed: {e}\n")
    finally:
        with GPS_STATE_LOCK:
            LAST_GPS_CHECK_TIME = time.time()
            GPS_CHECK_IN_PROGRESS = False


########## MISCELLANEOUS CONTROL FUNCTIONS ##########

def restart_process():  # start background thread to restart robot_dog.service every 30 minutes by checking elapsed time
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed >= 1800:  # 30 minutes = 1800 seconds
            os.system('sudo systemctl restart robot_dog.service')
            start_time = time.time()  # reset timer after restart
        time.sleep(1)  # check every second


########## RUN ROBOTIC PROCESS ##########

restart_thread = threading.Thread(target=restart_process, daemon=True)
restart_thread.start()
# voltage_thread = threading.Thread(target=voltage_monitor, daemon=True)
# voltage_thread.start()
_physical_loop()  # run robot process
